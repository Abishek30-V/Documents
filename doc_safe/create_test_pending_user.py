import sqlite3, os, bcrypt

DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
try:
    username = 'pending_user_test'
    email = 'pending_user_test@example.com'
    password = 'Pending@1234'
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cur.execute('DELETE FROM users WHERE username=? OR email=?', (username, email))
    cur.execute('INSERT INTO users (username, email, password, role, is_approved) VALUES (?, ?, ?, ?, ?)', (username, email, hashed, 'user', 0))
    conn.commit()
    print('Created pending user:', username)
finally:
    cur.close()
    conn.close()
