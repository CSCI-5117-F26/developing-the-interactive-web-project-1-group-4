from operator import ge

from sqlalchemy import Boolean, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import db
import datetime
class Ti_user(db.Model):
    ti_user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    Bio: Mapped[str] = mapped_column(String(200), nullable=True)
    Profile_picture_key: Mapped[str] = mapped_column(String(200), nullable=True)
    Phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(),onupdate=func.now())
    videos = relationship("videos", back_populates="Ti_user")
    comments = relationship("Comments", back_populates="Ti_user")
    likes = relationship("Likes", back_populates="Ti_user")
class Comments(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey('comments.id',ondelete='CASCADE') ,nullable=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('ti_user.ti_user_id',ondelete='CASCADE'),  nullable=False)
    video_id: Mapped[int] = mapped_column(ForeignKey('videos.id',ondelete='CASCADE'), nullable=False)
    video = relationship("videos", back_populates="comments", cascade="all, delete-orphan")
    ti_user = relationship("Ti_user", back_populates="comments",cascade="all, delete-orphan")
    comment: Mapped[str] = mapped_column(String(10000), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(),onupdate=func.now())

class Likes(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ti_user: Mapped[int] = mapped_column(ForeignKey('ti_user.ti_user_id',ondelete='CASCADE'), nullable=False)
    video_id: Mapped[int] = mapped_column(ForeignKey('videos.id',ondelete='CASCADE'), nullable=False)
    ti_user = relationship("Ti_user", back_populates="likes",cascade="all, delete-orphan")
    video = relationship("videos",back_populates="likes",cascade="all, delete-orphan")
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(),onupdate=func.now())
class Genres(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False , unique=True)
    videos = relationship("videos",back_populates="genres")
    drafts = relationship("Drafts", back_populates="genres")
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(),onupdate=func.now())
class Languages(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    videos = relationship("videos",back_populates="language")
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(),onupdate=func.now())
class videos(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ti_user: Mapped[int] = mapped_column(ForeignKey('ti_user.ti_user_id',ondelete='CASCADE'), nullable=False)
    ti_user = relationship("Ti_user", back_populates="videos", cascade="all, delete-orphan")
    thumbnail_key: Mapped[str] = mapped_column(String(200), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(10000), nullable=True)
    video_key: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(),onupdate=func.now())
    comments = relationship("Comments", back_populates="video", cascade="all, delete-orphan")
    likes = relationship("Likes",back_populates="video")
    genres = relationship("Genres",back_populates="videos")
    language: Mapped[str] = mapped_column(ForeignKey('languages.id'), nullable=False)
    language = relationship("Language", back_populates="videos")
    Original : Mapped[Boolean] = mapped_column(Boolean, nullable=False)
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    playlists = relationship("Playlists", back_populates="videos")
class Drafts(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ti_user: Mapped[str] = mapped_column(ForeignKey('ti_user.ti_user_id'), nullable=False)
    duration: Mapped[str] = mapped_column(String(100), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=True)
    description: Mapped[str] = mapped_column(String(10000), nullable=True)
    video_key: Mapped[str] = mapped_column(String(200), nullable=False)
    thumbnail_key: Mapped[str] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(),onupdate=func.now())
    genres = relationship("Genres", back_populates="drafts")
    language: Mapped[str] = mapped_column(ForeignKey('languages.name'), nullable=True)
    Original : Mapped[str] = mapped_column(Boolean, nullable=True)

class Playlists(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ti_user: Mapped[str] = mapped_column(ForeignKey('ti_user.ti_user_id',ondelete='CASCADE'), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    videos = relationship("Videos",back_populates="playlists")
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(),onupdate=func.now())

class Subscriptions(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subscriber_id: Mapped[int] = mapped_column(ForeignKey('ti_user.ti_user_id',ondelete='CASCADE'), nullable=False)
    channel_id: Mapped[int] = mapped_column(ForeignKey('ti_user.ti_user_id',ondelete='CASCADE'), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(),onupdate=func.now())

    
