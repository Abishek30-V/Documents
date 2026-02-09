from app import app

with app.test_client() as c:
    for path, expect in [('/', 'Admin Login'), ('/login', 'Admin Login'), ('/login/user', 'User Login'), ('/user-login', 'User Login')]:
        r = c.get(path)
        print(path, 'status', r.status_code, 'contains', expect, expect in r.get_data(as_text=True))
