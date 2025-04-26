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
# ----------------------------------------
# Helper Functions
# ----------------------------------------

def get_event_by_id(db: Session, event_id: int) -> Event:
    """Fetch an event by ID or raise 404."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")
    return event

def get_user_rsvp(db: Session, event_id: int, user_id: int) -> EventAttendee:
    """Fetch the RSVP status of a user for an event."""
    return db.query(EventAttendee).filter(
        EventAttendee.event_id == event_id,
        EventAttendee.user_id == user_id
    ).first()

def update_or_create_rsvp(db: Session, event_id: int, user_id: int, status: str) -> EventAttendee:
    """Update an existing RSVP or create a new one."""
    rsvp = get_user_rsvp(db, event_id, user_id)
    if rsvp:
        rsvp.status = status
    else:
        rsvp = EventAttendee(event_id=event_id, user_id=user_id, status=status)
        db.add(rsvp)
    db.commit()
    return rsvp

def delete_rsvp(db: Session, event_id: int, user_id: int):
    """Remove a user's RSVP from an event."""
    rsvp = get_user_rsvp(db, event_id, user_id)
    if not rsvp:
        raise HTTPException(status_code=404, detail="You haven't RSVP'd for this event.")
    
    db.delete(rsvp)
    db.commit()

def count_rsvp_status(db: Session, event_id: int, status: str) -> int:
    """Count users for a given RSVP status (going/interested)."""
    return db.query(func.count()).filter(
        EventAttendee.event_id == event_id,
        EventAttendee.status == status
    ).scalar()