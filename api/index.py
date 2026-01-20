from flask import Flask, render_template, request, send_file, abort
import qrcode
import io
import os
import zipfile
import datetime
import redis

# ------------------ APP INIT ------------------
app = Flask(__name__)

# ------------------ ENV CONFIG ------------------
ADMIN_KEY = os.getenv("ADMIN_KEY")

REDIS_URL = os.getenv("UPSTASH_REDIS_REST_URL")
REDIS_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

if not ADMIN_KEY or not REDIS_URL or not REDIS_TOKEN:
    raise RuntimeError("Missing required environment variables")

# ------------------ REDIS CLIENT ------------------
r = redis.Redis.from_url(
    REDIS_URL,
    password=REDIS_TOKEN,
    decode_responses=True
)

# ------------------ HELPERS ------------------
def admin_guard():
    if request.args.get("key") != ADMIN_KEY:
        abort(403)

def log_data(content: str):
    """
    Store QR content in Redis with 30-day TTL
    """
    expires_at = int(
        (datetime.datetime.utcnow() + datetime.timedelta(days=30)).timestamp()
    )
    key = f"qr:{expires_at}:{abs(hash(content))}"
    r.set(key, content)
    r.expireat(key, expires_at)

# ------------------ ROUTES ------------------

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.form.get("data", "").strip()
        if not data:
            return "Invalid input", 400

        img = qrcode.make(data)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        log_data(data)

        return send_file(
            buf,
            mimetype="image/png",
            as_attachment=True,
            download_name="qr.png"
        )

    return render_template("index.html", title="Single QR")


@app.route("/bulk", methods=["GET", "POST"])
def bulk():
    if request.method == "POST":
        links = [
            l.strip() for l in request.form.get("links", "").splitlines()
            if l.strip()
        ]
        if not links:
            return "No valid input", 400

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as z:
            for i, link in enumerate(links, start=1):
                img = qrcode.make(link)
                img_buf = io.BytesIO()
                img.save(img_buf, format="PNG")
                img_buf.seek(0)
                z.writestr(f"qr_{i}.png", img_buf.read())
                log_data(link)

        zip_buf.seek(0)
        return send_file(
            zip_buf,
            mimetype="application/zip",
            as_attachment=True,
            download_name="bulk_qr.zip"
        )

    return render_template("bulk.html", title="Bulk QR")


# ------------------ ADMIN ------------------

@app.route("/admin")
def admin():
    admin_guard()
    keys = r.keys("qr:*")
    return render_template(
        "admin.html",
        total_logs=len(keys)
    )


@app.route("/admin/cleanup")
def admin_cleanup():
    admin_guard()
    keys = r.keys("qr:*")
    for k in keys:
        r.delete(k)
    return f"✅ Deleted {len(keys)} records"


# ------------------ ERROR HANDLERS ------------------

@app.errorhandler(403)
def forbidden(_):
    return "403 Forbidden", 403
