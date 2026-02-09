import pymysql

conn = pymysql.connect(host='localhost', user='root', password='Abishek@007', database='doc_safe', autocommit=True)
cur = conn.cursor()

# Drop existing tables
cur.execute('DROP TABLE IF EXISTS documents')
cur.execute('DROP TABLE IF EXISTS users')

# Create users table
cur.execute('''
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(150) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role ENUM("admin","user") DEFAULT "user",
    is_approved TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB
''')

# Create documents table
cur.execute('''
CREATE TABLE documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    filepath VARCHAR(500) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB
''')

print('✓ Tables created successfully')
conn.close()
