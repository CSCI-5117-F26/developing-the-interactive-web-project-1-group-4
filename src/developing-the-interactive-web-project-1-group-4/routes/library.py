from flask import render_template, request, jsonify, url_for, redirect, abort
from ..models import Playlists, videos
from . import library_bp
from ..services import (
    fetchVideos, fetchGenres, fetchArtistVideos, searchAll, text_wrap,
    SEARCH_PREVIEW_LIMIT, SEARCH_PAGE_LIMIT, get_current_user
)
from ..database import db
@library_bp.get("/library")
def library():
    user = get_current_user()

    if user is None:
        return redirect(url_for("login"))

    playlists = []
    saved_videos = []
    watchlater = []

    for playlist in user.playlists:
        if playlist.title == "Watch Later":
            watchlater.extend(playlist.videos)
        elif playlist.title == "Saved Videos":
            saved_videos.extend(playlist.videos)
        else:
            playlists.append(playlist)

    return render_template(
        "library.html",
        playlists=playlists,
        saved_videos=saved_videos,
        watchlater=watchlater,
    )

@library_bp.post("/add-to-watch-later")
def add_to_watch_later():
    user = get_current_user()

    if user is None:
        return jsonify(error="Please log in to save videos."), 401

    data = request.get_json(silent=True) or {}
    video_id = data.get("video_id")

    if type(video_id) is not int or video_id <= 0:
        return jsonify(error="A valid video_id is required."), 400

    video = db.session.get(videos, video_id)

    if video is None:
        return jsonify(error="Video not found."), 404

    playlist = db.session.execute(
        db.select(Playlists).where(
            Playlists.ti_user == user.ti_user_id,
            Playlists.title == "Watch Later",
        )
    ).scalar_one_or_none()

    if playlist is not None and video in playlist.videos:
        return jsonify(message="Video is already in Watch Later."), 200

    try:
        if playlist is None:
            playlist = Playlists(
                ti_user=user.ti_user_id,
                title="Watch Later",
            )
            db.session.add(playlist)

        playlist.videos.append(video)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(message="Video added to Watch Later."), 201
    

@library_bp.post("/add-to-saved-videos")
def add_to_saved_videos():
    user = get_current_user()

    if user is None:
        return jsonify(error="Please log in to save videos."), 401

    data = request.get_json(silent=True) or {}
    video_id = data.get("video_id")

    if type(video_id) is not int or video_id <= 0:
        return jsonify(error="A valid video_id is required."), 400

    video = db.session.get(videos, video_id)

    if video is None:
        return jsonify(error="Video not found."), 404

    playlist = db.session.execute(
        db.select(Playlists).where(
            Playlists.ti_user == user.ti_user_id,
            Playlists.title == "Saved Videos",
        )
    ).scalar_one_or_none()

    if playlist is not None and video in playlist.videos:
        return jsonify(message="Video is already saved."), 200

    try:
        if playlist is None:
            playlist = Playlists(
                ti_user=user.ti_user_id,
                title="Saved Videos",
            )
            db.session.add(playlist)

        playlist.videos.append(video)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(message="Video added to Saved Videos."), 201

@library_bp.post("/api/playlists/<int:playlist_id>/videos")
def add_to_playlist(playlist_id):
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    video_id = data.get("video_id")

    if type(video_id) is not int or video_id <= 0:
        return jsonify(error="A valid video_id is required."), 400

    # Continue with your existing user, playlist and video checks.

    playlist = db.session.execute(
        db.select(Playlists).where(
            Playlists.id == playlist_id,
            Playlists.ti_user == user.ti_user_id,
        )
    ).scalar_one_or_none()

    if playlist is None:
        return jsonify(error="Playlist not found."), 404

    video = db.session.get(videos, video_id)
    if video is None:
        return jsonify(error="Video not found."), 404

    if video in playlist.videos:
        return jsonify(message="Video is already in this playlist."), 200

    try:
        playlist.videos.append(video)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(message="Video added to playlist."), 201

@library_bp.post("/create-playlist")
def create_playlist():
    user = get_current_user()
    if user is None:
        return redirect(url_for("login"))

    title = request.form.get("title", "").strip()

    if not title:
        return jsonify(error="Playlist title is required."), 400

    if len(title) > 200:
        return jsonify(error="Title must be 200 characters or fewer."), 400

    # Reserve these exact names for the default playlists.
    if title in ("Watch Later", "Saved Videos"):
        return jsonify(error="This playlist title is reserved."), 400

    playlist = Playlists(
        ti_user=user.ti_user_id,
        title=title,
    )

    try:
        db.session.add(playlist)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return redirect(url_for("library.library"), code=303)