import requests

BASE = 'http://127.0.0.1:5000'

def check(path, expect):
    try:
        r = requests.get(BASE + path, timeout=5)
        print(path, 'status:', r.status_code)
        found = expect in r.text
        print('Contains expected text ("%s"):' % expect, found)
    except Exception as e:
        print(path, 'error:', e)

if __name__ == '__main__':
    check('/login', 'Admin Login')
    check('/login/user', 'User Login')
    check('/', 'Admin Login')
