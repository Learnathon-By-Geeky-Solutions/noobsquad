from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.post import Like, Comment, Share, Post, Event, EventAttendee
from models.user import User
from schemas.post import PostResponse
from database.session import SessionLocal
from schemas.postReaction import LikeCreate, LikeResponse, CommentCreate, ShareResponse, CommentNestedResponse, ShareCreate
from schemas.eventAttendees import EventAttendeeCreate, EventAttendeeResponse
from api.v1.endpoints.auth import get_current_user
from datetime import datetime
import uuid  # Secure share token
from typing import List
from models.user import User
from models.post import Post, PostMedia, PostDocument, Event, Like, Comment
from zoneinfo import ZoneInfo
from crud.notification import create_notification
from schemas.notification import NotificationCreate
from services.reaction import get_like_count, add_like, remove_like, notify_if_not_self, build_comment_response
from .AttendeeHelperFunction import get_event_by_id, get_user_rsvp, update_or_create_rsvp, delete_rsvp, count_rsvp_status

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------------------
# API Routes
# ----------------------------------------

@router.post("/event/{event_id}/rsvp", response_model=EventAttendeeResponse)
def rsvp_event(
    event_id: int, 
    attendee_data: EventAttendeeCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """RSVP to an event (Going or Interested)."""
    get_event_by_id(db, event_id)  # Ensure event exists
    return update_or_create_rsvp(db, event_id, current_user.id, attendee_data.status)


@router.get("/event/{event_id}/attendees", response_model=list[EventAttendeeResponse])
def get_event_attendees(event_id: int, db: Session = Depends(get_db)):
    """Retrieve all attendees of an event."""
    return db.query(EventAttendee).filter(EventAttendee.event_id == event_id).all()


@router.delete("/event/{event_id}/rsvp")
def remove_rsvp(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Remove the current user's RSVP from an event."""
    delete_rsvp(db, event_id, current_user.id)
    return {"message": "RSVP removed successfully"}


@router.get("/event/{event_id}/my_rsvp/")
def get_user_rsvp_status(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get the current user's RSVP status for an event."""
    rsvp = get_user_rsvp(db, event_id, current_user.id)
    return {"status": rsvp.status if rsvp else None}


@router.get("/posts/events/rsvp/counts/")
def get_rsvp_counts(event_id: int = Query(...), db: Session = Depends(get_db)):
    """Get RSVP counts (Going/Interested) for an event."""
    return {
        "going": count_rsvp_status(db, event_id, "going"),
        "interested": count_rsvp_status(db, event_id, "interested")
    }
