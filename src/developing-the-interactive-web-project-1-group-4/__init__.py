from sqlalchemy import inspect
from . import models
from flask import Flask, request
from .database import db
from .services import create_dummy_user, create_dummy_video
from .storage import r2, bucket_name
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

@app.cli.command("reset-db")
def reset_db():  # Use `from . import models` if using package imports

    db.drop_all()
    db.create_all()

    print("Database tables recreated.")

@app.route('/')
def index():
    return '<p>Index Page</p>'

@app.route('/create-profile', methods=['POST'])
def create_profile():
    username = request.args.get('username')
    email = request.args.get('email')
    first_name = request.args.get('first_name')
    last_name = request.args.get('last_name')
    create_dummy_user(username, email, first_name, last_name)
    return "successfull"
@app.route('/create-video', methods=['POST'])
def create_video():
    ti_user = request.args.get('ti_user',type=int)
    thumbnail_key = request.args.get('thumbnail_key')
    duration = request.args.get('duration',type=int)
    title = request.args.get('title')
    video_key = request.args.get('video_key')
    language = request.args.get('language')
    original = request.args.get("original", "false").lower() == "true"
    create_dummy_video(ti_user, thumbnail_key, duration, title, video_key, language, original)
    return "successfull"

from flask import jsonify

@app.route("/api/thumbnails", methods=["GET"])
def get_thumbnails():
    thumbnail_keys = [
        "thumbnails/0067769d-f9fd-4a79-983e-ec8660fdaff4-2.jpg",
    ]

    thumbnails = []

    for key in thumbnail_keys:
        url = r2.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": os.environ["R2_BUCKET_NAME"],
                "Key": key,
            },
            ExpiresIn=3600
        )

        thumbnails.append({
            "key": key,
            "url": url,
        })

    return jsonify(thumbnails)

@app.route('/hello')
def hello():
    return '<p>Hello, World</p>'
