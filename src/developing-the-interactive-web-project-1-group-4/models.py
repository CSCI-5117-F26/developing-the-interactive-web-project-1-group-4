from sqlalchemy import Boolean, ForeignKey, Integer, String, Array
from sqlalchemy.orm import Mapped, mapped_column
from .database import db
class User(db.Model):
    username: Mapped[str] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[str] = mapped_column(String(100), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(100), nullable=False)
    Bio: Mapped[str] = mapped_column(String(200), nullable=True)
    Profile_picture: Mapped[str] = mapped_column(String(200), nullable=True)
    Phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
class Comments(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(ForeignKey('user.username'), nullable=False)
    video_id: Mapped[int] = mapped_column(ForeignKey('videos.id'), nullable=False)
    comment: Mapped[str] = mapped_column(String(10000), nullable=False)
    created_at: Mapped[str] = mapped_column(String(100), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(100), nullable=False)

class Likes(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(ForeignKey('user.username'), nullable=False)
    video_id: Mapped[int] = mapped_column(ForeignKey('published_videos.id'), nullable=False)
    created_at: Mapped[str] = mapped_column(String(100), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(100), nullable=False)
class Genres(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    videos: Mapped[str] = mapped_column(Array[ForeignKey('videos.id')], nullable=True)
class Languages(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    videos: Mapped[str] = mapped_column(Array[ForeignKey('videos.id')], nullable=True)
class videos(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(ForeignKey('user.username'), nullable=False)
    duration: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(10000), nullable=True)
    video_url: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[str] = mapped_column(String(100), nullable=False)
    posted_at: Mapped[str] = mapped_column(String(100), nullable=False)
    comments: Mapped[str] = mapped_column(Array[ForeignKey('comments.id')], nullable=True)
    likes: Mapped[str] = mapped_column(Array[ForeignKey('likes.id')], nullable=True)
    genres: Mapped[str] = mapped_column(Array[ForeignKey('genres.id')], nullable=False)
    language: Mapped[str] = mapped_column(ForeignKey('languages.name'), nullable=False)
    Original : Mapped[str] = mapped_column(Boolean, nullable=False)
    views: Mapped[int] = mapped_column(Integer, nullable=False)
    likes_count: Mapped[int] = mapped_column(Integer, nullable=False)
    comments_count: Mapped[int] = mapped_column(Integer, nullable=False)
    Draft: Mapped[str] = mapped_column(Boolean, nullable=True)

class Playlists(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(ForeignKey('user.username'), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    videos: Mapped[str] = mapped_column(Array[ForeignKey('videos.id')], nullable=True)
    created_at: Mapped[str] = mapped_column(String(100), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(100), nullable=False)

    
