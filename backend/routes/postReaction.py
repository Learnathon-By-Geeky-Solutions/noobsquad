from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def update_like_count(like_data, db: Session, action: str):
    if like_data.post_id:
        post = db.query(Post).filter(Post.id == like_data.post_id).first()
        if post:
            post.like_count = max(0, post.like_count + (1 if action == 'add' else -1))
    
    if like_data.comment_id:
        comment = db.query(Comment).filter(Comment.id == like_data.comment_id).first()
        if comment:
            comment.like_count = max(0, comment.like_count + (1 if action == 'add' else -1))
    
    db.commit()

# Helper function to remove like
def remove_like(existing_like, db: Session, like_data: LikeCreate):
    db.delete(existing_like)
    update_like_count(like_data, db, 'remove')

# Helper function to add new like
def add_like(like_data: LikeCreate, db: Session, current_user: User):
    created_at = datetime.now(ZoneInfo("UTC"))
    new_like = Like(user_id=current_user.id, post_id=like_data.post_id, comment_id=like_data.comment_id, created_at=created_at)
    db.add(new_like)
    update_like_count(like_data, db, 'add')
    db.commit()
    db.refresh(new_like)
    return new_like

@router.post("/like", response_model=LikeResponse)
def like_action(like_data: LikeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not like_data.post_id and not like_data.comment_id:
        raise HTTPException(status_code=400, detail="Either post_id or comment_id must be provided.")
    
    # Check if the like already exists
    existing_like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.post_id == like_data.post_id,
        Like.comment_id == like_data.comment_id
    ).first()

    if existing_like:
        remove_like(existing_like, db, like_data)
        return {
            "id": existing_like.id,
            "user_id": existing_like.user_id,
            "post_id": existing_like.post_id,
            "comment_id": existing_like.comment_id,
            "created_at": existing_like.created_at,
            "total_likes": db.query(Post if like_data.post_id else Comment).filter(
                Post.id == like_data.post_id if like_data.post_id else Comment.id == like_data.comment_id
            ).first().like_count,
            "user_liked": False,
            "message": "Like removed"
        }

    new_like = add_like(like_data, db, current_user)

    if like_data.post_id:
        post = db.query(Post).filter(Post.id == like_data.post_id).first()
        if post and post.user_id != current_user.id:  # Don't notify if liking own post

            create_notification(
                db=db,
                recipient_id=post.user_id,  # The owner of the post being liked
                actor_id=current_user.id,  # The user who liked the post
                notif_type="like",
                post_id=post.id  # The post that was liked
            )
    
    return {
        "id": new_like.id,
        "user_id": new_like.user_id,
        "post_id": new_like.post_id,
        "comment_id": new_like.comment_id,
        "created_at": new_like.created_at,
        "total_likes": db.query(Post if like_data.post_id else Comment).filter(
            Post.id == like_data.post_id if like_data.post_id else Comment.id == like_data.comment_id
        ).first().like_count,
        "user_liked": True,
        "message": "Like added successfully"
    }

# ✅ Comment on a Post
@router.post("/{post_id}/comment", response_model=CommentNestedResponse)
def comment_post(comment_data: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if comment_data.parent_id is not None:
        raise HTTPException(status_code=400, detail="Root comment cannot have a parent_id.")

    created_at = datetime.now(ZoneInfo("UTC"))
    new_comment = Comment(
        user_id=current_user.id,
        post_id=comment_data.post_id,
        content=comment_data.content,
        parent_id=None,
        created_at = created_at
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    post_owner = db.query(User).filter(User.id == new_comment.post.user_id).first()
    if post_owner and post_owner.id != current_user.id:
        create_notification(db, recipient_id=post_owner.id, actor_id=current_user.id, notif_type="comment", post_id=new_comment.post_id)
    return new_comment


# ✅ Reply to a Comment (Max Depth = 2)
@router.post("/{post_id}/comment/{parent_comment_id}/reply", response_model=CommentNestedResponse)
def reply_comment(comment_data: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    parent_comment = db.query(Comment).filter(Comment.id == comment_data.parent_id).first()
    
    if not parent_comment:
        raise HTTPException(status_code=404, detail="Parent comment not found.")

    # Enforce max depth of 2
    if parent_comment.parent_id is not None:
        raise HTTPException(status_code=400, detail="Cannot reply to a reply. Max depth reached.")
    
    created_at = datetime.now(ZoneInfo("UTC"))
    new_reply = Comment(
        user_id=current_user.id,
        post_id=parent_comment.post_id,
        content=comment_data.content,
        parent_id=comment_data.parent_id,
        created_at=created_at
    )
    db.add(new_reply)
    db.commit()
    db.refresh(new_reply)
    # 🔔 Send Notification to Comment Owner
    comment_owner = db.query(User).filter(User.id == parent_comment.user_id).first()
    if comment_owner and comment_owner.id != current_user.id:
        create_notification(db, recipient_id=comment_owner.id, actor_id=current_user.id, notif_type="reply", post_id=new_reply.post_id)
    return new_reply


@router.get("/{post_id}/comments")
def get_comments(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    ✅ Fetch comments for a specific post.
    """
    
    # Fetch parent comments (comments with parent_id=None)
    parent_comments = db.query(Comment).filter(Comment.post_id == post_id, Comment.parent_id == None).all()

    comment_list = []
    for comment in parent_comments:
        # Fetch replies for this parent comment (comments with parent_id equal to the parent comment's id)
        replies = db.query(Comment).filter(Comment.parent_id == comment.id).all()

        # Building comment data
        comment_data = {
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at,
            "user": {
                "id": comment.user.id,
                "username": comment.user.username,
                "profile_picture": f"http://127.0.0.1:8000/uploads/profile_pictures/{comment.user.profile_picture}"
            },
            "total_likes": len(comment.likes),
            "user_liked": any(like.user_id == current_user.id for like in comment.likes),
            "replies": [
                {
                    "id": reply.id,
                    "content": reply.content,
                    "created_at": reply.created_at,
                    "user": {
                        "id": reply.user.id,
                        "username": reply.user.username,
                        "profile_picture": f"http://127.0.0.1:8000/uploads/profile_pictures/{reply.user.profile_picture}"
                    },
                    "total_likes": len(reply.likes),
                    "user_liked": any(like.user_id == current_user.id for like in reply.likes),
                }
                for reply in replies
            ]
        }

        comment_list.append(comment_data)

    return {"comments": comment_list}



#delete the comment
@router.delete("/comment/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Get the comment by ID
    comment = db.query(Comment).filter(Comment.id == comment_id).first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
    
    # Get the post associated with the comment
    post = db.query(Post).filter(Post.id == comment.post_id).first()

    # Check if the current user is the comment owner or the post owner
    if comment.user_id != current_user.id and post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this comment.")

    # Delete the comment if the user has permission
    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted successfully"}



# ✅ Share a Post with a Unique Link (Stored)
@router.post("/{post_id}/share", response_model=ShareResponse)
def share_post(share_data: ShareCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = db.query(Post).filter(Post.id == share_data.post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    
    share_token = str(uuid.uuid4())
    
    created_at = datetime.now(ZoneInfo("UTC"))
    new_share = Share(
        user_id=current_user.id,
        post_id=share_data.post_id,
        share_token=share_token,
        created_at=created_at
    )
    db.add(new_share)
    db.commit()
    db.refresh(new_share)
    share_link = f"http://localhost:5173/share/{new_share.share_token}"

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
def get_shared_post(share_token: str, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    shared_post = db.query(Share).filter(Share.share_token == share_token).first()
    
    if not shared_post:
        raise HTTPException(status_code=404, detail="Invalid or expired share link")

    post = db.query(Post).filter(Post.id == shared_post.post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    
    user_liked = db.query(Like).filter(Like.post_id == post.id, Like.user_id == current_user.id).first() is not None

    
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
        "user_liked": user_liked,
        
    }

    # ✅ Fetch additional data based on post_type
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


    
    return post_data  # ✅ This returns all fields defined in the Post model



# ✅ RSVP for an event
@router.post("/event/{event_id}/rsvp", response_model=EventAttendeeResponse)
def rsvp_event(
    event_id: int, 
    attendee_data: EventAttendeeCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")

    existing_attendance = db.query(EventAttendee).filter(
        EventAttendee.event_id == event_id, EventAttendee.user_id == current_user.id
    ).first()

    if existing_attendance:
        existing_attendance.status = attendee_data.status
    else:
        new_attendance = EventAttendee(
            event_id=event_id,
            user_id=current_user.id,
            status=attendee_data.status
        )
        db.add(new_attendance)

    db.commit()
    return existing_attendance if existing_attendance else new_attendance

# ✅ Get attendees of an event
@router.get("/event/{event_id}/attendees", response_model=list[EventAttendeeResponse])
def get_event_attendees(event_id: int, db: Session = Depends(get_db)):
    attendees = db.query(EventAttendee).filter(EventAttendee.event_id == event_id).all()
    return attendees

# ✅ Remove RSVP
@router.delete("/event/{event_id}/rsvp")
def remove_rsvp(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rsvp = db.query(EventAttendee).filter(EventAttendee.event_id == event_id, EventAttendee.user_id == current_user.id).first()

    if not rsvp:
        raise HTTPException(status_code=404, detail="You haven't RSVP'd for this event.")

    db.delete(rsvp)
    db.commit()
    return {"message": "RSVP removed successfully"}