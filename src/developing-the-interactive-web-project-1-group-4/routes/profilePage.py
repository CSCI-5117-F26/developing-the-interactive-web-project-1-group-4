from . import profilePage_bp
from ..database import db
from .. import models
from ..models import *
from flask import render_template, request, jsonify, current_app, session, redirect, url_for
from ..services import *
from botocore.exceptions import BotoCoreError, ClientError

@profilePage_bp.route("/profile-videos", methods=["GET"])
def profile_videos():
    if session.get("user") is None:
        return redirect(url_for("login"))
    user = get_current_user()

    if user is None:
        return redirect(url_for("profileInput.createProfile"))
    return jsonify(videos=[
    {
        "id": video.id,
        "title": video.title,
        "description": video.description,
        "duration": video.duration,
        "language": video.language,
        "original": video.Original,
        "views": video.views,
        "video_key": video.video_key,
        "thumbnail_key": video.thumbnail_key,
        "genres": [genre.name for genre in video.genres],
        "created_at": (
            video.created_at.isoformat() if video.created_at else None
        ),
        "updated_at": (
            video.updated_at.isoformat() if video.updated_at else None
        ),
    }
    for video in user.videos
    ]), 200

@profilePage_bp.route("/profile-info", methods=["GET"])
def profile_info():
    if session.get("user") is None:
        return redirect(url_for("login"))
    user = get_current_user()

    if user is None:
        return redirect(url_for("profileInput.createProfile"))

    return jsonify(
        id=user.ti_user_id,
        username=user.username,
        bio=user.bio,
        subscribers_count=get_subscribers_count(user.ti_user_id),
        subscriptions_count=get_subscriptions_count(user.ti_user_id),
        contact_me=user.contact_me,
        profile_picture_url=(
            mediaURL(user.profile_picture_key)
            if user.profile_picture_key else None
        )
    ), 200
