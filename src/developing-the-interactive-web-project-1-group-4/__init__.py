from sqlalchemy import inspect

from flask import Flask
from .database import db
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["Database_url"]

db.init_app(app)
with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)
    print("Tables in the database:", inspector.get_table_names())


@app.route('/')
def index():
    return '<p>Index Page</p>'

@app.route('/hello')
def hello():
    return '<p>Hello, World</p>'
