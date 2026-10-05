import sqlite3
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    login_required,
    login_user,
    logout_user,
    current_user
)

from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "secure-master-key-safeplate"

DB_NAME = 'safeplate.db'

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Function to get a connection to the SQLite3 database
def get_db_connection():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    # Help convert query results to dictionary-like objects
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
  """Create the table if it does not exist in the file safeplate.db."""
  conn = get_db_connection()
  conn.execute(
      """
      CREATE TABLE IF NOT EXISTS user (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          email TEXT UNIQUE NOT NULL,
          password TEXT NOT NULL
      )
      """
  )
  conn.commit()
  conn.close()


# User Information Table in the Database
class User(UserMixin):
    def __init__(self, id, email, password):
        self.id = id
        self.email = email
        self.password = password

@login_manager.user_loader
def load_user(user_id):
  """Download a user by ID from the database using SQLite connection."""
  conn = get_db_connection()
  user = conn.execute("SELECT * FROM user WHERE id = ?", (int (user_id),)).fetchone()
  conn.close()

  if user:
      return User(id=user["id"], 
                  email=user["email"], 
                  password=user["password"])
  return None

# Main route for the home page

# 1. main.html
@app.route("/")
def home():
  return render_template('main.html')


# 2. Processing Register
@app.route("/register", methods=["GET", "POST"])
def register():
  if request.method == "POST":
    email = request.form.get("email")
    password = request.form.get("password")

    conn = get_db_connection()

    # Check if email already exists
    user_exists = conn.execute(
       "SELECT * FROM user WHERE email = ?", (email,)
       ).fetchone()
    if user_exists:
      conn.close()
      return "Email this has already been used!"

    # Encrypt the password and save it to the database.
    hashed_password = generate_password_hash(password, method="scrypt")
    conn.execute(
       "INSERT INTO user (email, password) VALUES (?, ?)", 
                 (email, hashed_password))
    conn.commit()
    conn.close()

    return redirect(url_for("login"))

  return render_template('register.html')


# 3. Processing Login
@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == "POST":
    email = request.form.get("email")
    password = request.form.get("password")

    conn = get_db_connection()
    user = conn.execute(
       "SELECT * FROM user WHERE email = ?", (email,)
       ).fetchone()
    conn.close()

    # Check users and password
    if user and check_password_hash(user["password"], password):
      user_obj = User(
         id=user["id"], 
         email=user["email"], 
         password=user["password"]
         )
      login_user(user_obj)
      return redirect(url_for("home"))
    else:
      return "Invalid email or password!"

  return render_template('login.html')

# 4. Forgot Password
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        return f"Sent password reset instructions to email: {email}"
    return render_template('forgot_password.html')

# 5. Log out
@app.route("/logout")
@login_required
def logout():
  logout_user()
  return redirect(url_for("home"))


if __name__ == "__main__":
    init_db()  # Automatically run the database initialization when the application launches
    app.run(debug=True)

