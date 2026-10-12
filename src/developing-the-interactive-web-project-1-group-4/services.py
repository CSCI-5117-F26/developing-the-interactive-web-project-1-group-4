from .database import db
from .models import *
from .storage import r2
from uuid import uuid4
from werkzeug.utils import secure_filename
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