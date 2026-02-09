import re
import io
import bcrypt
import sqlite3
import os
from dotenv import load_dotenv
from app import app

# Load DB path for direct DB writes
DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')

def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

ADMIN_EMAIL = 'abishekvaiyapuri@gmail.com'
ADMIN_PASS = 'Abishek@2007'

# Create approved user in DB
username = 'local_user_test'
email = 'local_user_test@example.com'
password = 'UserLocal@1234'
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
conn = get_db_conn()
cur = conn.cursor()
try:
    cur.execute('DELETE FROM users WHERE username=? OR email=?', (username, email))
    cur.execute('INSERT INTO users (username, email, password, role, is_approved) VALUES (?, ?, ?, ?, ?)', (username, email, hashed, 'user', 1))
    cur.execute('SELECT id FROM users WHERE email=?', (email,))
    user_row = cur.fetchone()
    user_id = user_row['id']
    print('Created approved user id=', user_id)
    conn.commit()
finally:
    cur.close()
    conn.close()

with app.test_client() as c:
    # Admin login
    rv = c.post('/login', data={'email': ADMIN_EMAIL, 'password': ADMIN_PASS}, follow_redirects=True)
    print('Admin login status', rv.status_code)

    # Admin upload
    data = {
        'file': (io.BytesIO(b'admin-file-content'), 'admin_upload.pdf')
    }
    rv = c.post('/dashboard', data=data, content_type='multipart/form-data', follow_redirects=True)
    print('Admin upload status', rv.status_code)

    # Find uploaded filename by querying database directly
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute('SELECT filepath FROM documents ORDER BY uploaded_at DESC LIMIT 1')
        row = cur.fetchone()
        if not row:
            print('No documents found in database')
            raise SystemExit(1)
        filepath = row['filepath']
        uploaded_filename = filepath.split('/')[-1]  # Extract filename from path
        print('Uploaded filename (local):', uploaded_filename)
    finally:
        cur.close()
        conn.close()

    # User login
    rv = c.post('/login/user', data={'email': email, 'password': password}, follow_redirects=True)
    print('User login status', rv.status_code)

    # User attempt upload
    data = {'file': (io.BytesIO(b'user-upload'), 'user_upload.txt')}
    rv = c.post('/dashboard', data=data, content_type='multipart/form-data', follow_redirects=True)
    text = rv.get_data(as_text=True)
    if 'Only administrators can upload documents' in text:
        print('User upload blocked as expected')
    else:
        print('User upload NOT blocked (unexpected)')

    # User download admin file
    rv = c.get(f'/uploads/{uploaded_filename}')
    print('User download status', rv.status_code)
    if rv.status_code == 200:
        print('Downloaded bytes:', rv.data[:40])
    else:
        print('Download failed')
