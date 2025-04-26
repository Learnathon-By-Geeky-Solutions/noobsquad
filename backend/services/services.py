#all helper functions related to post, will be here
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from models.user import User
from models.post import Post, Event
from zoneinfo import ZoneInfo
from core.connection_crud import get_connections
from crud.notification import create_notification

STATUS_404_ERROR = "Post not found"

# Event part

def should_convert(date, time, tz):
    return all([date, time, tz])

def try_convert_datetime(date, time, tz, fallback):
    return convert_to_utc(date, time, tz) if should_convert(date, time, tz) else fallback

def update_post_and_event(
    db: Session,
    post,
    event,
    post_data: dict,
    event_data: dict
) -> bool:
    updated = False
    updated |= update_fields(post_data, post, db)
    updated |= update_fields(event_data, event, db)
    return updated


def format_updated_event_response(post, event):
    return {
        "message": "Event post updated successfully",
        "updated_post": {
            "id": post.id,
            "content": post.content,
            "title": event.title,
            "description": event.description,
            "event_datetime": event.event_datetime,
            "location": event.location
        }
    }


# Helper function to get post and associated event
def get_post_and_event(post_id: int, user_id: int, db: Session):
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == user_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or not authorized")
    
    event = db.query(Event).filter(Event.post_id == post.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event details not found")
    
    return post, event

def parse_datetime(date_str, time_str):
    return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

def convert_to_utc(event_date, event_time, user_timezone):
    local_datetime = parse_datetime(event_date, event_time)
    local_tz = ZoneInfo(user_timezone)
    return local_datetime.replace(tzinfo=local_tz).astimezone(ZoneInfo("UTC"))


# Helper function to update post and event fields
def update_fields(fields, model_instance, db: Session) -> bool:
    updated = False
    for field, value in fields.items():
        if value is not None and getattr(model_instance, field) != value:
            setattr(model_instance, field, value)
            updated = True
    if updated:
        db.commit()
        db.refresh(model_instance)
    return updated


