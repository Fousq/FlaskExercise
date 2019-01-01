import os

import requests
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

key = "9SONAGWBR4c8TJbP6M9g"

@app.route("/")
def index():
    return render_template('index.html', logged_in=user_logged_in, name=user_name)

@app.route("/signup")
def render_signup():
    return render_template('signup.html', logged_in=user_logged_in)

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
    return render_template('login.html', logged_in=user_logged_in)

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

@app.route("/search", methods=['POST'])
def search():
    bookInfo = '%' + request.form['bookInfo'] + '%'
    resultSet = db.execute("SELECT * FROM books" 
    " WHERE isbn LIKE :bookInfo OR title LIKE :bookInfo" 
    " OR author LIKE :bookInfo", {"bookInfo" : bookInfo}).fetchall()
    books = list()
    for book in resultSet:
        result = requests.get("https://www.goodreads.com/book/review_counts.json"
        , params={"key" : key, "isbns" : book['isbn']})
        print(result.json()['books'][0]['average_rating'])
        books.append({
            'id' : book['id'],
            'isbn' : book['isbn'],
            'title' : book['title'],
            'author' : book['author'],
            'year' : book['year'],
            'ratings_count' : result.json()['books'][0]['work_ratings_count'],
            'average_rating' : result.json()['books'][0]['average_rating']
        })
    return render_template("search.html", logged_in=user_logged_in, books=books)

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
