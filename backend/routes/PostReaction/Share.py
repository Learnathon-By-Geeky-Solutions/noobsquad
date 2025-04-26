from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.post import Post
from models.user import User
from database.session import SessionLocal
from schemas.postReaction import ShareResponse, ShareCreate
from api.v1.endpoints.auth import get_current_user
from .ShareHandler import (
    create_share,
    get_post_by_share_token,
    get_post_additional_data
)
from crud.notification import create_notification

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
