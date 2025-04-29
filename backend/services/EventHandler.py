from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo
from models.post import Post, Event
from utils.post_utils import create_base_post
from services.FileHandler import save_upload_file, generate_secure_filename

def parse_event_datetime(
    event_date: str,
    event_time: str,
    user_timezone: str = "UTC"
) -> datetime:
    """Parse and convert event datetime to UTC."""
    try:
        local_datetime = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
        local_tz = ZoneInfo(user_timezone)
        return local_datetime.replace(tzinfo=local_tz).astimezone(ZoneInfo("UTC"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing datetime: {str(e)}")

def create_event_post(
    db: Session,
    user_id: int,
    content: Optional[str],
    event_data: Dict[str, Any],
    event_image: Optional[UploadFile] = None,
    upload_dir: str = "uploads/event_images"
) -> Tuple[Post, Event]:
    """Create a new event post with associated event details."""
    # Create base post
    post = create_base_post(db, user_id, content, "event")
    
    # Handle event image if provided
    image_filename = None
    if event_image:
        image_filename = generate_secure_filename(user_id, ".jpg")  # Assuming jpg for simplicity
        save_upload_file(event_image, upload_dir, image_filename)
    
    # Parse event datetime
    event_datetime = parse_event_datetime(
        event_data["event_date"],
        event_data["event_time"],
        event_data.get("user_timezone", "UTC")
    )
    
    # Create event
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

def update_event_post(
    db: Session,
    post: Post,
    event: Event,
    update_data: Dict[str, Any]
) -> Tuple[Post, Event]:
    """Update an existing event post and its details."""
    # Update post content if provided
    if "content" in update_data and update_data["content"] is not None:
        post.content = update_data["content"]
    
    # Update event fields if provided
    event_fields = {
        "title": "event_title",
        "description": "event_description",
        "location": "location"
    }
    
    for model_field, data_field in event_fields.items():
        if data_field in update_data and update_data[data_field] is not None:
            setattr(event, model_field, update_data[data_field])
    
    # Update event datetime if both date and time are provided
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