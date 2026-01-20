from flask import Flask, render_template, request, send_file, abort
import qrcode, os, sqlite3, zipfile, io, datetime

app = Flask(__name__)
DB = "qr.db"
from dotenv import load_dotenv
load_dotenv()

ADMIN_KEY = os.getenv("ADMIN_KEY", "changeme")

os.makedirs("generated_qr/single", exist_ok=True)
os.makedirs("generated_qr/bulk", exist_ok=True)

def admin_guard():
    if request.args.get("key") != ADMIN_KEY:
        abort(403)

def log_data(content):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    expires = datetime.datetime.now() + datetime.timedelta(days=30)
    cur.execute(
        "INSERT INTO qr_logs(content, expires_at) VALUES (?, ?)",
        (content, expires)
    )
    con.commit()
    con.close()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.form.get("data", "").strip()
        if not data:
            return "Invalid input", 400

        img = qrcode.make(data)

        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        log_data(data)

        return send_file(
            img_bytes,
            mimetype="image/png",
            as_attachment=True,
            download_name="qr.png"
        )

    return render_template("index.html",title="Single QR Generator")

@app.route("/bulk", methods=["GET", "POST"])
def bulk():
    if request.method == "POST":
        links = [l.strip() for l in request.form.get("links", "").splitlines() if l.strip()]
        if not links:
            return "No valid input", 400

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
            for i, link in enumerate(links, start=1):
                img = qrcode.make(link)

                img_bytes = io.BytesIO()
                img.save(img_bytes, format="PNG")
                img_bytes.seek(0)

                z.writestr(f"qr_{i}.png", img_bytes.read())
                log_data(link)

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name="bulk_qr.zip",
            mimetype="application/zip"
        )

    return render_template("bulk.html",title="Bulk QR Generator")


# ---------- ADMIN PANEL ----------

@app.route("/admin")
def admin():
    admin_guard()
    return render_template("admin.html")

@app.route("/admin/logs")
def admin_logs():
    admin_guard()
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("SELECT * FROM qr_logs ORDER BY id DESC")
    rows = cur.fetchall()
    con.close()
    return render_template("admin_logs.html", rows=rows)

@app.route("/admin/cleanup/db")
def cleanup_db():
    admin_guard()
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("DELETE FROM qr_logs WHERE expires_at < CURRENT_TIMESTAMP")
    con.commit()
    con.close()
    return "✅ Expired DB records removed"

@app.route("/admin/files")
def admin_files():
    admin_guard()
    data = {}
    for folder in ["single", "bulk"]:
        path = f"generated_qr/{folder}"
        data[folder] = os.listdir(path)
    return render_template("admin_files.html", data=data)

@app.route("/admin/cleanup/files")
def cleanup_files():
    admin_guard()
    cutoff = datetime.datetime.now() - datetime.timedelta(days=30)
    for root, _, files in os.walk("generated_qr"):
        for f in files:
            path = os.path.join(root, f)
            if datetime.datetime.fromtimestamp(os.path.getmtime(path)) < cutoff:
                os.remove(path)
    return "✅ Old QR images deleted"

if __name__ == "__main__":
    app.run(debug=True)
