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
    if is_user(name, password):
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
    if not is_user(name, password):
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
        books.append({
            'id' : book['id'],
            'isbn' : book['isbn'],
            'title' : book['title'],
            'author' : book['author'],
            'year' : book['year'],
            'ratings_count' : result.json()['books'][0]['work_ratings_count'],
            'average_rating' : result.json()['books'][0]['average_rating']
        })
    return render_template("search.html", logged_in=user_logged_in, 
    name=user_name ,books=books)

@app.route("/search/<int:book_id>")
def open_book(book_id: int):
    user_index = -1
    resultSet = db.execute("SELECT * FROM books WHERE id=:id",
    { "id" : book_id })
    book = resultSet.fetchone()
    if not book:
        global error_content
        error_content = "Somehow you find unknown book"
        return redirect(url_for('error'))
    result = requests.get("https://www.goodreads.com/book/review_counts.json",
     params={"key" : key, "isbns" : book['isbn']})
    book = {
        "id" : book['id'],
        "isbn" : book['isbn'],
        "title" : book['title'],
        "author" : book['author'],
        "year" : book['year'],
        "ratings_count" : result.json()['books'][0]['work_ratings_count'],
        "average_rating" : result.json()['books'][0]['average_rating']
    }
    resultSet = db.execute("SELECT comment, rating FROM comments")
    comments = resultSet.fetchall()
    if user_logged_in:
        resultSet = db.execute("SELECT id FROM users WHERE name=:name",
        {"name" : user_name})
        user_index = resultSet.fetchone()['id']
    user_available_to_comment = is_user_available_to_comment(book['id'], user_index)
    return render_template("book.html", book=book, comments=comments,
     available_to_comment=user_available_to_comment, logged_in=user_logged_in,
     name=user_name)

@app.route("/search/<int:book_id>", methods=['POST'])
def comment(book_id):
    comment = request.form['comment']
    rating = request.form['rating']
    resultSet = db.execute("SELECT id from users WHERE name=:name",
    {"name" : user_name})
    user_index = resultSet.fetchone()['id']
    db.execute("INSERT INTO comments(comment, rating, book_id, user_id) "
    "VALUES (:comment, :rating, :book_id, :user_id)",
    {"comment" : comment, "rating" : rating, "book_id" : book_id, "user_id" : user_index})
    db.commit()
    return render_template("success.html", logged_in=user_logged_in, name=user_name)

@app.route("/error")
def error():
    return render_template('error.html', content=error_content, 
    logged_in=user_logged_in, name=user_name)

@app.route("/logout")
def logout():
    global user_logged_in
    user_logged_in = False
    return redirect(url_for('.index'))

def is_user(name: str, password: str) -> bool:
    resultSet = db.execute("SELECT * FROM users " 
    "WHERE name=:name AND password=:password",
    {"name": name, "password": password})
    if not resultSet.fetchone():
        return False
    return True

def is_user_available_to_comment(book_id, user_id) -> bool:
    if user_id is -1:
        return False
    resultSet = db.execute("SELECT comment FROM comments " 
    "WHERE user_id=:user_id AND book_id=:book_id",
    {"user_id" : user_id, "book_id" : book_id})
    if resultSet.fetchone():
        return False
    return True
