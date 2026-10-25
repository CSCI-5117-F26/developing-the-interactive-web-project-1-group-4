from flask import render_template, request, jsonify, url_for, redirect, abort

from . import homePage_bp
from ..services import (
    fetchVideos, fetchGenres, fetchArtistVideos, searchAll, text_wrap,
    SEARCH_PREVIEW_LIMIT, SEARCH_PAGE_LIMIT,
)


# ---------------- Reading the URL safely ----------------

def readQuery():
    return request.args.get("q", "").strip()[:100]


def readGenre():
    genre = request.args.get("genre", "").strip()
    valid = {g["name"] for g in fetchGenres()}
    return genre if genre in valid else ""


def addTitleLines(videos):
    for video in videos:
        video["title_lines"] = text_wrap(video["title"], max_length=25)
    return videos


# ---------------- Pages ----------------

@homePage_bp.get("/")
def home():
    genre = readGenre()
    return render_template(
        "home.html",
        videos=fetchVideos(genre=genre),
        genres=fetchGenres(),
        q="",
        selected_genre=genre,
    )


@homePage_bp.get("/search")
def search():
    q = readQuery()
    username = request.args.get("artist", "").strip()[:50]

    if username:
        artist, videos = fetchArtistVideos(username, SEARCH_PAGE_LIMIT)
        if artist is None:
            abort(404)
        results = {"videos": videos, "artists": [], "genres": []}
    elif q:
        artist = None
        results = searchAll(q, SEARCH_PAGE_LIMIT)
    else:
        return redirect(url_for("homePage.home"))

    addTitleLines(results["videos"])
    return render_template("search.html", q=q, artist=artist, **results)


@homePage_bp.get("/library")
def library():
    playlists = [
    {
        "title": "test title",
        "number of videos": "5"
    },
    {
        "title": "test title 2",
        "number of videos": "120"
    }
    ]

    saved_videos = [
    {
        "title": "testing save 1",
        "duration_text": "03:10",
        "author": "some dude",
        "thumbnail_url": "",
        "savedtime": "2 hours"
    },
    {
        "title": "testing save 2",
        "duration_text": "05:55",
        "author": "some dude",
        "thumbnail_url": "",
        "savedtime": "2 hours"
    },
    {
        "title": "testing save 3",
        "duration_text": "02:30",
        "author": "some dude",
        "thumbnail_url": "",
        "savedtime": "2 hours"
    },
    {
        "title": "testing save 4",
        "duration_text": "02:30",
        "author": "some dude",
        "thumbnail_url": "",
        "savedtime": "2 hours"
    }
    ]

    watchlater = [
    {
        "title": "testing watchlater 1",
        "duration_text": "03:10",
        "author": "some dude",
        "thumbnail": "",
        "savedtime": "2 hours"
    },
    {
        "title": "testing watchlater 2",
        "duration_text": "05:55",
        "author": "some dude",
        "thumbnail": "",
        "savedtime": "2 hours"
    },
    {
        "title": "testing watchlater 3",
        "duration_text": "02:30",
        "author": "some dude",
        "thumbnail": "",
        "savedtime": "2 hours"
    }
    ]
    return render_template(
        "library.html", playlists = playlists, saved_videos = saved_videos, watchlater = watchlater
    )


@homePage_bp.get("/activity")
def activity():
    return render_template(
        "activity.html"
    )

# ---------------- JSON endpoints ----------------

@homePage_bp.get("/api/search")
def api_search():
    q = readQuery()
    if not q:
        return jsonify(videos=[], artists=[], genres=[], viewMoreURL=None)

    results = searchAll(q, SEARCH_PREVIEW_LIMIT)
    results["viewMoreURL"] = url_for("homePage.search", q=q)
    return jsonify(results)


@homePage_bp.get("/api/videos")
def list_videos():
    return jsonify(fetchVideos(genre=readGenre()))


@homePage_bp.get("/api/genres")
def list_genres():
    return jsonify(fetchGenres())