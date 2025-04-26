#all helper functions related to post, will be here
from sqlalchemy.orm import Session
from models.post import Post, PostMedia, PostDocument, Event
from sqlalchemy.orm import Session

STATUS_404_ERROR = "Post not found"

# Helper function to get additional data based on the post type (media, document, event)
def get_post_additional_data(post: Post, db: Session):
    handlers = {
        "media": get_media_post_data,
        "document": get_document_post_data,
        "event": get_event_post_data,
    }
    handler = handlers.get(post.post_type)
    return handler(post, db) if handler else {}
    

def get_media_post_data(post: Post, db: Session):
    media = db.query(PostMedia).filter(PostMedia.post_id == post.id).first()
    return {
        "media_url": f"http://127.0.0.1:8000/uploads/media/{media.media_url}" if media else None
    }

def get_document_post_data(post: Post, db: Session):
    document = db.query(PostDocument).filter(PostDocument.post_id == post.id).first()
    return {
        "document_url": f"http://127.0.0.1:8000/uploads/document/{document.document_url}" if document else None
    }

def get_event_post_data(post: Post, db: Session):
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
