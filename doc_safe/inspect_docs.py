import sqlite3, os

DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
try:
    cur.execute('SELECT id, user_id, filename, filepath, uploaded_at FROM documents ORDER BY uploaded_at DESC')
    rows = cur.fetchall()
    for r in rows:
        print(r)
finally:
    cur.close()
    conn.close()
