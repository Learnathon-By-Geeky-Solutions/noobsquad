from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.session import SessionLocal
from api.v1.endpoints.auth import get_current_user
from models.user import User
from models.notifications import Notification
from services.NotificationHandler import (
    get_user_notifications,
    mark_notification_as_read,
    get_unread_notification_count,
    clear_all_notifications
)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[dict])
async def get_notifications(
    limit: int = Query(10, description="Number of notifications to return"),
    offset: int = Query(0, description="Number of notifications to skip"),
    unread_only: bool = Query(False, description="Only return unread notifications"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user notifications with pagination and optional filtering."""
    notifications = get_user_notifications(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        unread_only=unread_only
    )
    
    return [notification.__dict__ for notification in notifications]

@router.post("/{notification_id}/read")
async def read_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read."""
    notification = mark_notification_as_read(db, notification_id, current_user.id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read"}

@router.get("/unread/count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the count of unread notifications."""
    count = get_unread_notification_count(db, current_user.id)
    return {"unread_count": count}

@router.post("/clear-all")
async def clear_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read."""
    updated_count = clear_all_notifications(db, current_user.id)
    return {
        "message": "All notifications marked as read",
        "updated_count": updated_count
    }
