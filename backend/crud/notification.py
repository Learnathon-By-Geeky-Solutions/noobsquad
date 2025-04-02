from sqlalchemy.orm import Session
from models.notifications import Notification
from schemas.notification import NotificationCreate
from datetime import datetime

# Function to create a new notification
def create_notification(db: Session, recipient_id: int, actor_id: int, notif_type: str, post_id: int = None):
    new_notification = Notification(
        user_id=recipient_id,  # Receiver
        actor_id=actor_id,  # Action performer
        type=notif_type,
        post_id=post_id,
        created_at=datetime.utcnow(),
        is_read=False
    )
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    return new_notification

# Function to fetch unread notifications
def get_unread_notifications(db: Session, user_id: int):
    return db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False).all()

# Function to fetch all notifications (both read & unread)
def get_all_notifications(db: Session, user_id: int):
    return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()

# Function to mark a notification as read
def mark_notification_as_read(db: Session, notif_id: int):
    notification = db.query(Notification).filter(Notification.id == notif_id).first()
    if notification:
        notification.is_read = True
        db.commit()
        return notification
    return None
