from uuid import uuid4
import uuid
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Union
import os
import secrets
from pathlib import Path
from datetime import datetime, timezone
from api.v1.endpoints.auth import get_current_user
from models.user import User
from models.post import Post, PostMedia, PostDocument, Event, Like, Comment
from schemas.post import PostResponse, MediaPostResponse, DocumentPostResponse, EventResponse, TextPostUpdate
from database.session import SessionLocal
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session, joinedload
import shutil
from core.connection_crud import get_connections
from crud.notification import create_notification
from AI.moderation import moderate_text

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

MEDIA_DIR = "uploads/media/"
DOCUMENT_DIR = "uploads/document/"
EVENT_UPLOAD_DIR = "uploads/event_images"
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(DOCUMENT_DIR, exist_ok=True)
os.makedirs(EVENT_UPLOAD_DIR, exist_ok=True)

STATUS_404_ERROR = "Post not found"
ALLOWED_MEDIA = {".jpg", ".jpeg", ".jfif", ".png", ".gif", ".webp", ".mp4", ".mov"}
ALLOWED_DOCS = {".pdf", ".docx", ".txt"}



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

def validate_file_extension(filename: str, allowed_extensions: set):
    ext = Path(filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file format.")
    return ext


def save_upload_file(upload_file: UploadFile, destination_dir: str, filename: str) -> str:
    file_path = os.path.join(destination_dir, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return file_path


def generate_secure_filename(user_id: int, file_ext: str) -> str:
    return f"{user_id}_{secrets.token_hex(8)}{file_ext}"


def create_post_entry(db: Session, user_id: int, content: Optional[str], post_type: str) -> Post:
    post = Post(content=content, user_id=user_id, post_type=post_type)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def send_post_notifications(db: Session, user: User, post: Post):
    friends = get_connections(db, user.id)
    for friend in friends:
        friend_id = friend["friend_id"] if friend["user_id"] == user.id else friend["user_id"]
        create_notification(db=db, recipient_id=friend_id, actor_id=user.id, notif_type="new_post", post_id=post.id)
    db.commit()

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


def remove_old_file_if_exists(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)

def try_convert_datetime(date: str, time: str, tz: str, fallback: datetime) -> datetime:
    if date and time and tz:
        return convert_to_utc(date, time, tz)
    return fallback


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



# Main function refactor
@router.get("/")
def get_posts(
    limit: int = Query(10, alias="limit"),  # Default to 10 posts
    offset: int = Query(0, alias="offset"),  # Start at 0
    last_seen_post: Optional[int] = Query(None, alias="last_seen"),  # Last post ID seen
    user_id: Optional[int] = Query(None, alias="user_id"),  # User ID to filter posts (for profile)
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ✅ Fetch posts with pagination.
    ✅ If `last_seen_post` is provided, fetch **newer** posts than the last seen post.
    ✅ Include total likes, user liked status, and comments for each post.
    """

    # ✅ Get the posts query with the optional filter for newer posts
    query = get_newer_posts(last_seen_post, db)

    if user_id:
        query = query.filter(Post.user_id == user_id)
    
    # ✅ Apply pagination
    posts = query.order_by(Post.created_at.desc()).offset(offset).limit(limit).all()

    post_list = []

    for post in posts:
        # ✅ Get like count & user like status
        user_liked = get_user_like_status(post.id, current_user.id, db)

        post_data = {
            "id": post.id,
            "post_type": post.post_type,
            "content": post.content,
            "created_at": post.created_at,
            "user": {
                "id": post.user.id,
                "username": post.user.username,
                "profile_picture": f"http://127.0.0.1:8000/uploads/profile_pictures/{post.user.profile_picture}"
            },
            "total_likes": post.like_count,
            "user_liked": user_liked
        }

        # ✅ Fetch additional data based on post_type
        post_data.update(get_post_additional_data(post, db))

        post_list.append(post_data)

    return {"posts": post_list, "count": len(post_list)}

def send_post_notifications(db: Session, user: User, post: Post):
    """Sends notifications to all friends when a user creates a post."""
    
    # ✅ Fetch connected friends
    friends = get_connections(db, user.id)

    # ✅ Create notifications for all connected friends
    for friend in friends:
        friend_id = friend["friend_id"] if friend["user_id"] == user.id else friend["user_id"]
        
        create_notification(
            db=db,
            recipient_id=friend_id,  # ✅ Friend should receive the notification
            actor_id=user.id,        # ✅ The user who created the post
            notif_type="new_post",
            post_id=post.id
        )

    db.commit()  # ✅ Commit once after all notifications are added

@router.get("/{post_id}")
def get_single_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    user_liked = get_user_like_status(post.id, current_user.id, db)

    post_data = {
        "id": post.id,
        "post_type": post.post_type,
        "content": post.content,
        "created_at": post.created_at,
        "user": {
            "id": post.user.id,
            "username": post.user.username,
            "profile_picture": f"http://127.0.0.1:8000/uploads/profile_pictures/{post.user.profile_picture}"
        },
        "total_likes": post.like_count,
        "user_liked": user_liked
    }

    post_data.update(get_post_additional_data(post, db))

    return post_data


@router.post("/create_media_post/", response_model=MediaPostResponse)
async def create_media_post(
    content: Optional[str] = Form(None),
    media_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ext = validate_file_extension(media_file.filename, ALLOWED_MEDIA)
    filename = generate_secure_filename(current_user.id, ext)
    save_upload_file(media_file, MEDIA_DIR, filename)

    post = create_post_entry(db, current_user.id, content, "media")
    media_entry = PostMedia(post_id=post.id, media_url=filename, media_type=ext)
    db.add(media_entry)
    db.commit()
    db.refresh(media_entry)

    send_post_notifications(db, current_user, post)
    return media_entry


@router.post("/create_document_post/", response_model=DocumentPostResponse)
async def create_document_post(
    content: Optional[str] = Form(None),
    document_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ext = validate_file_extension(document_file.filename, ALLOWED_DOCS)
    filename = generate_secure_filename(current_user.id, ext)
    save_upload_file(document_file, DOCUMENT_DIR, filename)

    post = create_post_entry(db, current_user.id, content, "document")
    doc_entry = PostDocument(post_id=post.id, document_url=filename, document_type=ext)
    db.add(doc_entry)
    db.commit()
    db.refresh(doc_entry)

    send_post_notifications(db, current_user, post)
    return doc_entry


@router.post("/create_text_post/", response_model=PostResponse)
async def create_text_post(
    content: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if moderate_text(content):
        raise HTTPException(status_code=400, detail="Inappropriate content detected")

    post = create_post_entry(db, current_user.id, content, "text")
    send_post_notifications(db, current_user, post)

    post.comment_count = 0
    post.user_liked = False
    return post


@router.post("/create_event_post/", response_model=EventResponse)
async def create_event_post(
    content: Optional[str] = Form(None),
    event_title: str = Form(...),
    event_description: str = Form(...),
    event_date: str = Form(...),
    event_time: str = Form(...),
    user_timezone: str = Form("Asia/Dhaka"),
    location: Optional[str] = Form(None),
    event_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        dt_local = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
        dt_utc = dt_local.replace(tzinfo=ZoneInfo(user_timezone)).astimezone(ZoneInfo("UTC"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date/time: {str(e)}")

    image_url = None
    if event_image:
        ext = validate_file_extension(event_image.filename, {".jpg", ".jpeg", ".png", ".gif", ".webp"})
        filename = generate_secure_filename(current_user.id, ext)
        save_upload_file(event_image, EVENT_UPLOAD_DIR, filename)
        image_url = f"http://127.0.0.1:8000/uploads/event_images/{filename}"

    post = create_post_entry(db, current_user.id, content, "event")
    event = Event(
        post_id=post.id,
        user_id=current_user.id,
        title=event_title,
        description=event_description,
        event_datetime=dt_utc,
        location=location,
        image_url=image_url
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    send_post_notifications(db, current_user, post)

    return event

@router.get("/posts/")
def get_posts(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Post)
    if user_id:
        query = query.filter(Post.user_id == user_id)
    return query.all()



@router.put("/update_text_post/{post_id}")
async def update_text_post(
    post_id: int,
    update_data: TextPostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = get_post_by_id(db, post_id, current_user.id)
    update_post_content(post, update_data.content)
    db.commit()
    db.refresh(post)
    return post



@router.put("/update_media_post/{post_id}")
async def update_media_post(
    post_id: int,
    content: Optional[str] = Form(None),
    media_file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = get_post_by_id(db, post_id, current_user.id)
    update_post_content(post, content)

    if media_file and media_file.filename:
        ext = validate_file_extension(media_file.filename, ALLOWED_MEDIA)
        filename = generate_secure_filename(current_user.id, ext)
        save_upload_file(media_file, MEDIA_DIR, filename)

        media_entry = db.query(PostMedia).filter(PostMedia.post_id == post.id).first()
        if media_entry:
            remove_old_file_if_exists(os.path.join(MEDIA_DIR, media_entry.media_url))
            media_entry.media_url = filename
            media_entry.media_type = ext
        else:
            media_entry = PostMedia(post_id=post.id, media_url=filename, media_type=ext)
            db.add(media_entry)

        db.commit()

    db.refresh(post)
    media_url = db.query(PostMedia).filter(PostMedia.post_id == post.id).first().media_url

    return {
        "message": "Media post updated successfully",
        "updated_post": {
            "id": post.id,
            "user_id": post.user_id,
            "content": post.content,
            "post_type": post.post_type,
            "created_at": post.created_at,
            "media_url": media_url,
        },
    }

@router.put("/update_document_post/{post_id}")
async def update_document_post(
    post_id: int,
    content: Optional[str] = Form(None),
    document_file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = get_post_by_id(db, post_id, current_user.id)
    update_post_content(post, content)

    if document_file and document_file.filename:
        ext = validate_file_extension(document_file.filename, ALLOWED_DOCS)
        filename = generate_secure_filename(current_user.id, ext)
        save_upload_file(document_file, DOCUMENT_DIR, filename)

        doc_entry = db.query(PostDocument).filter(PostDocument.post_id == post.id).first()
        if doc_entry:
            remove_old_file_if_exists(os.path.join(DOCUMENT_DIR, doc_entry.document_url))
            doc_entry.document_url = filename
            doc_entry.document_type = ext
        else:
            doc_entry = PostDocument(post_id=post.id, document_url=filename, document_type=ext)
            db.add(doc_entry)

        db.commit()

    db.refresh(post)
    document_url = db.query(PostDocument).filter(PostDocument.post_id == post.id).first().document_url

    return {
        "message": "Document post updated successfully",
        "updated_post": {
            "id": post.id,
            "user_id": post.user_id,
            "content": post.content,
            "post_type": post.post_type,
            "created_at": post.created_at,
            "document_url": document_url,
        },
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

# Helper function to convert event date and time to UTC
def convert_to_utc(event_date: str, event_time: str, user_timezone: str) -> Optional[datetime]:
    try:
        local_datetime = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
        local_tz = ZoneInfo(user_timezone)  # Correct way to use ZoneInfo
        local_dt_with_tz = local_datetime.replace(tzinfo=local_tz)  # Add timezone info
        return local_dt_with_tz.astimezone(ZoneInfo("UTC"))  # Convert to UTC
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date/time format: {str(e)}")

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

@router.put("/update_event_post/{post_id}")
async def update_event_post(
    post_id: int,
    content: Optional[str] = Form(None),
    event_title: Optional[str] = Form(None),
    event_description: Optional[str] = Form(None),
    event_date: Optional[str] = Form(None),
    event_time: Optional[str] = Form(None),
    user_timezone: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post, event = get_post_and_event(post_id, current_user.id, db)
    
    event_datetime_utc = try_convert_datetime(event_date, event_time, user_timezone, fallback=event.event_datetime)
    
    post_updated = update_post_and_event(
        db=db,
        post=post,
        event=event,
        post_data={"content": content},
        event_data={
            "title": event_title,
            "description": event_description,
            "event_datetime": event_datetime_utc,
            "location": location
        }
    )
    
    if post_updated:
        return format_updated_event_response(post, event)

    return {"message": "No changes detected"}


@router.delete("/delete_post/{post_id}")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = get_post_by_id(db, post_id, current_user.id)
    db.delete(post)
    db.commit()
    return {"message": "Post deleted successfully"}

@router.get("/events/", response_model=Union[List[EventResponse], EventResponse])
async def get_events(
    request: Request,  # We need this to access the base URL of the server
    event_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if event_id is not None:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        # # Build the full image URL if it exists
        # if event.image_url:
        #     # Replace any backslashes with forward slashes
        #     # full_image_url = f"{str(request.base_url).rstrip('/')}{event.image_url.replace('\\', '/')}"
        #     event.image_url = full_image_url

        return event
    else:
        events = db.query(Event).all()
        if not events:
            raise HTTPException(status_code=404, detail="No events found")

        # Add full image URL to each event in the list
        # for event in events:
        #     if event.image_url:
        #         # Replace any backslashes with forward slashes
        #         full_image_url = f"{str(request.base_url).rstrip('/')}{event.image_url.replace('\\', '/')}"
        #         event.image_url = full_image_url

        return events