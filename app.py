from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (
    UserMixin,
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'khoa-bao-mat-safeplate'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///safeplate.db'  # Tạo file DB tên safeplate.db

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# User Information Table in the Database
class User(UserMixin, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  email = db.Column(db.String(150), unique=True, nullable=False)
  password = db.Column(db.String(150), nullable=False)


@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))


# 1. main.html
@app.route('/')
def home():
  return render_template('main.html')


# 2. Processing Register
@app.route('/register', methods=['GET', 'POST'])
def register():
  if request.method == 'POST':
    email = request.form.get('email')
    password = request.form.get('password')

    # Check if email already exists
    user_exists = User.query.filter_by(email=email).first()
    if user_exists:
      return 'Email this has already been used!'

    # Encrypt the password and save it to the database.
    hashed_password = generate_password_hash(password, method='scrypt')
    new_user = User(email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('login'))

  return render_template('register.html')


# 3. Processing Login
@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()
    # Check users and password
    if user and check_password_hash(user.password, password):
      login_user(user)
      return redirect(url_for('home'))
    else:
      return 'Invalid email or password!'

  return render_template('login.html')
# 4. Forgot Password
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        return f"Sent password reset instructions to email: {email}"
    return render_template('forgot_password.html')

# 5. Log out
@app.route('/logout')
@login_required
def logout():
  logout_user()
  return redirect(url_for('home'))


if __name__ == '__main__':
  with app.app_context():
    db.create_all()  # Automatically create the database file when the application launches
  app.run(debug=True)

