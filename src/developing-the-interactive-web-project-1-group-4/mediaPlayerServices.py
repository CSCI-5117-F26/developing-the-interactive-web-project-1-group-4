from sqlalchemy import select, func, case, or_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from .database import db
from .models import (
    videos as Video, Genres, Comments, Likes, Playlists, video_genres,
)
from .services import mediaURL, videoCard, videoQuery, addStats

recommendationLimit = 10
commentPageSize = 20
commentMaxLength = 2000
playlistTitleMaxLength = 200 


# ---------------- Errors the routes turn into HTTP responses ----------------
class NotFoundError(Exception):      # -> 404
    pass

class ValidationError(Exception):    # -> 400
    pass

class ConflictError(Exception):      # -> 409
    pass


# ---------------- Time helpers ----------------
def databaseNow():
    """Current time from Postgres, the same clock that filled created_at."""
    return db.session.scalar(select(func.localtimestamp()))


def timeAgo(then, now):
    """datetime -> '15 minutes ago', '1 year ago', 'just now'"""
    seconds = max(0, int((now - then).total_seconds()))
    units = [
        ("year", 365 * 24 * 3600),
        ("month", 30 * 24 * 3600),
        ("week", 7 * 24 * 3600),
        ("day", 24 * 3600),
        ("hour", 3600),
        ("minute", 60),
    ]
    for name, size in units:
        count = seconds // size
        if count >= 1:
            return f"{count} {name}{'s' if count > 1 else ''} ago"
    return "just now"


# ---------------- Video ----------------
def getVideo(videoId):
    video = db.session.scalar(videoQuery().where(Video.id == videoId))
    if video is None:
        raise NotFoundError("Video not found.")
    return video


def addView(videoId):
    """views = views + 1, done inside the database so two viewers can't overwrite each other."""
    db.session.execute(update(Video).where(Video.id == videoId).values(views=Video.views + 1))
    db.session.commit()


def videoDetails(video, user):
    now = databaseNow()
    details = videoCard(video)
    uploader = video.uploader
    details.update({
        "description": video.description or "",
        "language": video.language,
        "original": video.Original,
        "uploadedAt": video.created_at.isoformat(),
        "uploadedAgo": timeAgo(video.created_at, now),
        "artistName": f"{uploader.first_name} {uploader.last_name}".strip() if uploader else "",
        "artistPicture": (mediaURL(uploader.Profile_picture_key) if uploader else None) or "",
        "likeCount": countLikes(video.id),
        "likedByMe": userLikedVideo(video.id, user),
    })
    addStats([details])
    return details


# ---------------- Recommendations ----------------
def fetchRecommendations(video, limit=recommendationLimit):
    """Same artist and/or same genre first; if there aren't enough, fill with popular videos."""
    genreIds = [g.id for g in video.genres]

    sameArtist = case((Video.ti_user == video.ti_user, 1), else_=0)
    sharedGenres = (
        select(func.count())
        .select_from(video_genres)
        .where(video_genres.c.video_id == Video.id, video_genres.c.genre_id.in_(genreIds))
        .scalar_subquery()
    )

    stmt = (
        videoQuery()
        .where(
            Video.id != video.id,
            or_(Video.ti_user == video.ti_user, Video.genres.any(Genres.id.in_(genreIds))),
        )
        .order_by(sameArtist.desc(), sharedGenres.desc(), Video.views.desc(), Video.created_at.desc())
        .limit(limit)
    )
    results = list(db.session.scalars(stmt))

    if len(results) < limit:
        excludeIds = [video.id] + [v.id for v in results]
        filler = (
            videoQuery()
            .where(Video.id.not_in(excludeIds))
            .order_by(Video.views.desc(), Video.created_at.desc())
            .limit(limit - len(results))
        )
        results += list(db.session.scalars(filler))

    cards = []
    for v in results:
        card = videoCard(v)
        if v.ti_user == video.ti_user:
            card["reason"] = "sameArtist"
        elif any(g.id in genreIds for g in v.genres):
            card["reason"] = "sameGenre"
        else:
            card["reason"] = "popular"
        cards.append(card)
    return addStats(cards)


# ---------------- Likes ----------------
def countLikes(videoId):
    return db.session.scalar(select(func.count()).select_from(Likes).where(Likes.video_id == videoId))


def userLikedVideo(videoId, user):
    if user is None:
        return False
    likeId = db.session.scalar(
        select(Likes.id).where(Likes.video_id == videoId, Likes.ti_user == user.ti_user_id)
    )
    return likeId is not None


def setLike(videoId, user, liked):
    """liked=True -> like, liked=False -> unlike. Safe to call twice (double clicks)."""
    getVideo(videoId)   # 404 if the video doesn't exist
    existing = db.session.scalar(
        select(Likes).where(Likes.video_id == videoId, Likes.ti_user == user.ti_user_id)
    )
    if liked and existing is None:
        db.session.add(Likes(ti_user=user.ti_user_id, video_id=videoId))
    elif not liked and existing is not None:
        db.session.delete(existing)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()   # the like already exists (two clicks at once); that's fine

    return {"likedByMe": liked, "likeCount": countLikes(videoId)}


# ---------------- Comments ----------------
def commentCard(comment, now):
    author = comment.ti_user
    return {
        "id": comment.id,
        "parentId": comment.parent_id,
        "comment": comment.comment,
        "username": author.username if author else "",
        "userPicture": (mediaURL(author.Profile_picture_key) if author else None) or "",
        "createdAt": comment.created_at.isoformat(),
        "timeAgo": timeAgo(comment.created_at, now),
    }


def fetchComments(videoId, offset=0, limit=commentPageSize):
    getVideo(videoId)
    total = db.session.scalar(
        select(func.count()).select_from(Comments).where(Comments.video_id == videoId)
    )
    stmt = (
        select(Comments)
        .options(selectinload(Comments.ti_user))
        .where(Comments.video_id == videoId)
        .order_by(Comments.created_at.desc(), Comments.id.desc())
        .offset(offset)
        .limit(limit)
    )
    now = databaseNow()
    comments = [commentCard(c, now) for c in db.session.scalars(stmt)]
    return {
        "comments": comments,
        "total": total,
        "hasMore": offset + len(comments) < total,
    }


def addComment(videoId, user, text, parentId=None):
    getVideo(videoId)
    text = (text or "").strip()
    if not text:
        raise ValidationError("Comment can't be empty.")
    if len(text) > commentMaxLength:
        raise ValidationError(f"Comment must be {commentMaxLength} characters or fewer.")

    if parentId is not None:
        parent = db.session.get(Comments, parentId)
        if parent is None or parent.video_id != videoId:
            raise ValidationError("You can only reply to a comment on this video.")

    comment = Comments(video_id=videoId, user_id=user.ti_user_id, comment=text, parent_id=parentId)
    db.session.add(comment)
    db.session.commit()
    return commentCard(comment, databaseNow())


# ---------------- Playlists ----------------
def playlistCard(playlist, videoId=None):
    return {
        "id": playlist.id,
        "title": playlist.title,
        "videoCount": len(playlist.videos),
        "containsVideo": videoId is not None and any(v.id == videoId for v in playlist.videos),
    }


def fetchPlaylists(user, videoId=None):
    stmt = (
        select(Playlists)
        .options(selectinload(Playlists.videos))
        .where(Playlists.ti_user == user.ti_user_id)
        .order_by(Playlists.created_at.desc())
    )
    return [playlistCard(p, videoId) for p in db.session.scalars(stmt)]


def getOwnPlaylist(playlistId, user):
    """A playlist that belongs to this user. Other people's playlists look 'not found'."""
    playlist = db.session.get(Playlists, playlistId)
    if playlist is None or playlist.ti_user != user.ti_user_id:
        raise NotFoundError("Playlist not found.")
    return playlist


def createPlaylist(user, title, videoId=None):
    title = (title or "").strip()
    if not title:
        raise ValidationError("Playlist name can't be empty.")
    if len(title) > playlistTitleMaxLength:
        raise ValidationError(f"Playlist name must be {playlistTitleMaxLength} characters or fewer.")

    duplicate = db.session.scalar(
        select(Playlists.id).where(
            Playlists.ti_user == user.ti_user_id,
            func.lower(Playlists.title) == title.lower(),
        )
    )
    if duplicate is not None:
        raise ConflictError("You already have a playlist with that name.")

    playlist = Playlists(ti_user=user.ti_user_id, title=title)
    if videoId is not None:
        playlist.videos.append(getVideo(videoId))

    db.session.add(playlist)
    db.session.commit()
    return playlistCard(playlist, videoId)


def addVideoToPlaylist(playlistId, videoId, user):
    playlist = getOwnPlaylist(playlistId, user)
    video = getVideo(videoId)
    alreadyAdded = video in playlist.videos
    if not alreadyAdded:
        playlist.videos.append(video)
        db.session.commit()
    card = playlistCard(playlist, videoId)
    card["alreadyAdded"] = alreadyAdded
    return card


def removeVideoFromPlaylist(playlistId, videoId, user):
    playlist = getOwnPlaylist(playlistId, user)
    video = getVideo(videoId)
    if video in playlist.videos:
        playlist.videos.remove(video)
        db.session.commit()
    return playlistCard(playlist, videoId)