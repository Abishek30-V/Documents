import sqlite3, os

DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
try:
    # Create database
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            is_approved INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    ''')

    # Create initial admin with specified credentials
    cur.execute("SELECT COUNT(*) as cnt FROM users WHERE role='admin'")
    if cur.fetchone()['cnt'] == 0:
        admin_username = 'admin'
        admin_email = 'abishekvaiyapuri@gmail.com'
        admin_password = 'Abishek@2007'
        hashed = bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt())
        cur.execute(
            'INSERT INTO users (username, email, password, role, is_approved) VALUES (?, ?, ?, ?, ?)',
            (admin_username, admin_email, hashed.decode(), 'admin', 1)
        )
    conn.commit()
    print("Database initialized successfully")
finally:
    cur.close()
    conn.close()
