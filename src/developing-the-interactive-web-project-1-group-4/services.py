from .database import db
from .models import *
import subprocess
from .storage import r2
from uuid import uuid4
from werkzeug.utils import secure_filename
from flask import request
import os
from dotenv import load_dotenv
load_dotenv()
def create_dummy_user(username: str, email: str, first_name: str, last_name: str):
    user = Ti_user(username=username, email=email, first_name=first_name, last_name=last_name)
    db.session.add(user)
    db.session.commit()
    return user

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
    db.session.add(video)
    db.session.commit()


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

    duration = float(result.stdout.strip())
    return duration