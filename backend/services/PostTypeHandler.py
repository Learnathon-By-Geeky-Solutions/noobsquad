#all helper functions related to post, will be here
from sqlalchemy.orm import Session
from models.post import Post, PostMedia, PostDocument, Event
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
from typing import Any, Dict

# Load environment variables
load_dotenv()

# Using the URL from tests or falling back to the environment variable
API_URL = os.getenv("VITE_API_URL")

STATUS_404_ERROR = "Post not found"

def _get_media_post_data(post: Post, db: Session) -> Dict[str, Any]:
    media = db.query(PostMedia).filter(PostMedia.post_id == post.id).first()
    return {
        "media_url": media.media_url if media else None
    }

def _get_document_post_data(post: Post, db: Session) -> Dict[str, Any]:
    document = db.query(PostDocument).filter(PostDocument.post_id == post.id).first()
    return {
        "document_url": f"{API_URL}/uploads/document/{document.document_url}" if document else None
    }

def _get_event_post_data(post: Post, db: Session) -> Dict[str, Any]:
    event = db.query(Event).filter(Event.post_id == post.id).first()
    if not event:
        return {}
    return {
        "event": {
            "title": event.title,
            "description": event.description,
            "event_datetime": event.event_datetime,
            "location": event.location
        }
    }

def get_post_additional_data(post: Post, db: Session) -> Dict[str, Any]:
    """Get additional data based on the post type (media, document, event)."""
    handlers = {
        "media": _get_media_post_data,
        "document": _get_document_post_data,
        "event": _get_event_post_data,
    }
    handler = handlers.get(post.post_type)
    return handler(post, db) if handler else {}
