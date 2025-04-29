#all helper functions related to post, will be here
from typing import List, Optional
from sqlalchemy.orm import Session
from models.user import User
from models.post import Post
from models.notifications import Notification
from core.connection_crud import get_connections

STATUS_404_ERROR = "Post not found"

def create_notification(
    db: Session,
    user_id: int,
    actor_id: int,
    type: str,
    post_id: Optional[int] = None
) -> Notification:
    """Create a new notification."""
    notification = Notification(
        user_id=user_id,
        actor_id=actor_id,
        type=type,
        post_id=post_id,
        is_read=False
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification

def send_post_notifications(
    db: Session,
    author: User,
    post: Post,
    notification_type: str = "new_post"
) -> List[Notification]:
    """Send notifications to all connections when a user creates a new post."""
    notifications = []
    connections = get_connections(db, author.id)
    
    for connection in connections:
        # Determine the recipient
        recipient_id = connection["friend_id"] if connection["user_id"] == author.id else connection["user_id"]
        
        # Create and store notification
        notification = create_notification(
            db=db,
            user_id=recipient_id,
            actor_id=author.id,
            type=notification_type,
            post_id=post.id
        )
        notifications.append(notification)
    
    return notifications

def mark_notification_as_read(
    db: Session,
    notification_id: int,
    user_id: int
) -> Optional[Notification]:
    """Mark a notification as read if it belongs to the user."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    
    if notification and not notification.is_read:
        notification.is_read = True
        db.commit()
        db.refresh(notification)
    
    return notification

def get_user_notifications(
    db: Session,
    user_id: int,
    limit: int = 10,
    offset: int = 0,
    unread_only: bool = False
) -> List[Notification]:
    """Get user notifications with pagination and optional filtering."""
    query = db.query(Notification).filter(Notification.user_id == user_id)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    return query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()

def get_unread_notification_count(
    db: Session,
    user_id: int
) -> int:
    """Get the count of unread notifications for a user."""
    return db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).count()

def clear_all_notifications(
    db: Session,
    user_id: int
) -> int:
    """Mark all notifications as read for a user."""
    result = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    return result

