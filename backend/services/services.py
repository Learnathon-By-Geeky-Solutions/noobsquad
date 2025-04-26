
from fastapi import  HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from models.post import Post, PostMedia, PostDocument, Event, Like, Comment
from sqlalchemy.orm import Session

STATUS_404_ERROR = "Post not found"

# Helper function to get the latest post after the provided `last_seen_post`
def get_newer_posts(last_seen_post: Optional[int], db: Session):
    if last_seen_post:
        latest_post = db.query(Post).filter(Post.id == last_seen_post).first()
        if latest_post:
            return db.query(Post).filter(Post.created_at > latest_post.created_at)
    return db.query(Post)

# Helper function to get the like status of a user for a post
def get_user_like_status(post_id: int, user_id: int, db: Session):
    return db.query(Like).filter(Like.post_id == post_id, Like.user_id == user_id).first() is not None

# Helper function to get comments for a post
def get_comments_for_post(post_id: int, db: Session):
    return db.query(Comment).filter(Comment.post_id == post_id).all()

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


def create_post_entry(db: Session, user_id: int, content: Optional[str], post_type: str) -> Post:
    post = Post(content=content, user_id=user_id, post_type=post_type)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def get_post_by_id(db: Session, post_id: int, user_id: int = None):
    query = db.query(Post).filter(Post.id == post_id)
    if user_id is not None:
        query = query.filter(Post.user_id == user_id)
    post = query.first()
    if not post:
        raise HTTPException(status_code=404, detail=STATUS_404_ERROR)
    return post


def update_post_content(post: Post, content: Optional[str]):
    if content is not None:
        post.content = content


