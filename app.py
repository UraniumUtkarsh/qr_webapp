from flask import Flask, render_template, request, send_file
import qrcode, os, sqlite3, zipfile, io, datetime

app = Flask(__name__)
DB = "qr.db"

# Ensure directories exist
os.makedirs("generated_qr/single", exist_ok=True)
os.makedirs("generated_qr/bulk", exist_ok=True)

def log_data(content):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("INSERT INTO qr_logs(content) VALUES (?)", (content,))
    con.commit()
    con.close()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.form.get("data", "").strip()
        if not data:
            return "Invalid input", 400

        img = qrcode.make(data)

        filename = f"qr_{int(datetime.datetime.now().timestamp())}.png"
        path = f"generated_qr/single/{filename}"
        img.save(path)

        log_data(data)
        return send_file(path, as_attachment=True)

    return render_template("index.html")

@app.route("/bulk", methods=["GET", "POST"])
def bulk():
    if request.method == "POST":
        raw_links = request.form.get("links", "")
        links = [l.strip() for l in raw_links.splitlines() if l.strip()]

        if not links:
            return "No valid links provided", 400

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

    return render_template("bulk.html")

if __name__ == "__main__":
    app.run(debug=True)
