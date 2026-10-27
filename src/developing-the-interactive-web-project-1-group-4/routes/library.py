from flask import render_template, request, jsonify, url_for, redirect, abort
from ..models import Playlists, videos
from . import library_bp
from ..services import (
    fetchVideos, fetchGenres, fetchArtistVideos, searchAll, text_wrap,mediaURL,
    SEARCH_PREVIEW_LIMIT, SEARCH_PAGE_LIMIT, get_current_user, defaultCoverURL
)
from ..database import db
from dotenv import load_dotenv
load_dotenv()
import os
@library_bp.get("/library")
def library():
    user = get_current_user()

    if user is None:
        return redirect(url_for("login"))

    playlists = []
    saved_videos = []
    watchlater = []

    for playlist in user.playlists:
        if playlist.title == os.environ["WATCH_LATER"]:
            watchlater.extend(playlist.videos)
        elif playlist.title == os.environ["SAVED_VIDEOS"]:
            saved_videos.extend(playlist.videos)
        else:
            playlists.append(playlist)

    return render_template(
        "library.html",
        playlists=playlists,
        saved_videos=saved_videos,
        watchlater=watchlater,
        mediaURL=mediaURL,
        default_thumbnail_url=defaultCoverURL(),
    )

@library_bp.post("/add-to-watch-later")
def add_to_watch_later():
    user = get_current_user()

    if user is None:
        return jsonify(error="Please log in to add to Watch Later."), 401

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
            Playlists.title == os.environ["WATCH_LATER"],
        )
    ).scalar_one_or_none()

    if playlist is not None and video in playlist.videos:
        return jsonify(message="Video is already in Watch Later."), 200

    try:
        if playlist is None:
            playlist = Playlists(
                ti_user=user.ti_user_id,
                title=os.environ["WATCH_LATER"],
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
            Playlists.title == os.environ["SAVED_VIDEOS"],
        )
    ).scalar_one_or_none()

    if playlist is not None and video in playlist.videos:
        return jsonify(message="Video is already saved."), 200

    try:
        if playlist is None:
            playlist = Playlists(
                ti_user=user.ti_user_id,
                title=os.environ["SAVED_VIDEOS"],
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

    if user is None:
        return jsonify(error="Please log in to add to playlist."), 401

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

@library_bp.post("/remove-from-library")
def remove_from_library():
    """Take a video out of the user's Saved Videos or Watch Later list."""
    user = get_current_user()

    if user is None:
        return jsonify(error="Please log in."), 401

    data = request.get_json(silent=True) or {}
    video_id = data.get("video_id")
    list_name = data.get("list")

    if type(video_id) is not int or video_id <= 0:
        return jsonify(error="A valid video_id is required."), 400

    titles = {
        "saved": os.environ["SAVED_VIDEOS"],
        "watchlater": os.environ["WATCH_LATER"],
    }
    if list_name not in titles:
        return jsonify(error="Unknown list."), 400

    playlist = db.session.execute(
        db.select(Playlists).where(
            Playlists.ti_user == user.ti_user_id,
            Playlists.title == titles[list_name],
        )
    ).scalar_one_or_none()
    video = db.session.get(videos, video_id)

    if playlist is None or video is None or video not in playlist.videos:
        return jsonify(error="Video is not in this list."), 404

    try:
        playlist.videos.remove(video)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(message="Video removed."), 200


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
    if title in (os.environ["WATCH_LATER"], os.environ["SAVED_VIDEOS"]):
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

    # The Add to playlist pop-up creates a playlist with fetch() and needs its id back.
    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify(id=playlist.id, title=playlist.title), 201

    return redirect(url_for("library.library"), code=303)


@library_bp.post("/playlists/<int:playlist_id>/delete")
def delete_playlist(playlist_id):
    """Delete one of the user's own playlists (never Watch Later / Saved Videos)."""
    user = get_current_user()

    if user is None:
        return jsonify(error="Please log in."), 401

    playlist = db.session.execute(
        db.select(Playlists).where(
            Playlists.id == playlist_id,
            Playlists.ti_user == user.ti_user_id,
        )
    ).scalar_one_or_none()

    if playlist is None:
        return jsonify(error="Playlist not found."), 404

    if playlist.title in (os.environ["WATCH_LATER"], os.environ["SAVED_VIDEOS"]):
        return jsonify(error="This playlist can't be deleted."), 400

    try:
        playlist.videos.clear()          # remove the links only; the videos themselves stay
        db.session.delete(playlist)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify(message="Playlist deleted."), 200


@library_bp.get("/playlists/<int:playlist_id>/play")
def play_playlist(playlist_id):
    user = get_current_user()

    if user is None:
        return redirect(url_for("login"))

    playlist = db.session.execute(
        db.select(Playlists).where(
            Playlists.id == playlist_id,
            Playlists.ti_user == user.ti_user_id,
        )
    ).scalar_one_or_none()

    if playlist is None:
        abort(404, description="Playlist not found.")

    ordered_videos = sorted(playlist.videos, key=lambda video: video.id)

    if not ordered_videos:
        return redirect(url_for("library.library"))

    if "video_id" in request.args:
        selected_video_id = request.args.get("video_id", type=int)

        if selected_video_id is None:
            abort(400, description="Invalid video ID.")

        if selected_video_id not in {video.id for video in ordered_videos}:
            abort(404, description="Video not found in this playlist.")
    else:
        selected_video_id = ordered_videos[0].id

    return redirect(url_for(
        "mediaPlayer.watchVideo",
        videoId=selected_video_id,
        playlist_id=playlist.id,
        autoplay=1,
    ))