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
        videos=addTitleLines(fetchVideos(genre=genre)),
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