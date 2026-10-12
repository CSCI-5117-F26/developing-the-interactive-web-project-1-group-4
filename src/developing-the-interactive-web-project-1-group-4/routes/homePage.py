from flask import render_template, request, jsonify, url_for
from sqlalchemy.orm import selectinload
from ..services import mediaURL, formatDuration, text_wrap

from . import homePage_bp
from ..database import db
from ..models import videos as Video, Genres

# Switch to False once the database has real videos and R2 has their files
useSampleData = True


# ---------------- Sample data ----------------

dummyGenres = ["Pop", "Rock", "Country", "Rap", "RnB", "Punk"]

dummyVideos = [
    {"id": 1, "title": "It's My Life", "genre": "Rock", "duration": 180, "video_file": "videos/sample.mp4"},
    {"id": 2, "title": "Testing long long longgg title", "genre": "Pop", "duration": 200, "video_file": None},
    {"id": 3, "title": "Country Roads", "genre": "Country", "duration": 660, "video_file": None},
    {"id": 4, "title": "Rap Battle", "genre": "Rap", "duration": 299, "video_file": None},
    {"id": 5, "title": "Smooth RnB", "genre": "RnB", "duration": 840, "video_file": None},
    {"id": 6, "title": "Punk Night", "genre": "Punk", "duration": 67, "video_file": None},
]


def readFilters():
    #Read ?q= and ?genre= from the URL safely.
    q = request.args.get("q", "").strip()[:100]
    genre = request.args.get("genre", "").strip()
    if genre not in {g["name"] for g in fetchGenreType()}:
        genre = ""
    return q, genre


# ---------------- The two data functions ----------------

def fetchVideoFiles(q="", genre="", limit=24):
    #Videos matching the search text and genre, newest first.
    if useSampleData:
        results = []
        for v in dummyVideos:
            if q and q.lower() not in v["title"].lower():
                continue
            if genre and v["genre"] != genre:
                continue
            results.append({
                "id": v["id"],
                "title": v["title"],
                "genres": [v["genre"]],
                "cover": mediaURL("thumbnails/0067769d-f9fd-4a79-983e-ec8660fdaff4-2.jpg") if v["id"] == 1 else "",
                "video_url": url_for("static", filename=v["video_file"]) if v["video_file"] else None,
                "durationText": formatDuration(v["duration"]),
            })
        return results[:limit]

    # ----- Real database -----
    stmt = (
        db.select(Video)
        .options(selectinload(Video.genres))
        .order_by(Video.created_at.desc())
    )
    if q:
        stmt = stmt.where(Video.title.ilike(f"%{q}%"))
    if genre:
        stmt = stmt.where(Video.genres.any(Genres.name == genre))

    rows = db.session.scalars(stmt.limit(limit)).all()
    return [
        {
            "id": v.id,
            "title": v.title,
            "genres": [g.name for g in v.genres],
            "cover": mediaURL(v.thumbnail_key) or "",
            "videoURL": mediaURL(v.video_key),
            "durationText": formatDuration(v.duration),
        }
        for v in rows
    ]


def fetchGenreType():
    #Genre tags for the filter buttons.
    if useSampleData:
        return [{"name": g} for g in dummyGenres]

    names = db.session.scalars(db.select(Genres.name).order_by(Genres.name)).all()
    return [{"name": n} for n in names]


# ---------------- Routes ----------------

@homePage_bp.get("/")
def home():
    q, genre = readFilters()
    videos = fetchVideoFiles(q, genre)

    for i, video in enumerate(videos):
        video["title_lines"] = text_wrap(video["title"], max_length=25)
        if i > 0:
            video["videoURL"] = None   # only the first video is playable for now

    return render_template(
        "home.html",
        videos=videos,
        genres=fetchGenreType(),
        q=q,
        selected_genre=genre,
    )


@homePage_bp.get("/api/videos")
def list_videos():
    q, genre = readFilters()
    return jsonify(fetchVideoFiles(q, genre))


@homePage_bp.get("/api/genres")
def list_genres():
    return jsonify(fetchGenreType())