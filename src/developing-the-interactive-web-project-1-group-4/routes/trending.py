from flask import render_template, jsonify, abort

from . import trending_bp
from ..services import (
    fetchTrendingVideos, fetchGenreCards, fetchTrendingArtists,
    getGenre, fetchGenreVideos,get_current_user
)


# ---------------- Pages ----------------

@trending_bp.get("/trending")
def trending():
    user = get_current_user()
    return render_template(
        "trending.html",
        q="",
        trendingVideos=fetchTrendingVideos(),
        genres=fetchGenreCards(),
        artists=fetchTrendingArtists(),
        playlists=user.playlists if user else [],
    )


@trending_bp.get("/genre/<genreName>")
def genrePage(genreName):
    genre = getGenre(genreName)
    if genre is None:
        abort(404)
    user = get_current_user()
    return render_template(
        "genre.html",
        q="",
        genreName=genre.name,
        videos=fetchGenreVideos(genre.name),
        playlists=user.playlists if user else [],
    )


# ---------------- JSON (for later frontend use) ----------------

@trending_bp.get("/api/trending")
def apiTrending():
    return jsonify(
        trendingVideos=fetchTrendingVideos(),
        genres=fetchGenreCards(),
        artists=fetchTrendingArtists(),
    )


@trending_bp.get("/api/genres/<genreName>/videos")
def apiGenreVideos(genreName):
    if getGenre(genreName) is None:
        return jsonify(error="Genre not found."), 404
    return jsonify(fetchGenreVideos(genreName))