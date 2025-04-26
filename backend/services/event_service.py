from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.post import Post, Event
from typing import Optional, Tuple

# Helper function to get post and associated event
def get_post_and_event(post_id: int, user_id: int, db: Session):
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == user_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or not authorized")
    
    event = db.query(Event).filter(Event.post_id == post.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event details not found")
    
    return post, event

# Helper function to convert event date and time to UTC
def convert_to_utc(event_date: str, event_time: str, user_timezone: str) -> Optional[datetime]:
    try:
        local_datetime = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
        local_tz = ZoneInfo(user_timezone)  # Correct way to use ZoneInfo
        local_dt_with_tz = local_datetime.replace(tzinfo=local_tz)  # Add timezone info
        return local_dt_with_tz.astimezone(ZoneInfo("UTC"))  # Convert to UTC
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date/time format: {str(e)}")


def try_convert_datetime(date: str, time: str, tz: str, fallback: datetime) -> datetime:
    if date and time and tz:
        return convert_to_utc(date, time, tz)
    return fallback

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
