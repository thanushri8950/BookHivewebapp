import sqlite3

conn = sqlite3.connect("library.db")
cursor = conn.cursor()

# -------------------------------
# Books Table
# -------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    author TEXT,
    category TEXT,
    available INTEGER
)
""")

# -------------------------------
# Users Table (Admin + Students)
# -------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

# -------------------------------
# Insert Default Admin (only once)
# -------------------------------
cursor.execute("""
INSERT OR IGNORE INTO users (id, username, password, role)
VALUES (1, 'admin', 'admin123', 'admin')
""")

# -------------------------------
# Insert Sample Student
# -------------------------------
cursor.execute("""
INSERT OR IGNORE INTO users (username, password, role)
VALUES ('student1', 'student123', 'student')
""")


conn.commit()
conn.close()

print("Database setup complete.")
