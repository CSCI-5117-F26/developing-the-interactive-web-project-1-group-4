from .database import db
from .models import *
import subprocess

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