import sqlite3

con = sqlite3.connect("qr.db")
cur = con.cursor()

cur.execute("""
DELETE FROM qr_logs
WHERE created_at < datetime('now', '-30 days')
""")

con.commit()
con.close()
