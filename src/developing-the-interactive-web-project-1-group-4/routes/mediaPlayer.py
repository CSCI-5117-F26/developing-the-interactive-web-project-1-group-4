from flask import render_template, request, jsonify, abort, session,url_for, redirect
from ..database import db
from . import mediaPlayer_bp
from ..models import Playlists
from ..services import get_current_user
from ..mediaPlayerServices import (
    NotFoundError, ValidationError, ConflictError,
    getVideo, addView, videoDetails, fetchRecommendations,
    countLikes, userLikedVideo, setLike,
    fetchComments, addComment, commentPageSize,
    fetchPlaylists, createPlaylist, addVideoToPlaylist, removeVideoFromPlaylist,
)

recommendations = [
    {
        "id": 12,
        "title": "Introduction to Python",
        "thumbnail_url": "",
        "description": "Learn Python basics.",
        "duration_text": "03:10",
        "author": "unknown",
        "author_url": "hehe", 
    },
    {
        "id": 15,
        "title": "Flask Web Development",
        "thumbnail": "",
        "description": "Build web apps with Flask.",
        "duration_text": "03:10",
        "author": "unknown",
        "author_url": "hehe", 
    },
    {
        "id": 15,
        "title": "Flask Web Development",
        "thumbnail": "",
        "description": "Build web apps with Flask.",
        "duration_text": "03:10",
        "author": "unknown",
        "author_url": "hehe", 
    }
]

# ---------------- Helpers ----------------

def currentUser():
    """The logged-in user, or None for visitors."""
    return get_current_user() if session.get("user") else None


def loginRequired():
    return jsonify(error="Please log in first."), 401


def readJson():
    # Only accepts JSON bodies. This also protects against other websites
    # submitting hidden forms to these endpoints (CSRF).
    return request.get_json(silent=True) or {}


def readInt(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@mediaPlayer_bp.errorhandler(NotFoundError)
def handleNotFound(error):
    return jsonify(error=str(error)), 404


@mediaPlayer_bp.errorhandler(ValidationError)
def handleValidation(error):
    return jsonify(error=str(error)), 400


@mediaPlayer_bp.errorhandler(ConflictError)
def handleConflict(error):
    return jsonify(error=str(error)), 409


# ---------------- Page ----------------

@mediaPlayer_bp.get("/watch/<int:videoId>")
def watchVideo(videoId):
    # dummy variables
    mode = "Playlist"
    comments = [
        {
            "author": "Taylor Slow",
            "comment": ("The high notes were a master class in talent, please teach me your ways"),
            "timecommented": "5 hours ago"
        },
        {
            "author": "Taylor Fast",
            "comment": ("The high notes were a master class in talent, please teach me your ways"),
            "timecommented": "5 hours ago"
        }
    ]

    try:
        video = getVideo(videoId)
    except NotFoundError:
        abort(404)

    addView(videoId)
    user = currentUser()
    playlist = None
    previous_video_url = None
    next_video_url = None

    playlist_id = request.args.get("playlist_id", type=int)

    if "playlist_id" in request.args:
        if playlist_id is None:
            abort(400, description="Invalid playlist ID.")

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
        video_ids = [video.id for video in ordered_videos]

        if videoId not in video_ids:
            abort(404, description="Video not found in this playlist.")

        index = video_ids.index(videoId)

        if index > 0:
            previous_video_url = url_for(
                "mediaPlayer.watchVideo",
                videoId=video_ids[index - 1],
                playlist_id=playlist.id,
            )

        if index < len(video_ids) - 1:
            next_video_url = url_for(
                "mediaPlayer.watchVideo",
                videoId=video_ids[index + 1],
                playlist_id=playlist.id,
            )
    return render_template(
        "watch.html",
        mode = mode,
        comments = comments,
        video=videoDetails(video, user),
        recommendations=recommendations,
        # comments=fetchComments(videoId),
        playlist=playlist,
        previous_video_url=previous_video_url,
        next_video_url=next_video_url,
        loggedIn=user is not None,
    )


# ---------------- Video ----------------

@mediaPlayer_bp.get("/api/videos/<int:videoId>")
def getVideoDetails(videoId):
    return jsonify(videoDetails(getVideo(videoId), currentUser()))


@mediaPlayer_bp.get("/api/videos/<int:videoId>/recommendations")
def getRecommendations(videoId):
    return jsonify(fetchRecommendations(getVideo(videoId)))


# ---------------- Likes ----------------

@mediaPlayer_bp.get("/api/videos/<int:videoId>/likes")
def getLikes(videoId):
    getVideo(videoId)
    return jsonify(likeCount=countLikes(videoId), likedByMe=userLikedVideo(videoId, currentUser()))


@mediaPlayer_bp.post("/api/videos/<int:videoId>/likes")
def likeVideo(videoId):
    user = currentUser()
    if user is None:
        return loginRequired()
    return jsonify(setLike(videoId, user, liked=True))


@mediaPlayer_bp.delete("/api/videos/<int:videoId>/likes")
def unlikeVideo(videoId):
    user = currentUser()
    if user is None:
        return loginRequired()
    return jsonify(setLike(videoId, user, liked=False))


# ---------------- Comments ----------------

@mediaPlayer_bp.get("/api/videos/<int:videoId>/comments")
def getComments(videoId):
    offset = max(0, readInt(request.args.get("offset"), 0))
    limit = min(50, max(1, readInt(request.args.get("limit"), commentPageSize)))
    return jsonify(fetchComments(videoId, offset, limit))


@mediaPlayer_bp.post("/api/videos/<int:videoId>/comments")
def postComment(videoId):
    user = currentUser()
    if user is None:
        return loginRequired()
    data = readJson()
    comment = addComment(videoId, user, data.get("comment"), readInt(data.get("parentId")))
    return jsonify(comment), 201


# ---------------- Playlists ----------------
"""
@mediaPlayer_bp.get("/api/playlists")
def getPlaylists():
    user = currentUser()
    if user is None:
        return loginRequired()
    return jsonify(fetchPlaylists(user, readInt(request.args.get("videoId"))))


@mediaPlayer_bp.post("/api/playlists")
def postPlaylist():
    user = currentUser()
    if user is None:
        return loginRequired()
    data = readJson()
    playlist = createPlaylist(user, data.get("title"), readInt(data.get("videoId")))
    return jsonify(playlist), 201


@mediaPlayer_bp.post("/api/playlists/<int:playlistId>/videos")
def postPlaylistVideo(playlistId):
    user = currentUser()
    if user is None:
        return loginRequired()
    videoId = readInt(readJson().get("videoId"))
    if videoId is None:
        return jsonify(error="videoId is required."), 400
    return jsonify(addVideoToPlaylist(playlistId, videoId, user))


@mediaPlayer_bp.delete("/api/playlists/<int:playlistId>/videos/<int:videoId>")
def deletePlaylistVideo(playlistId, videoId):
    user = currentUser()
    if user is None:
        return loginRequired()
    return jsonify(removeVideoFromPlaylist(playlistId, videoId, user))
    """