"""
Document Manager - Flask + MySQL secure application
Features: Authentication, Admin panel, Document upload/download
"""

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import sqlite3
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import bcrypt
from datetime import datetime
from functools import wraps

# Load environment variables from script directory
env_file = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_file)

# Database config
DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
print(f"DEBUG: Using SQLite database at {DB_PATH}")

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# Flask config
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'super-secret-key')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Login manager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


def get_db_connection():
    """Get SQLite connection with Row factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class User(UserMixin):
    """User model for Flask-Login."""
    def __init__(self, row):
        self.id = row['id']
        self.username = row['username']
        self.email = row['email']
        self.password = row['password']
        self.role = row['role']
        self.is_approved = bool(row['is_approved'])


@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM users WHERE id = ?', (int(user_id),))
        row = cur.fetchone()
        return User(row) if row else None
    finally:
        cur.close()
        conn.close()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated


def init_db():
    """Initialize database tables and admin user."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
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
    finally:
        cur.close()
        conn.close()


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not all([username, email, password]):
            flash('Please fill all fields', 'warning')
            return redirect(url_for('register'))

        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT id FROM users WHERE username=? OR email=?', (username, email))
            if cur.fetchone():
                flash('Username or email already exists', 'danger')
                return redirect(url_for('register'))

            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            cur.execute(
                'INSERT INTO users (username, email, password, role, is_approved) VALUES (?, ?, ?, ?, ?)',
                (username, email, hashed.decode(), 'user', 0)
            )
            conn.commit()
            flash('Registration successful. Wait for admin approval.', 'success')
            return redirect(url_for('user_login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('SELECT * FROM users WHERE email = ?', (email,))
            user_row = cur.fetchone()

            if not user_row or not user_row['is_approved']:
                msg = 'Waiting for admin approval' if user_row else 'Invalid credentials'
                flash(msg, 'warning')
                return redirect(url_for('login'))

            if bcrypt.checkpw(password.encode(), user_row['password'].encode()):
                login_user(User(user_row))
                # If admin, set an approval session flag and redirect to admin panel
                if user_row['role'] == 'admin':
                    session['admin_approval_mode'] = True
                    flash('Admin logged in. Approval mode enabled.', 'success')
                    return redirect(url_for('admin_panel'))
                else:
                    # Ensure any admin session flag is removed for regular users
                    session.pop('admin_approval_mode', None)
                    flash('Logged in successfully', 'success')
                    return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials', 'danger')
                return redirect(url_for('login'))
        finally:
            cur.close()
            conn.close()

    return render_template('login.html')



@app.route('/login/user', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('SELECT * FROM users WHERE email = ?', (email,))
            user_row = cur.fetchone()

            if not user_row or not user_row['is_approved']:
                msg = 'Waiting for admin approval' if user_row else 'Invalid credentials'
                flash(msg, 'warning')
                return redirect(url_for('user_login'))

            if bcrypt.checkpw(password.encode(), user_row['password'].encode()):
                login_user(User(user_row))
                # Ensure any admin approval flag is cleared for regular users
                session.pop('admin_approval_mode', None)
                flash('Logged in successfully', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials', 'danger')
                return redirect(url_for('user_login'))
        finally:
            cur.close()
            conn.close()

    return render_template('user_login.html')


# Alias route for user login to avoid any path issues
@app.route('/user-login', methods=['GET', 'POST'])
def user_login_alias():
    return user_login()


@app.route('/logout')
@login_required
def logout():
    logout_user()
    # Clear admin approval session on logout
    session.pop('admin_approval_mode', None)
    flash('Logged out', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if request.method == 'POST':
            # Only admin is allowed to upload documents
            if current_user.role != 'admin':
                flash('Only administrators can upload documents.', 'warning')
                return redirect(url_for('dashboard'))

            if 'file' not in request.files or not request.files['file'].filename:
                flash('No file selected', 'warning')
            else:
                file = request.files['file']
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                    disk_filename = f"{current_user.id}_{timestamp}_{filename}"
                    save_path = os.path.join(UPLOAD_FOLDER, disk_filename)
                    file.save(save_path)
                    
                    # Store filepath using forward slashes so URLs work cross-platform
                    rel_path = f"uploads/{disk_filename}"
                    cur.execute(
                        'INSERT INTO documents (user_id, filename, filepath) VALUES (?, ?, ?)',
                        (current_user.id, filename, rel_path)
                    )
                    conn.commit()
                    flash('File uploaded', 'success')
                else:
                    flash('Invalid file type', 'danger')
            return redirect(url_for('dashboard'))

        # Admins see all documents; regular users see their own + documents uploaded by admins
        if current_user.role == 'admin':
            cur.execute('''
                SELECT d.id, d.user_id, d.filename, d.filepath, d.uploaded_at, u.username
                FROM documents d JOIN users u ON d.user_id = u.id ORDER BY d.uploaded_at DESC
            ''')
            docs = cur.fetchall()
        else:
            cur.execute('''
                SELECT d.id, d.user_id, d.filename, d.filepath, d.uploaded_at, u.username
                FROM documents d JOIN users u ON d.user_id = u.id 
                WHERE d.user_id = ? OR u.role = 'admin'
                ORDER BY d.uploaded_at DESC
            ''', (current_user.id,))
            docs = cur.fetchall()

        # If admin is in approval mode, load pending users for approval UI
        pending_users = []
        if current_user.role == 'admin' and session.get('admin_approval_mode'):
            cur.execute('SELECT id, username, email, created_at FROM users WHERE is_approved = 0 ORDER BY created_at ASC')
            pending_users = cur.fetchall()

        return render_template('dashboard.html', docs=docs, pending_users=pending_users)
    finally:
        cur.close()
        conn.close()


@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    try:
        owner_id = int(filename.split('_')[0])
    except (ValueError, IndexError):
        abort(404)

    # Allow if requester is admin
    if current_user.role == 'admin':
        return send_from_directory(UPLOAD_FOLDER, filename)

    # Check owner role; if owner is admin, allow users to download admin-uploaded files
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT role FROM users WHERE id = ?', (owner_id,))
        row = cur.fetchone()
        owner_role = row['role'] if row else None
    finally:
        cur.close()
        conn.close()

    if owner_role == 'admin':
        return send_from_directory(UPLOAD_FOLDER, filename)

    # Otherwise only owner can download
    if current_user.id != owner_id:
        abort(403)

    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT id, username, email, role, is_approved, created_at FROM users ORDER BY created_at DESC')
        users = cur.fetchall()
        cur.execute('''
            SELECT d.id, d.user_id, d.filename, d.filepath, d.uploaded_at, u.username
            FROM documents d JOIN users u ON d.user_id = u.id ORDER BY d.uploaded_at DESC
        ''')
        docs = cur.fetchall()
        return render_template('admin.html', users=users, docs=docs)
    finally:
        cur.close()
        conn.close()



@app.route('/admin/toggle_approval', methods=['POST'])
@login_required
@admin_required
def toggle_admin_approval():
    # Flip the admin approval mode session flag
    current = session.get('admin_approval_mode', False)
    session['admin_approval_mode'] = not current
    if not current:
        flash('Admin approval mode enabled', 'success')
    else:
        flash('Admin approval mode disabled', 'info')
    return redirect(url_for('dashboard'))


@app.route('/admin/approve/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('UPDATE users SET is_approved = 1 WHERE id = ?', (user_id,))
        conn.commit()
        flash('User approved', 'success')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('admin_panel'))


@app.route('/admin/reject/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reject_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        flash('User deleted', 'info')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('admin_panel'))


@app.route('/admin/delete_doc/<int:doc_id>', methods=['POST'])
@login_required
@admin_required
def delete_doc(doc_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT filepath FROM documents WHERE id = ?', (doc_id,))
        row = cur.fetchone()
        if row:
            disk_path = os.path.join(BASE_DIR, row['filepath'])
            if os.path.exists(disk_path):
                try:
                    os.remove(disk_path)
                except OSError:
                    pass
            cur.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
            conn.commit()
            flash('Document deleted', 'info')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('admin_panel'))


@app.errorhandler(403)
def forbidden(e):
    return 'Forbidden: You do not have permission to access this resource.', 403


@app.errorhandler(404)
def not_found(e):
    return 'Not Found', 404


if __name__ == '__main__':
    init_db()
    # Disable the reloader to avoid process restarts during automated tests
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
