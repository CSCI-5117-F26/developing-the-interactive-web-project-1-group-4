from flask import Blueprint, render_template, request, jsonify

homePage_bp = Blueprint("home", __name__)

def get_int(name, default, max_value):
    try:
        value = int(request.args.get(name, default))
    except ValueError:
        value=default
    return max(0, min(value, max_value))

@homePage_bp.get("/")
def home():
    """Front End"""
    return render_template("home.html")

@homePage_bp.get("api/videos")
def listVideos():
    return

@homePage_bp.get("api/videos")
def listGenres():
    return


def fetchVideos():
    return

def fetch_genres():
    return