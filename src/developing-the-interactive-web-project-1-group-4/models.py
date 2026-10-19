from operator import ge
from sqlalchemy import Boolean, ForeignKey, Integer, String, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import db
import datetime
video_genres = db.Table(
    "video_genres",
    db.Column(
        "video_id",
        Integer,
        ForeignKey("videos.id", ondelete="CASCADE"),
        primary_key=True
    ),
    db.Column(
        "genre_id",
        Integer,
        ForeignKey("genres.id", ondelete="CASCADE"),
        primary_key=True
    )
)
draft_genres = db.Table(
    "draft_genres",
    db.Column(
        "draft_id",
        Integer,
        ForeignKey("drafts.id", ondelete="CASCADE"),
        primary_key=True
    ),
    db.Column(
        "genre_id",
        Integer,
        ForeignKey("genres.id", ondelete="CASCADE"),
        primary_key=True
    )
)
playlist_videos = db.Table(
    "playlist_videos",
    db.Column(
        "playlist_id", Integer,
        ForeignKey("playlists.id", ondelete="CASCADE"),
        primary_key=True
    ),
    db.Column(
        "video_id", Integer,
        ForeignKey("videos.id", ondelete="CASCADE"),
        primary_key=True
    )
)
class Ti_user(db.Model):
    ti_user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    auth0_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    Bio: Mapped[str] = mapped_column(String(200), nullable=True)
    Profile_picture_key: Mapped[str] = mapped_column(String(200), nullable=True)
    Phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(),onupdate=func.now())
    videos = relationship("videos", back_populates="uploader", cascade="all, delete-orphan")
    comments = relationship("Comments", back_populates="ti_user", cascade="all, delete-orphan")
    likes = relationship("Likes", back_populates="liker", cascade="all, delete-orphan")
class Comments(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey('comments.id',ondelete='CASCADE') ,nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('ti_user.ti_user_id',ondelete='CASCADE'),  nullable=False)
    video_id: Mapped[int] = mapped_column(ForeignKey('videos.id',ondelete='CASCADE'), nullable=False)
    video = relationship("videos", back_populates="comments")
    ti_user = relationship("Ti_user", back_populates="comments")
    comment: Mapped[str] = mapped_column(String(10000), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(),onupdate=func.now())

class Likes(db.Model):
    __table_args__ = (
        UniqueConstraint(
            "ti_user", "video_id",
            name="uq_likes_user_video"
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ti_user: Mapped[int] = mapped_column(ForeignKey('ti_user.ti_user_id',ondelete='CASCADE'), nullable=False)
    video_id: Mapped[int] = mapped_column(ForeignKey('videos.id',ondelete='CASCADE'), nullable=False)
    liker = relationship("Ti_user", back_populates="likes")
    video = relationship("videos",back_populates="likes")
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(),onupdate=func.now())
class Genres(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False , unique=True)
    videos = relationship("videos",secondary=video_genres,back_populates="genres")
    drafts = relationship("Drafts",secondary=draft_genres, back_populates="genres")
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(),onupdate=func.now())
class videos(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ti_user: Mapped[int] = mapped_column(ForeignKey('ti_user.ti_user_id',ondelete='CASCADE'), nullable=False)
    uploader = relationship("Ti_user", back_populates="videos")
    thumbnail_key: Mapped[str] = mapped_column(String(200), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(10000), nullable=True)
    video_key: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(),onupdate=func.now())
    comments = relationship("Comments", back_populates="video", cascade="all, delete-orphan")
    likes = relationship("Likes",back_populates="video")
    genres = relationship("Genres",secondary = video_genres,back_populates="videos")
    language: Mapped[str] = mapped_column(String(100), nullable=False)
    Original : Mapped[bool] = mapped_column(Boolean, nullable=False)
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    playlists = relationship("Playlists",secondary=playlist_videos, back_populates="videos")
class Drafts(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ti_user: Mapped[int] = mapped_column(ForeignKey('ti_user.ti_user_id'), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=True)
    description: Mapped[str] = mapped_column(String(10000), nullable=True)
    video_key: Mapped[str] = mapped_column(String(200), nullable=False)
    thumbnail_key: Mapped[str] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(),onupdate=func.now())
    genres = relationship("Genres",secondary=draft_genres, back_populates="drafts")
    language: Mapped[str] = mapped_column(String(100), nullable=True)
    Original : Mapped[bool] = mapped_column(Boolean, nullable=True)

class Playlists(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ti_user: Mapped[int] = mapped_column(ForeignKey('ti_user.ti_user_id',ondelete='CASCADE'), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    videos = relationship("videos",secondary = playlist_videos,back_populates="playlists")
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(),onupdate=func.now())

class Subscriptions(db.Model):
    __table_args__ = (
        UniqueConstraint(
            "subscriber_id", "channel_id",
            name="uq_subscriptions_subscriber_channel"
        ),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subscriber_id: Mapped[int] = mapped_column(ForeignKey('ti_user.ti_user_id',ondelete='CASCADE'), nullable=False)
    channel_id: Mapped[int] = mapped_column(ForeignKey('ti_user.ti_user_id',ondelete='CASCADE'), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(),onupdate=func.now())

    
