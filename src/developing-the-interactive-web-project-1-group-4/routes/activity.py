from datetime import datetime, timezone
from .. services import mediaURL, get_current_user
from flask import Blueprint, redirect, render_template, url_for
from sqlalchemy.orm import joinedload, selectinload
from . import activity_bp
from ..database import db
from ..models import Comments, Likes, videos
# Import your existing get_current_user and mediaURL helpers here.


def time_ago(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    seconds = max(
        0,
        int((datetime.now(timezone.utc) - value).total_seconds())
    )

    for label, size in (
        ("year", 365 * 24 * 3600),
        ("month", 30 * 24 * 3600),
        ("day", 24 * 3600),
        ("hour", 3600),
        ("minute", 60),
    ):
        amount = seconds // size
        if amount:
            return f"{amount} {label}{'s' if amount != 1 else ''}"

    return "a few seconds"


def activity_video(video):
    duration = int(video.duration or 0)
    hours, remainder = divmod(duration, 3600)
    minutes, seconds = divmod(remainder, 60)

    return {
        "id": video.id,
        "title": video.title,
        "author": video.uploader.username,
        "thumbnail_url": (
            mediaURL(video.thumbnail_key)
            if video.thumbnail_key else None
        ),
        "is_default": not bool(video.thumbnail_key),
        "duration_text": (
            f"{hours}:{minutes:02}:{seconds:02}"
            if hours else f"{minutes}:{seconds:02}"
        ),
        "views": video.views,
        "likes": len(video.likes),
        "comments_count": len(video.comments),
    }


@activity_bp.get("/activity")
def activity():
    user = get_current_user()

    if user is None:
        return redirect(url_for("login"))

    # Eager-load the data used by activity_video().
    video_options = (
        joinedload(videos.uploader),
        selectinload(videos.likes),
        selectinload(videos.comments),
    )

    liked_rows = db.session.execute(
        db.select(Likes)
        .where(Likes.ti_user == user.ti_user_id)
        .options(
            joinedload(Likes.video).options(*video_options)
        )
        .order_by(Likes.created_at.desc(), Likes.id.desc())
    ).scalars().all()

    liked_videos = []

    for like in liked_rows:
        card = activity_video(like.video)
        card["likedtime"] = time_ago(like.created_at)
        liked_videos.append(card)

    comment_rows = db.session.execute(
        db.select(Comments)
        .where(Comments.user_id == user.ti_user_id)
        .options(
            joinedload(Comments.video).options(*video_options)
        )
        .order_by(Comments.created_at.desc(), Comments.id.desc())
    ).scalars().all()

    # Group comments so each video has one card.
    commented_by_id = {}

    for comment in comment_rows:
        if comment.video_id not in commented_by_id:
            card = activity_video(comment.video)
            card["commentedtime"] = time_ago(comment.created_at)
            card["comments"] = []
            commented_by_id[comment.video_id] = card

        commented_by_id[comment.video_id]["comments"].append({
            "id": comment.id,
            "comment": comment.comment,
        })

    return render_template(
        "activity.html",
        liked_videos=liked_videos,
        commented_videos=list(commented_by_id.values()),
        default_thumbnail_url=None,
    )