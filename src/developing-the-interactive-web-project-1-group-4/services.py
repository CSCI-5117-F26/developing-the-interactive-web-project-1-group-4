from .database import db
from .models import *
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
