import time
import requests
import sqlite3
import os
import bcrypt
from dotenv import load_dotenv

BASE = 'http://127.0.0.1:5000'
ADMIN_EMAIL = 'abishekvaiyapuri@gmail.com'
ADMIN_PASS = 'Abishek@2007'

# Load DB path
DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')

# helper connect
def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 1) Admin login and upload
s_admin = requests.Session()
print('Logging in as admin...')
r = s_admin.post(f'{BASE}/login', data={'email': ADMIN_EMAIL, 'password': ADMIN_PASS}, allow_redirects=True)
print('Admin login status:', r.status_code, r.url)

# Upload a test file
files = {'file': ('admin_doc.txt', b'hello from admin', 'text/plain')}
print('Uploading file as admin...')
r = s_admin.post(f'{BASE}/dashboard', files=files, allow_redirects=True)
print('Upload response:', r.status_code)

# Find uploaded filename from admin dashboard HTML
r = s_admin.get(f'{BASE}/admin')
text = r.text
import re
matches = re.findall(r'/uploads/([A-Za-z0-9_\-\.]+)', text)
if not matches:
    print('Could not find uploaded file link in admin panel')
    raise SystemExit(1)
uploaded_filename = matches[0]
print('Found uploaded filename:', uploaded_filename)

# 2) Create an approved test user in DB
username = 'approved_user_test'
email = 'approved_user_test@example.com'
password = 'User@1234'
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
conn = get_db_conn()
cur = conn.cursor()
try:
    cur.execute('DELETE FROM users WHERE username=? OR email=?', (username, email))
    cur.execute('INSERT INTO users (username, email, password, role, is_approved) VALUES (?, ?, ?, ?, ?)', (username, email, hashed, 'user', 1))
    conn.commit()
    print('Created approved user:', username)
finally:
    cur.close()
    conn.close()

# 3) Login as approved user and attempt to upload (should be blocked)
s_user = requests.Session()
r = s_user.post(f'{BASE}/login/user', data={'email': email, 'password': password}, allow_redirects=True)
print('User login status:', r.status_code, r.url)
# Attempt upload
files = {'file': ('user_doc.txt', b'user content', 'text/plain')}
r = s_user.post(f'{BASE}/dashboard', files=files, allow_redirects=True)
print('User attempted upload status:', r.status_code)
if 'Only administrators can upload documents' in r.text:
    print('Upload correctly blocked for user')
else:
    print('Unexpected: user upload was not blocked')

# 4) User attempts to download admin-uploaded file
r = s_user.get(f'{BASE}/uploads/{uploaded_filename}')
print('User download status:', r.status_code)
if r.status_code == 200:
    print('Downloaded content:', r.content[:60])
else:
    print('Failed to download as user')

print('Full smoke test finished')
