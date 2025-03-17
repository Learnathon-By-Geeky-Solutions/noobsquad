from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.post import Like, Comment, Share, Post, Event, EventAttendee
from models.user import User
from database.session import SessionLocal
from schemas.postReaction import LikeCreate, LikeResponse, CommentCreate, ShareResponse, CommentResponse, ShareCreate
from schemas.eventAttendees import EventAttendeeCreate, EventAttendeeResponse
from api.v1.endpoints.auth import get_current_user
from datetime import datetime
import uuid  # Secure share token


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Like a Post or Comment
@router.post("/like", response_model=LikeResponse)
def like_action(like_data: LikeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not like_data.post_id and not like_data.comment_id:
        raise HTTPException(status_code=400, detail="Either post_id or comment_id must be provided.")

    existing_like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.post_id == like_data.post_id,
        Like.comment_id == like_data.comment_id
    ).first()

    if existing_like:
        raise HTTPException(status_code=400, detail="Already liked this item.")

    new_like = Like(user_id=current_user.id, post_id=like_data.post_id, comment_id=like_data.comment_id, created_at=datetime.utcnow())
    db.add(new_like)
    db.commit()
    db.refresh(new_like)
    return new_like

# ✅ Unlike a Post or Comment
@router.delete("/unlike")
def unlike_action(post_id: int = None, comment_id: int = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not post_id and not comment_id:
        raise HTTPException(status_code=400, detail="Either post_id or comment_id must be provided.")

    like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.post_id == post_id,
        Like.comment_id == comment_id
    ).first()

    if not like:
        raise HTTPException(status_code=404, detail="Like not found.")

    db.delete(like)
    db.commit()
    return {"message": "Unlike successful"}


# ✅ Comment on a Post
@router.post("/comment", response_model=CommentResponse)
def comment_post(comment_data: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_comment = Comment(
        user_id=current_user.id,
        post_id=comment_data.post_id,
        content=comment_data.content,
        parent_id=comment_data.parent_id,
        created_at=datetime.utcnow()
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

# ✅ Reply to a Comment
@router.post("/comment/reply", response_model=CommentResponse)
def reply_comment(comment_data: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    parent_comment = db.query(Comment).filter(Comment.id == comment_data.parent_id).first()
    
    if not parent_comment:
        raise HTTPException(status_code=404, detail="Parent comment not found.")

    new_reply = Comment(
        user_id=current_user.id,
        post_id=parent_comment.post_id,
        content=comment_data.content,
        parent_id=comment_data.parent_id,
        created_at=datetime.utcnow()
    )
    db.add(new_reply)
    db.commit()
    db.refresh(new_reply)
    return new_reply

# ✅ Delete a Comment
@router.delete("/comment/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.user_id == current_user.id).first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")

    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted successfully"}


# ✅ Share a Post
@router.post("/share", response_model=ShareResponse)
def share_post(share_data: ShareCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = db.query(Post).filter(Post.id == share_data.post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    
    share_token = str(uuid.uuid4())

    share_link = f"http://UHub.com/share/{share_token}"

    new_share = Share(
        user_id=current_user.id,
        post_id=share_data.post_id,
        created_at=datetime.utcnow()
    )
    db.add(new_share)
    db.commit()
    db.refresh(new_share)

    return {
        "id": new_share.id,
        "user_id": new_share.user_id,
        "post_id": new_share.post_id,
        "share_link": share_link,
        "created_at": new_share.created_at
    }

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