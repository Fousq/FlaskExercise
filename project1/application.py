import os

from flask import ( 
    Flask, session, render_template, url_for, request,
    redirect
)
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
app.static_folder = 'static'

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
resultSet = None

user_logged_in = False
user_name = None
error_content = None

@app.route("/")
def index():
    print(user_logged_in)
    return render_template('index.html', logged_in=user_logged_in, name=user_name)

@app.route("/signup")
def render_signup():
    return render_template('signup.html')

@app.route("/signup", methods=['POST'])
def signup():
    name = request.form['name']
    password = request.form['password']
    if not is_user(name, password):
        global error_content
        error_content= "Such user's already existed"
        return redirect(url_for('error'))
    db.execute("INSERT INTO users(name, password) "
    "VALUES (:name, :password)",
    {"name" : name, "password" : password})
    db.commit()
    global user_logged_in
    user_logged_in = True
    global user_name
    user_name = name
    return redirect(url_for('.index'))

@app.route("/login")
def render_login():
    return render_template('login.html')

@app.route("/login", methods=['POST'])
def login():
    name = request.form['name']
    password = request.form['password']
    if is_user(name, password):
        global error_content
        error_content= "Such user doesn't exist"
        return redirect(url_for('error'))
    global user_logged_in
    user_logged_in = True
    global user_name
    user_name = name
    return redirect(url_for('.index'))

@app.route("/search", methods=['GET'])
def search():
    return "SEARCH"

@app.route("/error")
def error():
    return render_template('error.html', content=error_content)

@app.route("/logout")
def logout():
    global user_logged_in
    user_logged_in = False
    return redirect(url_for('.index'))

def is_user(name: str, password: str) -> bool:
    resultSet = db.execute("SELECT * FROM users " 
    "WHERE name=:name AND password=:password",
    {"name": name, "password": password})
    if resultSet.fetchone():
        return False
    return True
