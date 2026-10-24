from . import subscription_bp
from ..database import db
from .. import models
from ..models import *
from flask import render_template, request, jsonify, current_app, session, redirect, url_for
from ..services import *
from sqlalchemy.exc import SQLAlchemyError
from botocore.exceptions import BotoCoreError, ClientError

@subscription_bp.route("/subscribe", methods=["POST"])
def subscribe():
    user = get_current_user()

    if user is None:
        return redirect(url_for("login")),401
    user_id = user.ti_user_id

    data = request.get_json(silent=True) or {}
    channel_id = data.get("channel_id")

    if channel_id is None:
        return jsonify(error="channel_id is required."), 400

    existing = Subscriptions.query.filter_by(
        subscriber_id=user_id,
        channel_id=channel_id
    ).first()

    if existing:
        return jsonify(message="Already subscribed."), 409

    subscription = Subscriptions(
        subscriber_id=user_id,
        channel_id=channel_id
    )

    try:
        db.session.add(subscription)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify(error="Could not create subscription."), 500

    return jsonify(message="Subscribed successfully."), 201

@subscription_bp.route("/unsubscribe", methods=["POST"])
def unsubscribe():
    user = get_current_user()

    if user is None:
        return redirect(url_for("login")),401
    user_id = user.ti_user_id

    data = request.get_json(silent=True) or {}
    channel_id = data.get("channel_id")

    if channel_id is None:
        return jsonify(error="channel_id is required."), 401

    existing = Subscriptions.query.filter_by(
        subscriber_id=user_id,
        channel_id=channel_id
    ).first()

    if not existing:
        return jsonify(message="Not subscribed."), 409

    try:
        db.session.delete(existing)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify(error="Could not unsubscribe."), 500

    return jsonify(message="Unsubscribed successfully."), 200

@subscription_bp.route("/get-subscriptions", methods=["GET"])
def get_subscriptions():
    user = get_current_user()

    if user is None:
        return redirect(url_for("login")),401
    user_id = user.ti_user_id

    subscriptions = Subscriptions.query.filter_by(subscriber_id=user_id).all()
    channels = [Ti_user(ti_user_id=sub.channel_id) for sub in subscriptions]

    return jsonify(channels=[
        {
            "id": channel.ti_user_id,
            "username": channel.username,
            "profile_picture_url": (
                mediaURL(channel.profile_picture_key)
                if channel.profile_picture_key else None
            ),
        }
        for channel in channels
    ]),200

@subscription_bp.route("/get-subscribers", methods=["GET"])
def get_subscribers():
    user = get_current_user()

    if user is None:
        return redirect(url_for("login")),401
    user_id = user.ti_user_id

    subscribers = Subscriptions.query.filter_by(channel_id=user_id).all()
    subscriber_ids = [Ti_user(ti_user_id=sub.subscriber_id) for sub in subscribers]

    return jsonify(subscribers=[
            {
                "id": subscriber.ti_user_id,
                "username": subscriber.username,
                "profile_picture_url": (
                    mediaURL(subscriber.profile_picture_key)
                    if subscriber.profile_picture_key else None
                ),
            }
            for subscriber in subscriber_ids
        ]),200


# ---------- Subscriptions page (grid of artists the user follows) ----------
@subscription_bp.route("/subscriptions", methods=["GET"])
def subscriptions_page():
    if session.get("user") is None:
        return redirect(url_for("login"))
    user = get_current_user()
    if user is None:
        return redirect(url_for("profileInput.createProfile"))

    channels = (
        db.session.query(Ti_user)
        .join(Subscriptions, Subscriptions.channel_id == Ti_user.ti_user_id)
        .filter(Subscriptions.subscriber_id == user.ti_user_id)
        .order_by(Ti_user.username)
        .all()
    )

    artists = [
        {
            "username": channel.username,
            "initial": (channel.username or "?")[:1].upper(),
            "picture_url": (
                mediaURL(channel.Profile_picture_key)
                if channel.Profile_picture_key else None
            ),
            "profile_url": url_for("profilePage.profile_page", username=channel.username),
        }
        for channel in channels
    ]

    return render_template("subscriptions.html", artists=artists)