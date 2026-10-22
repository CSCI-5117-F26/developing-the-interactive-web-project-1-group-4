from . import manageVideos_bp
from ..database import db
from .. import models
from ..models import *
from flask import render_template, request, jsonify, current_app, session, redirect, url_for
from ..services import *
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy.exc import SQLAlchemyError
from ..storage import r2

@manageVideos_bp.route("/manage-videos", methods=["GET"])
def manage_videos():
    if session.get("user") is None:
        return redirect(url_for("login"))
    user = get_current_user()
    return jsonify(videos=[
    {
        "id": video.id,
        "title": video.title,
        "description": video.description,
        "duration": video.duration,
        "views": video.views,
        "thumbnail_url": (
            mediaURL(video.thumbnail_key)
            if video.thumbnail_key else None
        ),
    }
    for video in user.videos
])

@manageVideos_bp.route("/edit-video/<int:video_id>", methods=["PATCH"])
def edit_video(video_id):
    user = get_current_user()

    if user is None:
        return redirect(url_for("login"))

    # Find the video only if it belongs to the current user.
    video = db.session.execute(
        db.select(models.videos).filter_by(
            id=video_id,
            ti_user=user.ti_user_id
        )
    ).scalar_one_or_none()

    if video is None:
        return jsonify(error="Video not found"), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(error="A JSON object is required"), 400

    if "title" in data:
        title = data["title"]
        if not isinstance(title, str) or not title.strip():
            return jsonify(error="Title must be a non-empty string"), 400

    if "description" in data:
        description = data["description"]
        if not isinstance(description, str):
            return jsonify(error="Description must be a string"), 400

    if "title" in data:
        video.title = title.strip()

    if "description" in data:
        video.description = description.strip()

    old_thumbnail_key = video.thumbnail_key
    new_thumbnail_key = data.get("thumbnail_key")

    if new_thumbnail_key is not None:
        if not isinstance(new_thumbnail_key, str) or not new_thumbnail_key.strip():
            return jsonify(error="Invalid thumbnail key"), 400

        new_thumbnail_key = new_thumbnail_key.strip()

        # Verify this key belongs to an upload by the current user
        # before saving it.
        video.thumbnail_key = new_thumbnail_key

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("Video update failed")
            return jsonify(error="Could not update video"), 500

        # Delete the old thumbnail only after the database update succeeds.
        if (
            new_thumbnail_key
            and old_thumbnail_key
            and new_thumbnail_key != old_thumbnail_key
        ):
            try:
                r2.delete_object(
                    Bucket=os.environ["R2_BUCKET_NAME"],
                    Key=old_thumbnail_key
                )
            except (BotoCoreError, ClientError):
                current_app.logger.exception(
                    "Old thumbnail cleanup failed for video %s", video.id
                )
        return jsonify(message="Video updated", video_id=video.id)

@manageVideos_bp.route("/edit-video/<int:video_id>/delete", methods=["POST"])
def delete_video(video_id):
    user = get_current_user()

    if user is None:
        return jsonify(error="Please log in and create your profile"), 401

    video = db.session.execute(
        db.select(models.videos).filter_by(
            id=video_id,
            ti_user=user.ti_user_id
        )
    ).scalar_one_or_none()

    if video is None:
        return jsonify(error="Video not found"), 404

    # Save the keys before deleting the database record.
    keys = {key for key in (
        video.video_key,
        video.thumbnail_key
    ) if key}

    try:
        db.session.delete(video)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Video deletion failed")
        return jsonify(error="Could not delete video"), 500

    cleanup_failed = False

    for key in keys:
        try:
            r2.delete_object(
                Bucket=os.environ["R2_BUCKET_NAME"],
                Key=key
            )
        except (BotoCoreError, ClientError):
            cleanup_failed = True
            current_app.logger.exception(
                "R2 cleanup failed for deleted video %s, key %s",
                video_id, key
            )

    if cleanup_failed:
        return jsonify(
            message="Video record deleted, but some cloud files could not be removed",
            cleanup_required=True
        ), 200

    return jsonify(message="Video and thumbnail deleted successfully")

