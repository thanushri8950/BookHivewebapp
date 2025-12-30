from flask import session

from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)
app.secret_key = "library_secret_key"


# -------------------------------
# Database Connection Function
# -------------------------------
def get_db_connection():
    conn = sqlite3.connect("library.db")
    conn.row_factory = sqlite3.Row
    return conn

# -------------------------------
# Home Page (User Search Page)
# -------------------------------
@app.route("/")
def home():
    if "role" not in session:
        return render_template("role_select.html")

    if session["role"] == "admin":
        return redirect("/admin")

    return redirect("/student")



# -------------------------------
# Admin Dashboard
# -------------------------------
@app.route("/admin")
def admin():
    # Check if the user is logged in and is an admin
    if "role" not in session or session["role"] != "admin":
        return redirect("/login")
    
    # Render the admin dashboard
    return render_template("admin.html")



# -------------------------------
# Add Book (Admin)
# -------------------------------
@app.route("/admin/add", methods=["GET", "POST"])
def add_book():
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
# Search Books (User)
# -------------------------------
@app.route("/search")
def search():
    query = request.args.get("query", "").strip()
    conn = get_db_connection()

    # CASE 1: Numeric input → search by ID
    if query.isdigit():
        books = conn.execute(
            "SELECT * FROM books WHERE id = ?",
            (int(query),)
        ).fetchall()
    else:
        # CASE 2: Text input → search by title, author, category
        books = conn.execute(
            """
            SELECT * FROM books
            WHERE LOWER(title) LIKE LOWER(?)
               OR LOWER(author) LIKE LOWER(?)
               OR LOWER(category) LIKE LOWER(?)
            ORDER BY title
            """,
            (f"%{query}%", f"%{query}%", f"%{query}%")
        ).fetchall()

    conn.close()
    return render_template("search.html", books=books)

# -------------------------------
# Issue Book (Admin)
# -------------------------------
@app.route("/admin/issue", methods=["GET", "POST"])
def issue_book():
    message = None
    if request.method == "POST":
        book_id = request.form["book_id"]
        try:
            book_id = int(book_id)
        except ValueError:
            message = "Invalid Book ID."
            return render_template("issue_book.html", message=message)

        conn = get_db_connection()
        book = conn.execute(
            "SELECT * FROM books WHERE id = ?",
            (book_id,)
        ).fetchone()

        if book and book["available"] == 1:
            conn.execute(
                "UPDATE books SET available = 0 WHERE id = ?",
                (book_id,)
            )
            conn.commit()
            message = "Book issued successfully."
        else:
            message = "Book not found or already issued."

        conn.close()
    return render_template("issue_book.html", message=message)

# -------------------------------
# Return Book (Admin)
# -------------------------------
@app.route("/admin/return", methods=["GET", "POST"])
def return_book():
    message = None
    if request.method == "POST":
        book_id = request.form["book_id"]
        try:
            book_id = int(book_id)
        except ValueError:
            message = "Invalid Book ID."
            return render_template("return_book.html", message=message)

        conn = get_db_connection()
        book = conn.execute(
            "SELECT * FROM books WHERE id = ?",
            (book_id,)
        ).fetchone()

        if book and book["available"] == 0:
            conn.execute(
                "UPDATE books SET available = 1 WHERE id = ?",
                (book_id,)
            )
            conn.commit()
            message = "Book returned successfully."
        else:
            message = "Book not found or already available."

        conn.close()
    return render_template("return_book.html", message=message)

# -------------------------------
# Delete Book (Admin)
# -------------------------------
@app.route("/admin/delete", methods=["GET", "POST"])
def delete_book():
    message = None
    if request.method == "POST":
        book_id = request.form["book_id"]
        try:
            book_id = int(book_id)
        except ValueError:
            message = "Invalid Book ID."
            return render_template("delete_book.html", message=message)

        conn = get_db_connection()
        book = conn.execute(
            "SELECT * FROM books WHERE id = ?",
            (book_id,)
        ).fetchone()

        if book:
            conn.execute(
                "DELETE FROM books WHERE id = ?",
                (book_id,)
            )
            conn.commit()
            message = f"Book ID {book_id} deleted successfully."
        else:
            message = "Book not found."

        conn.close()
    return render_template("delete_book.html", message=message)


#-----------------------------------------
# login route 
#------------------------------------------
@app.route("/login/<role>", methods=["GET", "POST"])
def login(role):
    error = None

    if role not in ["admin", "student"]:
        return redirect("/")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ? AND role = ?",
            (username, password, role)
        ).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["role"] = user["role"]

            print("LOGIN SUCCESS:", user["username"], user["role"])  # debug

            if role == "admin":
                return redirect("/admin")
            else:
                return redirect("/student")
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error, role=role)


# ------------------------------------------
# Signup route
# ------------------------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    message = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()

        existing_user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if existing_user:
            message = "Username already exists."
            conn.close()
        else:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, 'student')",
                (username, password)
            )
            conn.commit()
            conn.close()

            session["role"] = "student"
            return redirect("/student")

    return render_template("signup.html", message=message)



#------------------------------------------
# Student route
#------------------------------------------
@app.route("/student")
def student_home():
    if session.get("role") != "student":
        return redirect("/")
    return render_template("index.html")


#--------------------------------
# Logout route
#--------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")



# -------------------------------
# Run App
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)