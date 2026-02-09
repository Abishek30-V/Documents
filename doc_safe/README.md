# Document Manager (Flask + MySQL)

Minimal secure document manager built with Flask, PyMySQL, Flask-Login and bcrypt.

Quick setup
- Create and activate a virtualenv inside `doc_safe`:

```powershell
python -m venv venv
venv\Scripts\activate
```

- Install dependencies:

```powershell
pip install -r requirements.txt
```

- Update `.env` with your MySQL credentials (already present, edit `DB_PASSWORD`, `SECRET_KEY`).

- Create the MySQL database (example):

```sql
CREATE DATABASE doc_safe CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL ON doc_safe.* TO 'root'@'localhost';
```

- Run the app (first run will create tables):

```powershell
# from doc_safe folder
python app.py
```

Notes
- Admin account: if `ADMIN_USERNAME` and `ADMIN_PASSWORD` are set in `.env` and no admin exists, an approved admin user will be created automatically on first run.
- Uploads are saved in the `uploads/` folder and paths stored in the `documents` table.
- Security:
  - Passwords hashed with `bcrypt`.
  - Parameterized queries used to prevent SQL injection.
  - Uploaded filenames sanitized via `secure_filename` and validated by extension.

Next actions I can take
- Run the app locally and smoke-test endpoints.
- Add unit tests or Dockerfile.
