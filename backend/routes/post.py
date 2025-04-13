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
os.makedirs(MEDIA_DIR, exist_ok=True)  # Ensure upload directory exists
DOCUMENT_DIR = "uploads/document/"
os.makedirs(DOCUMENT_DIR, exist_ok=True) 
STATUS_404_ERROR= "Post not found"




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
    post_data = {}

    if post.post_type == "media":
        media = db.query(PostMedia).filter(PostMedia.post_id == post.id).first()
        post_data["media_url"] = f"http://127.0.0.1:8000/uploads/media/{media.media_url}" if media else None
    elif post.post_type == "document":
        document = db.query(PostDocument).filter(PostDocument.post_id == post.id).first()
        post_data["document_url"] = f"http://127.0.0.1:8000/uploads/document/{document.document_url}" if document else None
    elif post.post_type == "event":
        event = db.query(Event).filter(Event.post_id == post.id).first()
        if event:
            post_data["event"] = {
                "title": event.title,
                "description": event.description,
                "event_datetime": event.event_datetime,
                "location": event.location
            }

    return post_data

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


@router.post("/create_text_post/", response_model=PostResponse)
async def create_text_post(
    content: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if the content is inappropriate using the AI-based moderation function
    if moderate_text(content):
        raise HTTPException(status_code=400, detail="Inappropriate content detected, Please revise your content")
    
    new_post = Post(content=content, user_id=current_user.id, post_type="text")
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    send_post_notifications(db, current_user, new_post)

    # Add required fields dynamically
    new_post.comment_count = 0
    new_post.user_liked = False
    return new_post  # Returns as PostResponse schema


@router.post("/create_media_post/", response_model=MediaPostResponse)
async def create_media_post(
    content: Optional[str] = Form(None),
    media_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not media_file:
        raise HTTPException(status_code=400, detail="No media file received")  # ✅ Debugging

    allowed_media = {".jpg", ".jpeg", ".jfif", ".png", ".gif", ".webp", ".mp4", ".mov"}
    media_ext = Path(media_file.filename).suffix.lower()
    if media_ext not in allowed_media:
        raise HTTPException(status_code=400, detail="Invalid media format.")
    

    # Save media to local storage
    media_filename = f"{current_user.id}_{secrets.token_hex(8)}{media_ext}"
    media_path = os.path.join(MEDIA_DIR, media_filename)
    with open(media_path, "wb") as buffer:
        shutil.copyfileobj(media_file.file, buffer)

    # Create Post Entry
    new_post = Post(content=content, user_id=current_user.id, post_type="media")
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    # Add Media Entry
    new_media = PostMedia(post_id=new_post.id, media_url=media_filename, media_type=media_ext)
    db.add(new_media)
    db.commit()
    db.refresh(new_media)
    send_post_notifications(db, current_user, new_post)

    return new_media  # Returns as MediaPostResponse schema



@router.post("/create_document_post/", response_model=DocumentPostResponse)
async def create_document_post(
    content: Optional[str] = Form(None),
    document_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    allowed_docs = {".pdf", ".docx", ".txt"}
    doc_ext = Path(document_file.filename).suffix.lower()
    if doc_ext not in allowed_docs:
        raise HTTPException(status_code=400, detail="Invalid document format.")

    # Save document to local storage
    doc_filename = f"{current_user.id}_{secrets.token_hex(8)}{doc_ext}"
    document_path = os.path.join(DOCUMENT_DIR, doc_filename)
    with open(document_path, "wb") as buffer:
        buffer.write(document_file.file.read())

    # Create Post Entry
    new_post = Post(content=content, user_id=current_user.id, post_type="document")
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    # Add Document Entry
    new_document = PostDocument(post_id=new_post.id, document_url=doc_filename, document_type=doc_ext)
    db.add(new_document)
    db.commit()
    db.refresh(new_document)
    send_post_notifications(db, current_user, new_post)



    return new_document  # Returns as DocumentPostResponse schema

# Define upload directory as a constant
EVENT_UPLOAD_DIR = "uploads/event_images"
os.makedirs(EVENT_UPLOAD_DIR, exist_ok=True)

@router.post("/create_event_post/", response_model=EventResponse)
async def create_event_post(
    content: Optional[str] = Form(None),
    event_title: str = Form(...),
    event_description: str = Form(...),
    event_date: str = Form(...),   # Accepts date in "YYYY-MM-DD"
    event_time: str = Form(...),   # Accepts time in "HH:MM"
    user_timezone: str = Form("Asia/Dhaka"),  # User’s timezone (e.g., "Asia/Dhaka")
    location: Optional[str] = Form(None),
    event_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Combine Date & Time
        local_datetime = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")

        # Convert to UTC
        local_tz = ZoneInfo(user_timezone)
        local_dt_with_tz = local_datetime.replace(tzinfo=local_tz)
        event_datetime_utc = local_dt_with_tz.astimezone(ZoneInfo("UTC"))

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date/time format: {str(e)}")

    # Handle image upload securely
    image_url = None
    if event_image:
        try:
            # Validate file extension
            ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
            file_extension = Path(event_image.filename).suffix.lower()
            if file_extension not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file type"
                )

            # Generate a secure filename
            secure_filename = f"{current_user.id}_{secrets.token_hex(8)}{file_extension}"
            file_location = os.path.abspath(os.path.join(EVENT_UPLOAD_DIR, secure_filename))

            # Prevent directory traversal
            if not file_location.startswith(os.path.abspath(EVENT_UPLOAD_DIR)):
                raise HTTPException(status_code=400, detail="Invalid file path detected.")

            # Save the uploaded image to the server
            with open(file_location, "wb") as buffer:
                buffer.write(event_image.file.read())

            # Construct the image URL using the mounted static path
            image_url = f"http://127.0.0.1:8000/uploads/event_images/{secure_filename}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")

    # Create Post Entry
    new_post = Post(content=content, user_id=current_user.id, post_type="event")
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    # Add Event Entry with UTC time
    new_event = Event(
        post_id=new_post.id,
        user_id=current_user.id,
        title=event_title,
        description=event_description,
        event_datetime=event_datetime_utc,
        location=location,
        image_url=image_url
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    # Notify users about the new event
    send_post_notifications(db, current_user, new_post)

    return new_event

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
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == current_user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail=STATUS_404_ERROR)

    if update_data.content is not None:
        post.content = update_data.content

    db.commit()
    db.refresh(post)
    return post


@router.put("/update_media_post/{post_id}")
async def update_media_post(
    post_id: int,
    content: Optional[str] = Form(None),  
    media_file: Optional[UploadFile] = File(None),  # ✅ Optional to allow skipping media update
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Find the post
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == current_user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail=STATUS_404_ERROR)
    
    # ✅ Only update content if it's provided
    if content is not None:
        post.content = content  

    # ✅ If a new media file is uploaded, replace the old one
    if media_file and media_file.filename:  
        allowed_media = {".jpg", ".jpeg", ".jfif", ".png", ".gif", ".webp", ".mp4", ".mov"}
        media_ext = Path(media_file.filename).suffix.lower()
        if media_ext not in allowed_media:
            raise HTTPException(status_code=400, detail="Invalid media format.")

        media_filename = f"{current_user.id}_{secrets.token_hex(8)}{media_ext}"
        media_path = os.path.join(MEDIA_DIR, media_filename)

        # ✅ Save the new file safely
        with open(media_path, "wb") as buffer:
            shutil.copyfileobj(media_file.file, buffer)

        # ✅ Find existing media
        media_entry = db.query(PostMedia).filter(PostMedia.post_id == post.id).first()
        if media_entry:
            # ✅ Remove old file safely
            old_media_path = os.path.join(MEDIA_DIR, media_entry.media_url)
            if os.path.exists(old_media_path):
                os.remove(old_media_path)

            # ✅ Update media entry
            media_entry.media_url = media_filename  
            media_entry.media_type = media_ext
            db.commit()  # ✅ Save changes
        else:
            new_media = PostMedia(post_id=post.id, media_url=media_filename, media_type=media_ext)
            db.add(new_media)
            db.commit()  # ✅ Save changes

    db.commit()
    db.refresh(post)

    # ✅ Fetch updated media entry
    media_entry = db.query(PostMedia).filter(PostMedia.post_id == post.id).first()
    media_url = media_entry.media_url if media_entry else None
    
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
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == current_user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail=STATUS_404_ERROR)

    if content is not None:
        post.content = content  

    allowed_docs = {".pdf", ".docx", ".txt"}

    # Handle document file replacement
    if document_file is not None and document_file.filename != "":  
        doc_ext = Path(document_file.filename).suffix.lower()
        if doc_ext not in allowed_docs:
            raise HTTPException(status_code=400, detail="Invalid document format.")

        doc_filename = f"{current_user.id}_{secrets.token_hex(8)}{doc_ext}"
        document_path = os.path.join(DOCUMENT_DIR, doc_filename)

        # Save the new document file
        with open(document_path, "wb") as buffer:
            buffer.write(document_file.file.read())

        # Check if the post already has an associated document
        doc_entry = db.query(PostDocument).filter(PostDocument.post_id == post.id).first()
        if doc_entry:
            old_doc_path = doc_entry.document_url
            if old_doc_path and os.path.exists(old_doc_path):
                os.remove(old_doc_path)  # Safely remove old file

            doc_entry.document_url = doc_filename
            doc_entry.document_type = doc_ext
        else:
            new_media = PostDocument(post_id=post.id, document_url=doc_filename, document_type=doc_ext)
            db.add(new_media)

    db.commit()
    db.refresh(post)

    # Fetch updated document entry
    doc_entry = db.query(PostDocument).filter(PostDocument.post_id == post.id).first()
    document_url = doc_entry.document_url if doc_entry else ""

    return {
        "message": "Document post updated successfully",
        "updated_post": {
            "id": post.id,
            "user_id": post.user_id,
            "content": post.content,
            "post_type": post.post_type,
            "created_at": post.created_at,
            "document_url": document_url,  # Ensure document URL is always returned
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
    # Fetch the post and associated event
    post, event = get_post_and_event(post_id, current_user.id, db)

    # Convert event date & time to UTC if provided
    event_datetime_utc = None
    if event_date and event_time and user_timezone:
        event_datetime_utc = convert_to_utc(event_date, event_time, user_timezone)

    # Prepare fields to update for post and event
    post_fields = {"content": content}
    event_fields = {
        "title": event_title,
        "description": event_description,
        "event_datetime": event_datetime_utc if event_datetime_utc else event.event_datetime,
        "location": location,
    }

    # Update post and event fields
    updated_post = False
    updated_post |= update_fields(post_fields, post, db)
    updated_post |= update_fields(event_fields, event, db)

    # Return the response based on whether anything was updated
    if updated_post:
        updated_post_data = {
            "id": post.id,
            "content": post.content,
            "title": event.title,
            "description": event.description,
            "event_datetime": event.event_datetime,
            "location": event.location
        }
        return {"message": "Event post updated successfully", "updated_post": updated_post_data}

    return {"message": "No changes detected"}


@router.delete("/delete_post/{post_id}/")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find the post
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == current_user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or unauthorized")

    # Delete the post
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