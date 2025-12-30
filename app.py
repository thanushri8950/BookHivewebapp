from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "library_secret_key"

# -------------------------------
# Database Connection
# -------------------------------
def get_db_connection():
    conn = sqlite3.connect("library.db")
    conn.row_factory = sqlite3.Row
    return conn

# -------------------------------
# Role Selection Page
# -------------------------------
@app.route("/")
def role_select():
    return render_template("role_select.html")

# -------------------------------
# Login (Admin / Student)
# -------------------------------
@app.route("/login/<role>", methods=["GET", "POST"])
def login(role):
    if role not in ["admin", "student"]:
        return redirect("/")

    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=? AND role=?",
            (username, password, role)
        ).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["role"] = user["role"]

            if role == "admin":
                return redirect("/admin")
            else:
                return redirect("/student")
        else:
            error = "Invalid username or password"

    return render_template("login.html", role=role, error=error)

# -------------------------------
# Signup (Student Only)
# -------------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    message = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        existing = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        if existing:
            message = "Username already exists"
        else:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, 'student')",
                (username, password)
            )
            conn.commit()
            conn.close()
            return redirect("/login/student")

        conn.close()

    return render_template("signup.html", message=message)

# -------------------------------
# Admin Dashboard
# -------------------------------
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect("/")
    return render_template("admin.html")

# -------------------------------
# Student Home
# -------------------------------
@app.route("/student")
def student_home():
    if session.get("role") != "student":
        return redirect("/")
    return render_template("index.html")

# -------------------------------
# Add Book (Admin)
# -------------------------------
@app.route("/admin/add", methods=["GET", "POST"])
def add_book():
    if session.get("role") != "admin":
        return redirect("/")

    if request.method == "POST":
        book_id = int(request.form["book_id"])
        title = request.form["title"]
        author = request.form["author"]
        category = request.form["category"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO books (id, title, author, category, available) VALUES (?, ?, ?, ?, 1)",
            (book_id, title, author, category)
        )
        conn.commit()
        conn.close()
        return redirect("/admin")

    return render_template("add_book.html")

# -------------------------------
# Search Books
# -------------------------------
@app.route("/search")
def search():
    query = request.args.get("query", "")
    conn = get_db_connection()

    if query.isdigit():
        books = conn.execute(
            "SELECT * FROM books WHERE id=?",
            (int(query),)
        ).fetchall()
    else:
        books = conn.execute(
            """
            SELECT * FROM books
            WHERE title LIKE ? OR author LIKE ? OR category LIKE ?
            """,
            (f"%{query}%", f"%{query}%", f"%{query}%")
        ).fetchall()

    conn.close()
    return render_template("search.html", books=books)

# -------------------------------
# Issue Book
# -------------------------------
@app.route("/admin/issue", methods=["GET", "POST"])
def issue_book():
    if session.get("role") != "admin":
        return redirect("/")

    message = None

    if request.method == "POST":
        book_id = int(request.form["book_id"])

        conn = get_db_connection()
        book = conn.execute(
            "SELECT * FROM books WHERE id=? AND available=1",
            (book_id,)
        ).fetchone()

        if book:
            conn.execute(
                "UPDATE books SET available=0 WHERE id=?",
                (book_id,)
            )
            conn.commit()
            message = "Book issued successfully"
        else:
            message = "Book not available"

        conn.close()

    return render_template("issue_book.html", message=message)

# -------------------------------
# Return Book
# -------------------------------
@app.route("/admin/return", methods=["GET", "POST"])
def return_book():
    if session.get("role") != "admin":
        return redirect("/")

    message = None

    if request.method == "POST":
        book_id = int(request.form["book_id"])

        conn = get_db_connection()
        conn.execute(
            "UPDATE books SET available=1 WHERE id=?",
            (book_id,)
        )
        conn.commit()
        conn.close()
        message = "Book returned successfully"

    return render_template("return_book.html", message=message)

# -------------------------------
# Delete Book
# -------------------------------
@app.route("/admin/delete", methods=["GET", "POST"])
def delete_book():
    if session.get("role") != "admin":
        return redirect("/")

    message = None

    if request.method == "POST":
        book_id = int(request.form["book_id"])
        conn = get_db_connection()
        conn.execute("DELETE FROM books WHERE id=?", (book_id,))
        conn.commit()
        conn.close()
        message = "Book deleted successfully"

    return render_template("delete_book.html", message=message)

# -------------------------------
# Logout
# -------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -------------------------------
# Run App
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)
