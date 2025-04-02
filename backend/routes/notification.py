from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from crud.notification import create_notification, get_unread_notifications, get_all_notifications, mark_notification_as_read
from schemas.notification import NotificationResponse
from database.session import SessionLocal


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Get unread notifications for a user
@router.get("/unread", response_model=list[NotificationResponse])
def fetch_unread_notifications(user_id: int, db: Session = Depends(get_db)):
    return get_unread_notifications(db, user_id)

# Get all notifications for a user
@router.get("/", response_model=list[NotificationResponse])
def fetch_all_notifications(user_id: int, db: Session = Depends(get_db)):
    return get_all_notifications(db, user_id)

# Mark a notification as read
@router.put("/{notif_id}/read", response_model=NotificationResponse)
def read_notification(notif_id: int, db: Session = Depends(get_db)):
    notification = mark_notification_as_read(db, notif_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification
