from sqlalchemy import inspect
from . import models
from flask import Flask, render_template, request,jsonify, current_app
from .database import db
from .services import create_dummy_user, create_dummy_video, get_thumbnails_url, upload_video_to_cloud, upload_thumbnail_to_cloud
from botocore.exceptions import BotoCoreError, ClientError
from werkzeug.utils import secure_filename
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
    return render_template("base.html")


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



@app.route("/api/thumbnails", methods=["GET"])
def get_thumbnails():
    thumbnails = get_thumbnails_url()
    return jsonify(thumbnails)

@app.route("/new-video", methods=["GET", "POST"])
def new_video():
    return render_template("upload.html")

@app.route("/publish", methods=["POST"])
def publish():
    video_key = request.form.get("video_key")
    thumbnail_key = request.form.get("thumbnail_key")
    return render_template("Acknowledgement.html", name=video_key, thumbnail_name=thumbnail_key)

@app.route("/upload-video", methods=["POST"])
def upload_video():
    video = request.files.get("video_file")

    if video is None or not video.filename:
        return jsonify(error="No video selected."), 400

    try:
        video_key = upload_video_to_cloud(video)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except (BotoCoreError, ClientError):
        current_app.logger.exception("Video upload to R2 failed")
        return jsonify(error="Video upload failed. Please try again."), 502

    return jsonify(video_key=video_key)

@app.route("/upload-thumbnail", methods=["POST"])
def upload_thumbnail():
    thumbnail = request.files.get("thumbnail_file")

    if thumbnail is None or not thumbnail.filename:
        return jsonify(error="No Thumbnail selected."), 400

    try:
        thumbnail_key = upload_thumbnail_to_cloud(thumbnail)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except (BotoCoreError, ClientError):
        current_app.logger.exception("Thumbnail upload to R2 failed")
        return jsonify(error="Thumbnail upload failed. Please try again."), 502

    return jsonify(thumbnail_key=thumbnail_key)
if __name__ == "__main__":
    app.run(debug=True)
