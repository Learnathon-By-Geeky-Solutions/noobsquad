from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from models.notifications import Notification
from schemas.notification import NotificationCreate
from datetime import datetime, timezone
from models.user import User
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

API_URL = os.getenv("VITE_API_URL")
# Function to create a new notification
def create_notification(db: Session, recipient_id: int, actor_id: int, notif_type: str, post_id: int = None):
    new_notification = Notification(
        user_id=recipient_id,  # Receiver
        actor_id=actor_id,  # Action performer
        type=notif_type,
        post_id=post_id,
        created_at=datetime.now(timezone.utc),
        is_read=False
    )
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    return new_notification

# Function to fetch unread notifications
def get_unread_notifications(db: Session, user_id: int):
    notifications = (db.query(Notification).join(User, Notification.actor_id == User.id).filter(Notification.user_id == user_id, Notification.is_read == False).all())
    return [
        {
            "id": n.id,
            "type": n.type,
            "is_read": n.is_read,
            "post_id": n.post_id,
            "actor_id": n.actor_id,
            "actor_username": n.actor.username,
            "created_at": n.created_at,
            "user_id": n.user_id,  # Add this field
            "actor_image_url": f"{API_URL}/uploads/profile_pictures/{n.actor.profile_picture}"
        }

        for n in notifications
    ]

# Function to fetch all notifications (both read & unread)
def get_all_notifications(db: Session, user_id: int):
    notifications= (db.query(Notification).join(User, Notification.actor_id == User.id).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all())
    return [
        {
            "id": n.id,
            "type": n.type,
            "is_read": n.is_read,
            "post_id": n.post_id,
            "actor_id": n.actor_id,
            "actor_username": n.actor.username,
            "created_at": n.created_at,
            "user_id": n.user_id,  # Add this field
            "actor_image_url": f"{API_URL}/uploads/profile_pictures/{n.actor.profile_picture}"

        }
        for n in notifications
    ]

# Function to mark a notification as read
def mark_notification_as_read(db: Session, notif_id: int):
    notification = (
        db.query(Notification)
        .join(User, Notification.actor_id == User.id)
        .filter(Notification.id == notif_id)
        .first()
    )
    if notification:
        notification.is_read = True
        db.commit()
        return {
            "id": notification.id,
            "type": notification.type,
            "is_read": notification.is_read,
            "post_id": notification.post_id,
            "actor_id": notification.actor_id,
            "actor_username": notification.actor.username,
            "created_at": notification.created_at,
            "user_id": notification.user_id,  # Add this field
            "actor_image_url": f"{API_URL}/uploads/profile_pictures/{notification.actor.profile_picture}"

        }
    return None

