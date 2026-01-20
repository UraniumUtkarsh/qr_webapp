import sqlite3

DB_NAME = "qr.db"

def create_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Fresh start
    cursor.execute("DROP TABLE IF EXISTS qr_logs")

    cursor.execute("""
    CREATE TABLE qr_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME NOT NULL
    );
    """)

    conn.commit()
    conn.close()
    print("✅ Fresh SQLite DB created (manual admin cleanup only).")

if __name__ == "__main__":
    create_db()
