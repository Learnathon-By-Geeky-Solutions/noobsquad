from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo
from models.post import Post, Event
from utils.post_utils import create_base_post
from services.FileHandler import save_upload_file, generate_secure_filename

def _parse_datetime_string(date_str: str, time_str: str) -> datetime:
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {str(e)}")

def _convert_to_utc(local_datetime: datetime, user_timezone: str) -> datetime:
    try:
        local_tz = ZoneInfo(user_timezone)
        return local_datetime.replace(tzinfo=local_tz).astimezone(ZoneInfo("UTC"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing datetime: {str(e)}")

def parse_event_datetime(
    event_date: str,
    event_time: str,
    user_timezone: str = "UTC"
) -> datetime:
    """Parse and convert event datetime to UTC."""
    local_datetime = _parse_datetime_string(event_date, event_time)
    return _convert_to_utc(local_datetime, user_timezone)

def _handle_event_image(
    event_image: Optional[UploadFile],
    user_id: int,
    upload_dir: str
) -> Optional[str]:
    if not event_image:
        return None
    
    image_filename = generate_secure_filename(user_id, ".jpg")
    save_upload_file(event_image, upload_dir, image_filename)
    return image_filename

def create_event_post(
    db: Session,
    user_id: int,
    content: Optional[str],
    event_data: Dict[str, Any],
    event_image: Optional[UploadFile] = None,
    upload_dir: str = "uploads/event_images"
) -> Tuple[Post, Event]:
    """Create a new event post with associated event details."""
    post = create_base_post(db, user_id, content, "event")
    image_filename = _handle_event_image(event_image, user_id, upload_dir)
    
    event_datetime = parse_event_datetime(
        event_data["event_date"],
        event_data["event_time"],
        event_data.get("user_timezone", "UTC")
    )
    
    event = Event(
        post_id=post.id,
        title=event_data["event_title"],
        description=event_data["event_description"],
        event_datetime=event_datetime,
        location=event_data.get("location"),
        image_url=image_filename
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return post, event

def _update_post_content(post: Post, content: Optional[str]) -> None:
    if content is not None:
        post.content = content

def _update_event_fields(event: Event, update_data: Dict[str, Any]) -> None:
    event_fields = {
        "title": "event_title",
        "description": "event_description",
        "location": "location"
    }
    
    for model_field, data_field in event_fields.items():
        if data_field in update_data and update_data[data_field] is not None:
            setattr(event, model_field, update_data[data_field])

def update_event_post(
    db: Session,
    post: Post,
    event: Event,
    update_data: Dict[str, Any]
) -> Tuple[Post, Event]:
    """Update an existing event post and its details."""
    _update_post_content(post, update_data.get("content"))
    _update_event_fields(event, update_data)
    
    if all(key in update_data for key in ["event_date", "event_time"]):
        event_datetime = parse_event_datetime(
            update_data["event_date"],
            update_data["event_time"],
            update_data.get("user_timezone", "UTC")
        )
        event.event_datetime = event_datetime
    
    db.commit()
    db.refresh(post)
    db.refresh(event)
    
    return post, event

def format_event_response(post: Post, event: Event) -> Dict[str, Any]:
    """Format event post response."""
    return {
        "id": post.id,
        "content": post.content,
        "title": event.title,
        "description": event.description,
        "event_datetime": event.event_datetime,
        "location": event.location,
        "image_url": event.image_url
    } 