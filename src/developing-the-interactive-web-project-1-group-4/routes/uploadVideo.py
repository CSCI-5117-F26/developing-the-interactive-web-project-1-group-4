from . import uploadVideo_bp
from ..database import db
from .. import models
from ..models import *
from flask import render_template, request, jsonify, current_app, session, redirect, url_for
from ..services import *
from botocore.exceptions import BotoCoreError, ClientError


@uploadVideo_bp.route("/new-video", methods=["GET", "POST"])
def new_video():
    if session.get("user") is None:
        return redirect(url_for("login"))
    genres = db.session.execute(
        db.select(models.Genres).order_by(models.Genres.name)
    ).scalars().all()

    genre_options = [(genre.name, genre.name) for genre in genres]
    return render_template("upload.html", genre_options=genre_options)

@uploadVideo_bp.route("/save-draft", methods=["POST"])
def save_draft():
    if session.get("user") is None:
        return redirect(url_for("login"))
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
    user = get_current_user()
    user_id = user.ti_user_id
    create_draft_helper(
        ti_user=user_id,
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
@uploadVideo_bp.route("/publish", methods=["POST"])
def publish():
    if session.get("user") is None:
        return redirect(url_for("login"))
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
    user = get_current_user()
    user_id = user.ti_user_id
    create_video_helper(
        ti_user=user_id,
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

@uploadVideo_bp.route("/upload-video", methods=["POST"])
def upload_video():
    if session.get("user") is None:
        return redirect(url_for("login"))
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

@uploadVideo_bp.route("/upload-thumbnail", methods=["POST"])
def upload_thumbnail():
    if session.get("user") is None:
        return redirect(url_for("login"))
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