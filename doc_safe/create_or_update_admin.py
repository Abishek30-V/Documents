"""
Create or update an admin user in the doc_safe database using ADMIN_USERNAME/ADMIN_PASSWORD from .env
"""
import os
from dotenv import load_dotenv
import pymysql
import bcrypt

# load .env from script dir
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

DB_HOST = os.getenv('DB_HOST') or 'localhost'
DB_PORT = int(os.getenv('DB_PORT') or 3306)
DB_USER = os.getenv('DB_USER') or 'root'
DB_PASSWORD = os.getenv('DB_PASSWORD') or ''
DB_NAME = os.getenv('DB_NAME') or 'doc_safe'

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    print('ADMIN_USERNAME or ADMIN_PASSWORD not set in .env; aborting.')
    raise SystemExit(1)

def try_connect(password_try):
    return pymysql.connect(host=DB_HOST, user=DB_USER, password=password_try, database=DB_NAME, port=DB_PORT, cursorclass=pymysql.cursors.DictCursor, autocommit=True)

# Try primary password from .env, else retry with common fallback
try:
    conn = try_connect(DB_PASSWORD)
except Exception as e:
    fallback = 'Abishek@007'
    if DB_PASSWORD != fallback:
        try:
            conn = try_connect(fallback)
            print('Connected using fallback DB password')
        except Exception as e2:
            print('Failed to connect to DB with provided credentials and fallback:', e2)
            raise
    else:
        print('Failed to connect to DB with provided credentials:', e)
        raise
try:
    with conn.cursor() as cur:
        email = f"{ADMIN_USERNAME}@localhost"
        # check if user exists
        cur.execute('SELECT id FROM users WHERE username = %s OR email = %s', (ADMIN_USERNAME, email))
        row = cur.fetchone()
        hashed = bcrypt.hashpw(ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        if row:
            user_id = row['id']
            cur.execute('UPDATE users SET password = %s, role=%s, is_approved=1 WHERE id = %s', (hashed, 'admin', user_id))
            print(f'Updated existing user id={user_id} as admin (approved).')
        else:
            cur.execute('INSERT INTO users (username, email, password, role, is_approved) VALUES (%s,%s,%s,%s,%s)', (ADMIN_USERNAME, email, hashed, 'admin', 1))
            print(f'Created admin user {ADMIN_USERNAME} with email {email}.')
finally:
    conn.close()
