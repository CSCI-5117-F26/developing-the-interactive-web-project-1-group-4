from . import profilePage_bp
from ..database import db
from .. import models
from ..models import *
from flask import render_template, request, jsonify, current_app, session, redirect, url_for, abort
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
        bio=user.Bio,
        subscribers_count=get_subscribers_count(user.ti_user_id),
        subscriptions_count=get_subscriptions_count(user.ti_user_id),
        contact_me=user.contact_me,
        profile_picture_url=(
            mediaURL(user.Profile_picture_key)
            if user.Profile_picture_key else None
        )
    ), 200


# ======================= Profile page (HTML) =======================

def format_count(n):
    # 856 -> '856', 1200 -> '1.2K', 2400000 -> '2.4M'
    n = n or 0
    if n < 1000:
        return str(n)
    if n < 1_000_000:
        return f"{n / 1000:.1f}".rstrip("0").rstrip(".") + "K"
    return f"{n / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"


def profile_video_card(video, default_url):
    return {
        "id": video.id,
        "title": video.title,
        "duration_text": formatDuration(video.duration),
        "views": video.views,
        "views_text": format_count(video.views),
        "thumbnail_url": (
            mediaURL(video.thumbnail_key)
            if video.thumbnail_key else default_url
        ),
        "watch_url": url_for("mediaPlayer.watchVideo", videoId=video.id),
    }


# /profile            -> the logged-in user's own profile
# /profile/<username> -> another user's profile (anyone can view it)
@profilePage_bp.route("/profile", defaults={"username": None}, methods=["GET"])
@profilePage_bp.route("/profile/<username>", methods=["GET"])
def profile_page(username):
    current = get_current_user()   # None when logged out or no profile yet

    if username is None:
        if session.get("user") is None:
            return redirect(url_for("login"))
        if current is None:
            return redirect(url_for("profileInput.createProfile"))
        profile_user = current
    else:
        profile_user = db.session.execute(
            db.select(models.Ti_user).filter_by(username=username)
        ).scalar_one_or_none()
        if profile_user is None:
            abort(404)

    is_own = (
        current is not None
        and current.ti_user_id == profile_user.ti_user_id
    )

    default_url = defaultCoverURL()
    user_videos = db.session.execute(
        db.select(models.videos)
        .filter_by(ti_user=profile_user.ti_user_id)
        .order_by(models.videos.created_at.desc())
    ).scalars().all()

    is_subscribed = False
    if current is not None and not is_own:
        is_subscribed = Subscriptions.query.filter_by(
            subscriber_id=current.ti_user_id,
            channel_id=profile_user.ti_user_id,
        ).first() is not None

    profile = {
        "id": profile_user.ti_user_id,
        "username": profile_user.username,
        "initial": (profile_user.username or "?")[0].upper(),
        "bio": profile_user.Bio,
        "email": profile_user.email,
        "phone": profile_user.Phone_number,
        "contact_me": profile_user.contact_me,
        "picture_url": (
            mediaURL(profile_user.Profile_picture_key)
            if profile_user.Profile_picture_key else None
        ),
        "video_count": len(user_videos),
        "subscribers_count": get_subscribers_count(profile_user.ti_user_id),
        "subscriptions_count": get_subscriptions_count(profile_user.ti_user_id),
    }

    return render_template(
        "profilePage.html",
        profile=profile,
        videos=addStats([profile_video_card(v, default_url) for v in user_videos]),
        default_thumbnail_url=default_url,
        is_own=is_own,
        is_logged_in=current is not None,
        is_subscribed=is_subscribed,
    )