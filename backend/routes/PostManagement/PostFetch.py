from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Union
from api.v1.endpoints.Auth.auth import get_current_user
from models.user import User
from models.post import Post, Event
from schemas.post import  EventResponse
from database.session import SessionLocal
from sqlalchemy.orm import Session
from services.services import get_newer_posts, get_user_like_status, get_post_additional_data


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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




@router.get("/posts/")
def get_posts(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Post)
    if user_id:
        query = query.filter(Post.user_id == user_id)
    return query.all()


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

        return event
    else:
        events = db.query(Event).all()
        if not events:
            raise HTTPException(status_code=404, detail="No events found")

        return events