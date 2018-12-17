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

@app.route("/", methods='POST')
def index():
    """error = None
    bookInfo = request.form['bookInfo']
    if bookInfo is None:
        error = 'No information about book'
    
    if error is None:
        return redirect(url_for(''))"""
    return render_template('index.html')

@app.route("/signup", methods='POST')
def signup():
    """error = None
    username = request.form['name']
    password = request.form['password']

    if username:
        error = 'Name is required'
    if password:
        error = 'Password is required'
    if error is None:
        return redirect(url_for('index.html'))"""

    return render_template('signup.html')

@app.route("/login", methods='GET')
def login():
    """error = None
    username = request.form['name']
    password = request.form['password']

    if username:
        error = 'Name is required'
    if password:
        error = 'Password is required'
    if error is None:
        return redirect(url_for('index.html'))
    """
    return render_template('login.html')
