from . import uploadVideo_bp
from ..database import db
from .. import models
from ..models import *
from flask import render_template, request, jsonify, current_app, session, redirect, url_for
from ..services import *
from botocore.exceptions import BotoCoreError, ClientError
import os
from dotenv import load_dotenv
load_dotenv()


@uploadVideo_bp.route("/new-video", methods=["GET", "POST"])
def new_video():
    if session.get("user") is None:
        return redirect(url_for("login"))
    user = get_current_user()
    if user is None:
        return redirect(url_for("profileInput.createProfile"))
    genres = db.session.execute(
        db.select(models.Genres).order_by(models.Genres.name)
    ).scalars().all()
    drafts = db.session.execute(
    db.select(models.Drafts).where(models.Drafts.ti_user== user.ti_user_id).order_by(models.Drafts.created_at.desc())
    ).scalars().all()
    draft_list = [
        {
            "id": draft.id,
            "title": draft.title or "",
            "description": draft.description or "",
            "duration": draft.duration,
            "thumbnail_url": (
                mediaURL(draft.thumbnail_key)
                if draft.thumbnail_key else None
            ),
            "language": draft.language or "",
            "video_type": (
                "original" if draft.Original is True
                else "cover" if draft.Original is False
                else ""
            ),
            # Use the Genres primary-key attribute used by genre_options.
            "genres": [str(genre.name) for genre in draft.genres],
        }
        for draft in drafts
    ]
    genre_options = [(genre.name, genre.name) for genre in genres]
    return render_template("upload.html", genre_options=genre_options,draft_list =draft_list)

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
    if not title:
        return jsonify(error="A title is required to save a draft."), 400

    if len(title) > 200:
        return jsonify(error="Title must be 200 characters or fewer."), 400
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
        original=(
            video_type == "original"
            if video_type in ("original", "cover")
            else None
        )
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
        duration= getVideoDuration(mediaURL(data["video_key"])),
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

@uploadVideo_bp.route("/update-draft", methods=["POST"])
def update_draft():
    if session.get("user") is None:
        return jsonify(error="Please log in."), 401

    user = get_current_user()
    if user is None:
        return jsonify(error="Please create your profile."), 403

    draft = get_owned_draft(user)
    if draft is None:
        return jsonify(error="Draft not found."), 404

    try:
        apply_draft_form(draft)
        db.session.commit()
    except ValueError as error:
        db.session.rollback()
        return jsonify(error=str(error)), 400
    except Exception:
        db.session.rollback()
        raise

    return jsonify(message="Draft updated."), 200

@uploadVideo_bp.route("/publish-draft", methods=["POST"])
def publish_draft():
    if session.get("user") is None:
        return jsonify(error="Please log in."), 401

    user = get_current_user()
    if user is None:
        return jsonify(error="Please create your profile."), 403

    draft = get_owned_draft(user)
    if draft is None:
        return jsonify(error="Draft not found."), 404

    try:
        apply_draft_form(draft)

        if (
            not draft.video_key
            or not draft.thumbnail_key
            or not draft.description
            or not draft.genres
            or not draft.language
            or draft.Original is None
        ):
            raise ValueError(
                "Publishing requires a video, thumbnail, title, "
                "description, genre, Original/Cover selection and language."
            )

        create_video_helper(
            ti_user=user.ti_user_id,
            thumbnail_key=draft.thumbnail_key,
            duration=getVideoDuration(mediaURL(draft.video_key)),
            title=draft.title,
            description=draft.description,
            genres=[str(genre.name) for genre in draft.genres],
            video_key=draft.video_key,
            language=draft.language,
            original=draft.Original,
        )

        db.session.delete(draft)
        db.session.commit()

    except ValueError as error:
        db.session.rollback()
        return jsonify(error=str(error)), 400
    except Exception:
        db.session.rollback()
        raise

    return jsonify(message="Video published."), 200