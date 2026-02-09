import time
import requests

ADMIN_EMAIL = 'abishekvaiyapuri@gmail.com'
ADMIN_PASS = 'Abishek@2007'
BASE = 'http://127.0.0.1:5000'

s = requests.Session()

try:
    # give server a moment to start
    time.sleep(2)
    r = s.post(f'{BASE}/login', data={'email': ADMIN_EMAIL, 'password': ADMIN_PASS}, allow_redirects=True)
    print('LOGIN ->', r.status_code, r.url)

    r = s.get(f'{BASE}/dashboard')
    print('DASHBOARD contains pending panel:', 'Pending User Approvals' in r.text)

    r = s.post(f'{BASE}/admin/toggle_approval', allow_redirects=True)
    print('TOGGLE ->', r.status_code, r.url)

    r = s.get(f'{BASE}/dashboard')
    print('After toggle, dashboard has pending panel:', 'Pending User Approvals' in r.text)

    # toggle back
    r = s.post(f'{BASE}/admin/toggle_approval', allow_redirects=True)
    print('TOGGLE BACK ->', r.status_code, r.url)
    r = s.get(f'{BASE}/dashboard')
    print('After toggle back, pending panel:', 'Pending User Approvals' in r.text)

except Exception as e:
    print('TEST ERROR:', e)
