from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.post import Like, Comment, Share, Post, Event, EventAttendee
from models.user import User
from schemas.post import PostResponse
from database.session import SessionLocal
from schemas.postReaction import LikeCreate, LikeResponse, CommentCreate, ShareResponse, CommentNestedResponse, ShareCreate
from schemas.eventAttendees import EventAttendeeCreate, EventAttendeeResponse
from api.v1.endpoints.auth import get_current_user
from datetime import datetime
import uuid  # Secure share token
from typing import List
from models.user import User
from models.post import Post, PostMedia, PostDocument, Event, Like, Comment
from zoneinfo import ZoneInfo
from crud.notification import create_notification
from schemas.notification import NotificationCreate
from services.reaction import get_like_count, add_like, remove_like, notify_if_not_self, build_comment_response
from models.post import Like, Comment, Share, Post, Event, EventAttendee
from schemas.post import PostResponse
from database.session import SessionLocal
from schemas.postReaction import LikeCreate, LikeResponse, CommentCreate, ShareResponse, CommentNestedResponse, ShareCreate
from schemas.eventAttendees import EventAttendeeCreate, EventAttendeeResponse
from api.v1.endpoints.auth import get_current_user
from .PostReaction.CommentHelperFunc import get_comment_by_id, get_post_by_id
from schemas.postReaction import ShareResponse, ShareCreate
from .PostReaction.ShareHandler import (
    create_share,
    get_post_by_share_token,
    get_post_additional_data
)
from models.post import Like, Comment, Share, Post, Event, EventAttendee
from schemas.postReaction import LikeCreate, LikeResponse, CommentCreate, ShareResponse, CommentNestedResponse, ShareCreate
from schemas.eventAttendees import EventAttendeeCreate, EventAttendeeResponse
from models.post import Post, PostMedia, PostDocument, Event, Like, Comment
from .PostReaction.AttendeeHelperFunction import get_event_by_id, update_or_create_rsvp, count_rsvp_status, get_user_rsvp

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/like", response_model=LikeResponse)
def like_action(
    like_data: LikeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not like_data.post_id and not like_data.comment_id:
        raise HTTPException(status_code=400, detail="Either post_id or comment_id must be provided.")

    existing_like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.post_id == like_data.post_id,
        Like.comment_id == like_data.comment_id
    ).first()

    total_likes = get_like_count(db, like_data)

    if existing_like:
        response = {
            "id": existing_like.id,
            "user_id": existing_like.user_id,
            "post_id": existing_like.post_id,
            "comment_id": existing_like.comment_id,
            "created_at": existing_like.created_at,
            "total_likes": max(0, total_likes - 1),
            "user_liked": False,
            "message": "Like removed"
        }
        remove_like(existing_like, db, like_data)
        return response

    new_like = add_like(like_data, db, current_user)

    if like_data.post_id:
        post = db.query(Post).filter(Post.id == like_data.post_id).first()
        if post:
            notify_if_not_self(db, current_user.id, post.user_id, "like", post.id)

    total_likes = get_like_count(db, like_data)

    return {
        "id": new_like.id,
        "user_id": new_like.user_id,
        "post_id": new_like.post_id,
        "comment_id": new_like.comment_id,
        "created_at": new_like.created_at,
        "total_likes": total_likes,
        "user_liked": True,
        "message": "Like added successfully"
    }

@router.post("/{post_id}/comment", response_model=CommentNestedResponse)
def comment_post(comment_data: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if comment_data.parent_id:
        raise HTTPException(status_code=400, detail="Root comment cannot have a parent_id.")
    
    new_comment = Comment(
        user_id=current_user.id,
        post_id=comment_data.post_id,
        content=comment_data.content,
        created_at=datetime.now(ZoneInfo("UTC"))
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    notify_if_not_self(db, current_user.id, new_comment.post.user_id, "comment", new_comment.post_id)
    
    return new_comment


@router.post("/{post_id}/comment/{parent_comment_id}/reply", response_model=CommentNestedResponse)
def reply_comment(comment_data: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    parent = get_comment_by_id(db, comment_data.parent_id)
    
    if parent.parent_id:
        raise HTTPException(status_code=400, detail="Cannot reply to a reply. Max depth reached.")
    
    reply = Comment(
        user_id=current_user.id,
        post_id=parent.post_id,
        content=comment_data.content,
        parent_id=parent.id,
        created_at=datetime.now(ZoneInfo("UTC"))
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)

    notify_if_not_self(db, current_user.id, parent.user_id, "reply", reply.post_id)

    return reply


@router.get("/{post_id}/comments")
def get_comments(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    parent_comments = db.query(Comment).filter(Comment.post_id == post_id, Comment.parent_id == None).all()
    return {"comments": [build_comment_response(comment, db, current_user) for comment in parent_comments]}


# ✅ Share a Post with a Unique Link (Stored)
@router.post("/{post_id}/share", response_model=ShareResponse)
def share_post(share_data: ShareCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verify post exists
    post = db.query(Post).filter(Post.id == share_data.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    
    # Create share entry
    new_share = create_share(db, current_user.id, share_data.post_id)
    share_link = f"http://localhost:5173/share/{new_share.share_token}"

    # Notify post owner if different from current user
    post_owner = db.query(User).filter(User.id == post.user_id).first()
    if post_owner and post_owner.id != current_user.id:
        create_notification(db, recipient_id=post_owner.id, actor_id=current_user.id, notif_type="share", post_id=new_share.post_id)

    return {
        "id": new_share.id,
        "user_id": new_share.user_id,
        "post_id": new_share.post_id,
        "share_link": share_link,
        "created_at": new_share.created_at
    }

@router.get("/share/{share_token}")
def get_shared_post(share_token: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Get post from share token
    post = get_post_by_share_token(db, share_token)
    
    # Get post data with type-specific information
    return get_post_additional_data(db, post, current_user.id)


@router.post("/event/{event_id}/rsvp", response_model=EventAttendeeResponse)
def rsvp_event(
    event_id: int, 
    attendee_data: EventAttendeeCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """RSVP to an event (Going or Interested)."""
    get_event_by_id(db, event_id)  # Ensure event exists
    return update_or_create_rsvp(db, event_id, current_user.id, attendee_data.status)

@router.get("/event/{event_id}/my_rsvp/")
def get_user_rsvp_status(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get the current user's RSVP status for an event."""
    rsvp = get_user_rsvp(db, event_id, current_user.id)
    return {"status": rsvp.status if rsvp else None}


@router.get("/event/{event_id}/attendees", response_model=list[EventAttendeeResponse])
def get_event_attendees(event_id: int, db: Session = Depends(get_db)):
    """Retrieve all attendees of an event."""
    return db.query(EventAttendee).filter(EventAttendee.event_id == event_id).all()


@router.get("/posts/events/rsvp/counts/")
def get_rsvp_counts(event_id: int = Query(...), db: Session = Depends(get_db)):
    """Get RSVP counts (Going/Interested) for an event."""
    return {
        "going": count_rsvp_status(db, event_id, "going"),
        "interested": count_rsvp_status(db, event_id, "interested")
    }
