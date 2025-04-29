#all helper functions related to post, will be here
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Any
from datetime import datetime
from models.user import User
from models.post import Post, Event
from zoneinfo import ZoneInfo
from core.connection_crud import get_connections
from crud.notification import create_notification

STATUS_404_ERROR = "Post not found"

def _parse_datetime(date_str: str, time_str: str) -> datetime:
    return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

def _convert_to_utc(event_date: str, event_time: str, user_timezone: str) -> datetime:
    local_datetime = _parse_datetime(event_date, event_time)
    local_tz = ZoneInfo(user_timezone)
    return local_datetime.replace(tzinfo=local_tz).astimezone(ZoneInfo("UTC"))

def should_convert(date: Optional[str], time: Optional[str], tz: Optional[str]) -> bool:
    return all([date, time, tz])

def try_convert_datetime(date: Optional[str], time: Optional[str], tz: Optional[str], fallback: datetime) -> datetime:
    return _convert_to_utc(date, time, tz) if should_convert(date, time, tz) else fallback

def _update_field(model_instance: Any, field: str, value: Any) -> bool:
    if value is not None and getattr(model_instance, field) != value:
        setattr(model_instance, field, value)
        return True
    return False

def update_fields(fields: dict, model_instance: Any, db: Session) -> bool:
    updated = False
    for field, value in fields.items():
        updated |= _update_field(model_instance, field, value)
    if updated:
        db.commit()
        db.refresh(model_instance)
    return updated

def update_post_and_event(
    db: Session,
    post: Post,
    event: Event,
    post_data: dict,
    event_data: dict
) -> bool:
    updated = False
    updated |= update_fields(post_data, post, db)
    updated |= update_fields(event_data, event, db)
    return updated

def format_updated_event_response(post: Post, event: Event) -> dict:
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

def get_post_and_event(post_id: int, user_id: int, db: Session) -> tuple[Post, Event]:
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == user_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or not authorized")
    
    event = db.query(Event).filter(Event.post_id == post.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event details not found")
    
    return post, event


