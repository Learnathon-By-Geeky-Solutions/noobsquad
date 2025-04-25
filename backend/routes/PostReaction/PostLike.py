from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.post import Like, Post
from models.user import User
from database.session import SessionLocal
from schemas.postReaction import LikeCreate, LikeResponse
from api.v1.endpoints.Auth.auth import get_current_user
from services.reaction import add_like, remove_like, get_like_count, notify_if_not_self

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