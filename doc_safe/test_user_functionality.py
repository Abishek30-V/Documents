import sqlite3
import bcrypt
import os
from app import app

# Database path
DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')

def create_test_user():
    """Create a test user in the database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        username = 'test_user'
        email = 'test_user@example.com'
        password = 'TestPass@123'
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Delete if exists
        cur.execute('DELETE FROM users WHERE username=? OR email=?', (username, email))

        # Create user
        cur.execute('INSERT INTO users (username, email, password, role, is_approved) VALUES (?, ?, ?, ?, ?)',
                   (username, email, hashed, 'user', 1))
        conn.commit()
        print(f'Created test user: {username} with email: {email}')
        return username, email, password
    finally:
        cur.close()
        conn.close()

def test_user_registration():
    """Test user registration functionality"""
    print("\n=== Testing User Registration ===")
    with app.test_client() as c:
        # Test registration
        rv = c.post('/register', data={
            'username': 'new_reg_user',
            'email': 'new_reg_user@example.com',
            'password': 'RegPass@123'
        }, follow_redirects=True)
        print(f"Registration status: {rv.status_code}")
        if rv.status_code == 200:
            print("✓ Registration successful")
        else:
            print("✗ Registration failed")

def test_user_login():
    """Test user login functionality"""
    print("\n=== Testing User Login ===")
    username, email, password = create_test_user()

    with app.test_client() as c:
        # Test login
        rv = c.post('/login/user', data={'email': email, 'password': password}, follow_redirects=True)
        print(f"User login status: {rv.status_code}")
        if rv.status_code == 200 and 'dashboard' in rv.request.url:
            print("✓ User login successful")
        else:
            print("✗ User login failed")

def test_admin_login():
    """Test admin login functionality"""
    print("\n=== Testing Admin Login ===")
    with app.test_client() as c:
        rv = c.post('/login', data={
            'email': 'abishekvaiyapuri@gmail.com',
            'password': 'Abishek@2007'
        }, follow_redirects=True)
        print(f"Admin login status: {rv.status_code}")
        if rv.status_code == 200 and 'admin' in rv.request.url:
            print("✓ Admin login successful")
        else:
            print("✗ Admin login failed")

def test_admin_upload():
    """Test admin file upload"""
    print("\n=== Testing Admin File Upload ===")
    import io

    with app.test_client() as c:
        # Login as admin
        c.post('/login', data={
            'email': 'abishekvaiyapuri@gmail.com',
            'password': 'Abishek@2007'
        }, follow_redirects=True)

        # Upload file
        data = {'file': (io.BytesIO(b'test file content'), 'test_upload.pdf')}
        rv = c.post('/dashboard', data=data, content_type='multipart/form-data', follow_redirects=True)
        print(f"Admin upload status: {rv.status_code}")
        if rv.status_code == 200:
            print("✓ Admin upload successful")
        else:
            print("✗ Admin upload failed")

def test_user_permissions():
    """Test user permissions (should not be able to upload)"""
    print("\n=== Testing User Permissions ===")
    import io

    username, email, password = create_test_user()

    with app.test_client() as c:
        # Login as user
        c.post('/login/user', data={'email': email, 'password': password}, follow_redirects=True)

        # Try to upload (should fail)
        data = {'file': (io.BytesIO(b'user file content'), 'user_upload.pdf')}
        rv = c.post('/dashboard', data=data, content_type='multipart/form-data', follow_redirects=True)
        text = rv.get_data(as_text=True)
        if 'Only administrators can upload documents' in text:
            print("✓ User upload correctly blocked")
        else:
            print("✗ User upload not blocked (security issue!)")

def test_admin_panel_access():
    """Test admin panel access"""
    print("\n=== Testing Admin Panel Access ===")
    with app.test_client() as c:
        # Login as admin
        c.post('/login', data={
            'email': 'abishekvaiyapuri@gmail.com',
            'password': 'Abishek@2007'
        }, follow_redirects=True)

        # Access admin panel
        rv = c.get('/admin')
        print(f"Admin panel access status: {rv.status_code}")
        if rv.status_code == 200:
            print("✓ Admin panel access successful")
        else:
            print("✗ Admin panel access failed")

if __name__ == '__main__':
    print("Starting comprehensive functionality test...")

    test_user_registration()
    test_user_login()
    test_admin_login()
    test_admin_upload()
    test_user_permissions()
    test_admin_panel_access()

    print("\n=== Test Summary ===")
    print("All core functionalities tested. Check above for any failures.")
