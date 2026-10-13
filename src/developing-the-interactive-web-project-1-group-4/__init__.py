from sqlalchemy import inspect
from . import models
from flask import Flask, render_template, request,jsonify, current_app
from .database import db
from .services import create_dummy_user, create_dummy_video, get_thumbnails_url, upload_video_to_cloud, upload_thumbnail_to_cloud, get_upload_form_data, create_video_helper, create_draft_helper
from botocore.exceptions import BotoCoreError, ClientError
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
from .routes import homePage_bp
load_dotenv()

app = Flask(__name__)
app.register_blueprint(homePage_bp)
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
    genres = db.session.execute(
        db.select(models.Genres).order_by(models.Genres.name)
    ).scalars().all()

    genre_options = [(genre.name, genre.name) for genre in genres]
    return render_template("upload.html", genre_options=genre_options)


@app.route("/save-draft", methods=["POST"])
def save_draft():
    def optional_text(name):
        return request.form.get(name, "").strip() or None

    video_key = optional_text("video_key")

    if not video_key:
        return jsonify(error="A video is required to save a draft."), 400

    thumbnail_key = optional_text("thumbnail_key")
    title = optional_text("title")
    description = optional_text("description")
    language = optional_text("language")
    video_type = optional_text("video_type")

    # Missing genres becomes an empty list.
    genres = [
        genre.strip()
        for genre in request.form.getlist("genre")
        if genre.strip()
    ]
    create_draft_helper(
        ti_user=1,
        thumbnail_key=thumbnail_key,
        duration=150,
        title=title,
        description=description,
        genres=genres,
        video_key=video_key,
        language=language,
        original=request.form.get("original", "false").lower() == "true"
    )

    # Temporary response to check the collected data.

    return jsonify(
        video_key=video_key,
        thumbnail_key=thumbnail_key,
        title=title,
        description=description,
        language=language,
        video_type=video_type,
        genres=genres,
    ), 200
@app.route("/publish", methods=["POST"])
def publish():
    data = get_upload_form_data()

    required = (
        "video_key", "thumbnail_key", "title",
        "description", "genres", "video_type", "language",
    )
    missing = [field for field in required if not data[field]]

    if missing:
        return jsonify(
            error="Please fill in all required fields.",
            fields=missing,
        ), 400

    if data["video_type"] not in ("original", "cover"):
        return jsonify(error="Invalid video type."), 400
    create_video_helper(
        ti_user=1,
        thumbnail_key=data["thumbnail_key"],
        duration= 150,
        title=data["title"],
        description=data["description"],
        genres=data["genres"],
        video_key=data["video_key"],
        language=data["language"],
        original=request.form.get("original", "false").lower() == "true"
    )

    # Save the published video here.
    return "Succesfully created video"

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

