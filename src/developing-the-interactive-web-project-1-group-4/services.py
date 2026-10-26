
from .database import db
from .models import *
import subprocess
import json, os, re
from flask import current_app , session, url_for, request
from .models import db, Ti_user
from .storage import r2
from uuid import uuid4
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from sqlalchemy import func, or_, select, func
from sqlalchemy.orm import selectinload
from .models import videos as Video, Genres, Ti_user, video_genres, Drafts
import av

trendingVideoLimit = 20
trendingArtistLimit = 20
genrePageLimit = 60

from .models import videos as Video, Genres, Ti_user, video_genres

load_dotenv()
def create_dummy_user(username: str, email: str, first_name: str, last_name: str):
    user = Ti_user(username=username, email=email, first_name=first_name, last_name=last_name)
    db.session.add(user)
    db.session.commit()
    return user
def create_dummy_genre(name: str):
    genre = Genres(name=name)
    db.session.add(genre)
    db.session.commit()
    return genre
def create_dummy_video(ti_user:int,thumbnail_key:str,duration:int,title:str,video_key:str,language:str,original:bool):
    video = videos(ti_user=ti_user, thumbnail_key=thumbnail_key, duration=duration, title=title, video_key=video_key, language=language, Original=original)
    db.session.add(video)
    db.session.commit()
    return video
def get_thumbnails_url():
    thumbnail_keys = [
            "thumbnails/0067769d-f9fd-4a79-983e-ec8660fdaff4-2.jpg",
        ]
    
    thumbnails = []
    
    for key in thumbnail_keys:
        url = r2.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": os.environ["R2_BUCKET_NAME"],
                "Key": key,
            },
            ExpiresIn=3600
        )
    
        thumbnails.append({
            "key": key,
            "url": url,
        })
    
    return thumbnails


def upload_video_to_cloud(video):
    filename = secure_filename(video.filename or "")

    if not filename:
        raise ValueError("Please select a file with a valid filename.")

    # Unique key prevents files with the same name overwriting each other.
    video_key = f"videos/{uuid4()}-{filename}"

    r2.upload_fileobj(
        Fileobj=video.stream,
        Bucket=os.environ["R2_BUCKET_NAME"],
        Key=video_key,
        ExtraArgs={
            "ContentType": video.mimetype or "application/octet-stream"
        }
    )

    return video_key

def upload_thumbnail_to_cloud(thumbnail):
    filename = secure_filename(thumbnail.filename or "")

    if not filename:
        raise ValueError("Please select a file with a valid filename.")

    # Unique key prevents files with the same name overwriting each other.
    thumbnail_key = f"thumbnails/{uuid4()}-{filename}"

    r2.upload_fileobj(
        Fileobj=thumbnail.stream,
        Bucket=os.environ["R2_BUCKET_NAME"],
        Key=thumbnail_key,
        ExtraArgs={
            "ContentType": thumbnail.mimetype or "application/octet-stream"
        }
    )

    return thumbnail_key



def get_upload_form_data():
    def optional_text(name):
        value = request.form.get(name, "").strip()
        return value or None

    return {
        "video_key": optional_text("video_key"),
        "thumbnail_key": optional_text("thumbnail_key"),
        "title": optional_text("title"),
        "description": optional_text("description"),
        "genres": list(dict.fromkeys(
            genre.strip()
            for genre in request.form.getlist("genre")
            if genre.strip()
        )),
        "video_type": optional_text("video_type"),
        "language": optional_text("language"),
    }

def create_video_helper(ti_user, thumbnail_key, duration, title, description, genres, video_key, language, original):
    video = videos(ti_user=ti_user, thumbnail_key=thumbnail_key, duration=duration, title=title, description=description, video_key = video_key, language=language, Original=original)
    genre_records = db.session.execute(
        db.select(Genres).where(Genres.name.in_(genres))
    ).scalars().all()
    video.genres = genre_records
    try:
        db.session.add(video)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

def create_draft_helper(ti_user, thumbnail_key, duration, title, description, genres, video_key, language, original):
    draft = Drafts(ti_user=ti_user, thumbnail_key=thumbnail_key, duration=duration, title=title, description=description, video_key = video_key, language=language, Original=original)
    if genres:
        genre_records = db.session.execute(
                db.select(Genres).where(Genres.name.in_(genres))
            ).scalars().all()
        draft.genres = genre_records
    try:
        db.session.add(draft)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def mediaURL(key, expires=3600):
    #Turn an R2 file key into a temporary link (valid 1 hour).
    if not key:
        return None
    # Imported here so the app still starts on computers without R2 settings
    from .storage import r2, bucket_name
    return r2.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": key},
        ExpiresIn=expires,
    )


def formatDuration(seconds):
    #180 -> '3:00', 3725 -> '1:02:05'
    if not seconds:
        return ""
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02}:{secs:02}" if hours else f"{minutes}:{secs:02}"


def text_wrap(text, max_length = 50):
    words = text.split()
    lines = []
    line = ""

    for word in words:
        test_line = f"{line} {word}".strip()
        if len(test_line) > max_length and line:
            lines.append(line)
            line = word
        else:
            line = test_line

    if line: 
        lines.append(line)
    return lines

def getVideoDuration(video):
    """
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            video,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    """
    with av.open(video) as container:
        if container.duration is not None:
            return float(container.duration / av.time_base)

        for stream in container.streams.video:
            if stream.duration is not None and stream.time_base is not None:
                return float(stream.duration * stream.time_base)
    #duration = float(result.stdout.strip())
    raise ValueError("Could not determine video duration.")

def saveProfile(
    username,
    first_name,
    last_name,
    email,
    auth0_id,
    bio=None,
    phone_number=None,
    profile_picture_key=None,
    contact_me=None
):
    user = Ti_user(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        auth0_id=auth0_id,
        Bio=bio,
        Phone_number=phone_number,
        Profile_picture_key=profile_picture_key,
        contact_me=contact_me,
    )

    db.session.add(user)
    db.session.commit()

def upload_profile_picture_to_cloud(profile_picture):
    filename = secure_filename(profile_picture.filename or "")

    if not filename:
        raise ValueError("Please select a file with a valid filename.")

    # Unique key prevents files with the same name overwriting each other.
    profile_picture_key = f"profile_photos/{uuid4()}-{filename}"

    r2.upload_fileobj(
        Fileobj=profile_picture.stream,
        Bucket=os.environ["R2_BUCKET_NAME"],
        Key=profile_picture_key,
        ExtraArgs={
            "ContentType": profile_picture.mimetype or "application/octet-stream"
        }
    )

    return profile_picture_key

def get_current_user():
    login_user = session.get("user")
    auth0_id = (
        login_user.get("userinfo", {}).get("sub")
        if login_user else None
    )

    if not auth0_id:
        return None

    return db.session.execute(
        db.select(Ti_user).where(Ti_user.auth0_id == auth0_id)
    ).scalar_one_or_none()

# ======================= Home page & search =======================
HOME_PAGE_LIMIT = 24
SEARCH_PREVIEW_LIMIT = 5     # per group, in the dropdown
SEARCH_PAGE_LIMIT = 60       # per group, on the full results page
MAX_SEARCH_WORDS = 8

def searchWords(q):
    """'Country  Roads!' -> ['country', 'roads']  (letters and digits only)"""
    return re.findall(r"[^\W_]+", q.lower())[:MAX_SEARCH_WORDS]


def likePattern(text):
    """Escape % and _ so they're treated as normal characters in ILIKE."""
    escaped = text.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")
    return f"%{escaped}%"


def textMatch(column, q, words):
    """Full-text prefix match OR plain substring match, plus a relevance rank."""
    substring = column.ilike(likePattern(q), escape="\\")
    if not words:
        return substring, func.length(column) * 0     # rank 0 for everyone

    vector = func.to_tsvector("simple", column)
    query = func.to_tsquery("simple", " & ".join(f"{w}:*" for w in words))
    return or_(vector.op("@@")(query), substring), func.ts_rank(vector, query)

# ---------- Views & likes on video cards ----------

def formatCount(n):
    """856 -> '856', 1200 -> '1.2K', 2400000 -> '2.4M'"""
    n = n or 0
    if n < 1000:
        return str(n)
    if n < 1_000_000:
        return f"{n / 1000:.1f}".rstrip("0").rstrip(".") + "K"
    return f"{n / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"


def likeCounts(videoIds):
    """{videoId: likeCount} for many videos in ONE query."""
    if not videoIds:
        return {}
    rows = db.session.execute(
        select(Likes.video_id, func.count(Likes.id))
        .where(Likes.video_id.in_(videoIds))
        .group_by(Likes.video_id)
    )
    return dict(rows.all())


def addStats(cards):
    """Add views, likes, viewsText and likesText to every card (needs 'id' and 'views')."""
    counts = likeCounts([card["id"] for card in cards])
    for card in cards:
        views = card.get("views") or 0
        likes = counts.get(card["id"], 0)
        card.update(
            views=views,
            likes=likes,
            viewsText=formatCount(views),
            likesText=formatCount(likes),
        )
    return cards

# ---------- Turning database rows into page data ----------

def videoCard(v):
    fallback = defaultCoverURL()
    return {
        "id": v.id,
        "title": v.title,
        "artist": v.uploader.username if v.uploader else "",
        "genres": [g.name for g in v.genres],
        "cover": mediaURL(v.thumbnail_key) or fallback,
        "fallbackCover": fallback,
        "videoURL": mediaURL(v.video_key),
        "durationText": formatDuration(v.duration),
        "views": v.views,
        "watchURL": url_for("mediaPlayer.watchVideo", videoId=v.id),
    }


def artistCard(user, videoCount):
    return {
        "username": user.username,
        "displayName": f"{user.first_name} {user.last_name}".strip(),
        "picture": mediaURL(user.Profile_picture_key) or "",
        "videoCount": videoCount,
        "url": url_for("homePage.search", artist=user.username),
    }


def genreCard(name, videoCount):
    return {
        "name": name,
        "videoCount": videoCount,
        "url": url_for("homePage.home", genre=name),
    }


def videoQuery():
    """Base query for videos, loading genres and uploader in the same round trip."""
    return select(Video).options(selectinload(Video.genres), selectinload(Video.uploader))


# ---------- Home page ----------

def fetchVideos(genre="", limit=HOME_PAGE_LIMIT):
    stmt = videoQuery().order_by(Video.created_at.desc())
    if genre:
        stmt = stmt.where(Video.genres.any(Genres.name == genre))
    return addStats([videoCard(v) for v in db.session.scalars(stmt.limit(limit))])


def fetchGenres():
    names = db.session.scalars(select(Genres.name).order_by(Genres.name)).all()
    return [{"name": n} for n in names]


def fetchArtistVideos(username, limit=SEARCH_PAGE_LIMIT):
    user = db.session.scalar(select(Ti_user).where(Ti_user.username == username))
    if user is None:
        return None, []
    stmt = (
        videoQuery()
        .where(Video.ti_user == user.ti_user_id)
        .order_by(Video.created_at.desc())
        .limit(limit)
    )
    videos = addStats([videoCard(v) for v in db.session.scalars(stmt)])
    return artistCard(user, len(videos)), videos


# ---------- Search ----------

def searchVideos(q, words, limit):
    condition, rank = textMatch(Video.title, q, words)
    stmt = (
        videoQuery()
        .where(condition)
        .order_by(rank.desc(), Video.views.desc(), Video.created_at.desc())
        .limit(limit)
    )
    return addStats([videoCard(v) for v in db.session.scalars(stmt)])


def searchArtists(q, words, limit):
    fullName = func.concat_ws(" ", Ti_user.username, Ti_user.first_name, Ti_user.last_name)
    condition, rank = textMatch(fullName, q, words)
    videoCount = func.count(Video.id)
    stmt = (
        select(Ti_user, videoCount)
        .join(Video, Video.ti_user == Ti_user.ti_user_id)   # only users who have uploaded
        .where(condition)
        .group_by(Ti_user.ti_user_id)
        .order_by(rank.desc(), videoCount.desc())
        .limit(limit)
    )
    return [artistCard(user, count) for user, count in db.session.execute(stmt)]


def searchGenres(q, words, limit):
    condition, rank = textMatch(Genres.name, q, words)
    videoCount = func.count(video_genres.c.video_id)
    stmt = (
        select(Genres.name, videoCount)
        .outerjoin(video_genres, video_genres.c.genre_id == Genres.id)
        .where(condition)
        .group_by(Genres.id, Genres.name)
        .order_by(rank.desc(), videoCount.desc())
        .limit(limit)
    )
    return [genreCard(name, count) for name, count in db.session.execute(stmt)]


def searchAll(q, limit):
    words = searchWords(q)
    return {
        "videos": searchVideos(q, words, limit),
        "artists": searchArtists(q, words, limit),
        "genres": searchGenres(q, words, limit),
    }

def defaultCoverURL():
    """Default thumbnail: the R2 file named in DEFAULT_THUMBNAIL_KEY (.env)."""
    key = os.environ.get("DEFAULT_THUMBNAIL_KEY", "").strip()
    if key:
        return mediaURL(key)
    # Safety net if the setting is missing: the static placeholder image
    return url_for("static", filename="images/square_test.png")

def get_subscribers_count(channel_id):
    return Subscriptions.query.filter_by(channel_id=channel_id).count()

def get_subscriptions_count(user_id):
    return Subscriptions.query.filter_by(subscriber_id=user_id).count()

# ======================= Account deletion =======================

def deleteRowsAndDependents(table, column, ids):
    """Delete rows of `table` where `column` is in `ids`,
    after first deleting every row in any table that points at them."""
    ids = list(ids)
    if not ids:
        return

    # The primary keys of the rows we're about to delete
    primaryKey = list(table.primary_key.columns)[0]
    rowIds = db.session.scalars(select(primaryKey).where(column.in_(ids))).all()

    # Delete children first: any table with a foreign key pointing at this table
    if rowIds:
        for childTable in db.metadata.sorted_tables:
            for foreignKey in childTable.foreign_keys:
                if foreignKey.column.table is table:
                    deleteRowsAndDependents(childTable, foreignKey.parent, rowIds)

    db.session.execute(delete(table).where(column.in_(ids)))


def deleteCloudFiles(keys):
    """Remove files from R2. Failures are logged, not raised (the account is already gone)."""
    from .storage import r2, bucket_name
    defaultKey = os.environ.get("DEFAULT_THUMBNAIL_KEY", "").strip()

    for key in set(keys):
        if not key or key == defaultKey:     # never delete the shared default thumbnail
            continue
        try:
            r2.delete_object(Bucket=bucket_name, Key=key)
        except Exception:
            current_app.logger.exception("Could not delete %s from R2", key)


def deleteAccountData(user):
    """Delete a user and EVERYTHING connected to them: database rows and R2 files."""
    userId = user.ti_user_id

    # 1. Collect the R2 file keys first; they can't be read once the rows are gone
    keys = [user.Profile_picture_key]
    for videoKey, thumbnailKey in db.session.execute(
        select(Video.video_key, Video.thumbnail_key).where(Video.ti_user == userId)
    ):
        keys += [videoKey, thumbnailKey]
    for videoKey, thumbnailKey in db.session.execute(
        select(Drafts.video_key, Drafts.thumbnail_key).where(Drafts.ti_user == userId)
    ):
        keys += [videoKey, thumbnailKey]

    # 2. Delete all database rows in one transaction (all or nothing)
    try:
        db.session.delete(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    # 3. Only after the database delete succeeded, remove the files
    deleteCloudFiles(keys)

# ======================= Trending page =======================
def addTitleLines(cards):
    """The vinyl card needs the title split into lines."""
    for card in cards:
        card["title_lines"] = text_wrap(card["title"], max_length=25)
    return cards


def artistProfileURL(username):
    """Where an artist tile links to: that artist's public profile page."""
    return url_for("profilePage.profile_page", username=username)


# ---------- Trending videos ----------
def fetchTrendingVideos(limit=trendingVideoLimit):
    stmt = videoQuery().order_by(Video.views.desc(), Video.created_at.desc()).limit(limit)
    return addTitleLines(addStats([videoCard(v) for v in db.session.scalars(stmt)]))


# ---------- Genres ----------
def fetchGenreCards():
    """Every genre, most-watched first, shaped like a vinyl card."""
    videoCount = func.count(Video.id)
    totalViews = func.coalesce(func.sum(Video.views), 0)
    rows = db.session.execute(
        select(Genres.id, Genres.name, videoCount, totalViews)
        .outerjoin(video_genres, video_genres.c.genre_id == Genres.id)
        .outerjoin(Video, Video.id == video_genres.c.video_id)
        .group_by(Genres.id, Genres.name)
        .order_by(totalViews.desc(), videoCount.desc(), Genres.name)
    ).all()

    # Placeholder art: the thumbnail of each genre's most-viewed video (one query, Postgres DISTINCT ON)
    topThumbnails = dict(db.session.execute(
        select(video_genres.c.genre_id, Video.thumbnail_key)
        .join(Video, Video.id == video_genres.c.video_id)
        .where(Video.thumbnail_key.is_not(None))
        .order_by(video_genres.c.genre_id, Video.views.desc())
        .distinct(video_genres.c.genre_id)
    ).all())

    fallback = defaultCoverURL()
    return [
        {
            "title": name,
            "title_lines": text_wrap(name, max_length=25),
            "cover": mediaURL(topThumbnails.get(genreId)) or fallback,
            "fallbackCover": fallback,
            "videoURL": None,        # a genre card isn't a playable video
            "videoCount": count,
            "totalViews": views,
            "url": url_for("trending.genrePage", genreName=name),
        }
        for genreId, name, count, views in rows
    ]


def getGenre(genreName):
    return db.session.scalar(select(Genres).where(Genres.name == genreName))


def fetchGenreVideos(genreName, limit=genrePageLimit):
    stmt = (
        videoQuery()
        .where(Video.genres.any(Genres.name == genreName))
        .order_by(Video.views.desc(), Video.created_at.desc())
        .limit(limit)
    )
    return addTitleLines(addStats([videoCard(v) for v in db.session.scalars(stmt)]))


# ---------- Trending artists ----------
def fetchTrendingArtists(limit=trendingArtistLimit):
    totalViews = func.coalesce(func.sum(Video.views), 0)
    videoCount = func.count(Video.id)
    stmt = (
        select(Ti_user, totalViews, videoCount)
        .join(Video, Video.ti_user == Ti_user.ti_user_id)   # only users who have uploaded
        .group_by(Ti_user.ti_user_id)
        .order_by(totalViews.desc(), videoCount.desc())
        .limit(limit)
    )
    artists = []
    fallback = defaultCoverURL()
    artists = []
    for user, views, count in db.session.execute(stmt):
        artists.append({
            "username": user.username,
            "displayName": f"{user.first_name} {user.last_name}".strip() or user.username,
            "picture": mediaURL(user.Profile_picture_key) or fallback,
            "fallbackPicture": fallback,
            "totalViews": views,
            "videoCount": count,
            "url": artistProfileURL(user.username),
        })
    return artists
    return artists

def get_owned_draft(user):
    draft_id = request.form.get("draft_id", type=int)

    if draft_id is None:
        return None

    return db.session.execute(
        db.select(Drafts).where(
            Drafts.id == draft_id,
            Drafts.ti_user == user.ti_user_id,
        )
    ).scalar_one_or_none()


def apply_draft_form(draft):
    """Validate submitted fields before changing the draft."""
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    language = request.form.get("language", "").strip()
    video_type = request.form.get("video_type", "").strip()

    if not title:
        raise ValueError("A video title is required.")
    if len(title) > 200:
        raise ValueError("Title must be 200 characters or fewer.")
    if len(description) > 10000:
        raise ValueError("Description is too long.")
    if len(language) > 100:
        raise ValueError("Language is too long.")
    if video_type not in ("", "original", "cover"):
        raise ValueError("Invalid video type.")

    # Assumes genre_options uses Genres.id as its option values.
    try:
        genre_names = {
            str(value)
            for value in request.form.getlist("genre")
        }
    except ValueError:
        raise ValueError("Invalid genre selection.")

    genres = []
    if genre_names:
        genres = db.session.execute(
            db.select(Genres).where(
                Genres.name.in_(genre_names)
            )
        ).scalars().all()

        if len(genres) != len(genre_names):
            raise ValueError("Invalid genre selection.")

    thumbnail_key = draft.thumbnail_key
    if "thumbnail_key" in request.form:
        thumbnail_key = request.form["thumbnail_key"].strip() or None

    if thumbnail_key and len(thumbnail_key) > 200:
        raise ValueError("Invalid thumbnail key.")

    draft.title = title
    draft.description = description or None
    draft.language = language or None
    draft.Original = (
        None if not video_type else video_type == "original"
    )
    draft.thumbnail_key = thumbnail_key
    draft.genres = genres

def create_default_playlists(user_id):
    titles = (os.environ["WATCH_LATER"], os.environ["SAVED_VIDEOS"])

    existing = db.session.execute(
        db.select(Playlists).where(
            Playlists.ti_user == user_id,
            Playlists.title.in_(titles),
        )
    ).scalars().all()

    playlists_by_title = {
        playlist.title: playlist for playlist in existing
    }

    try:
        for title in titles:
            if title not in playlists_by_title:
                playlist = Playlists(
                    ti_user=user_id,
                    title=title,
                )
                db.session.add(playlist)
                playlists_by_title[title] = playlist

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return playlists_by_title

def create_default_playlists_for_all_users():
    user_ids = db.session.scalars(
        db.select(Ti_user.ti_user_id)
    ).all()

    for user_id in user_ids:
        create_default_playlists(user_id)

    return len(user_ids)

