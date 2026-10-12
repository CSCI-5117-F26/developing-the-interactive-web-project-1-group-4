from flask import Blueprint, render_template, request, jsonify
from . import homePage_bp

def get_int(name, default, max_value):
    try:
        value = int(request.args.get(name, default))
    except ValueError:
        value=default
    return max(0, min(value, max_value))

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

@homePage_bp.get("/")
def home():
    """Front End"""
    videos = [
    {"cover": "", "title": "It's My Life"},
    {"cover": "", "title": "Testing long long longgg title"},
    {"cover": "", "title": "It's My Life"},
    {"cover": "", "title": "It's My Life"},
    {"cover": "", "title": "It's My Life"},
    {"cover": "", "title": "It's My Life"},
    ]

    genres = [
    {"name": "Pop"},
    {"name": "Rock"},
    {"name": "Country"},
    {"name": "Rap"},
    {"name": "RnB"},
    {"name": "Punk"},
    ]

    for video in videos:
        video["title_lines"] = text_wrap(video["title"], max_length = 25)

    return render_template("home.html", videos = videos, genres = genres)

@homePage_bp.get("/api/videos")
def listVideos():
    return

@homePage_bp.get("/api/videos")
def listGenres():
    return


def fetchVideos():
    return

def fetch_genres():
    return