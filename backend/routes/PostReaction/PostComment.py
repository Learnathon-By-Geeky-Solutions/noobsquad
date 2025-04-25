from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.post import  Comment, Post
from models.user import User
from database.session import SessionLocal
from schemas.postReaction import  CommentCreate, CommentNestedResponse
from api.v1.endpoints.Auth.auth import get_current_user
from datetime import datetime
from zoneinfo import ZoneInfo
from services.reaction import notify_if_not_self, build_comment_response

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/{post_id}/comment", response_model=CommentNestedResponse)
def comment_post(comment_data: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if comment_data.parent_id:
        raise HTTPException(status_code=400, detail="Root comment cannot have a parent_id.")

    new_comment = Comment(
        user_id=current_user.id,
        post_id=comment_data.post_id,
        content=comment_data.content,
        parent_id=None,
        created_at=datetime.now(ZoneInfo("UTC"))
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    notify_if_not_self(db, current_user.id, new_comment.post.user_id, "comment", new_comment.post_id)
    return new_comment

@router.post("/{post_id}/comment/{parent_comment_id}/reply", response_model=CommentNestedResponse)
def reply_comment(comment_data: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    parent = db.query(Comment).filter(Comment.id == comment_data.parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent comment not found.")
    if parent.parent_id:
        raise HTTPException(status_code=400, detail="Cannot reply to a reply. Max depth reached.")

    reply = Comment(
        user_id=current_user.id,
        post_id=parent.post_id,
        content=comment_data.content,
        parent_id=comment_data.parent_id,
        created_at=datetime.now(ZoneInfo("UTC"))
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)
    notify_if_not_self(db, current_user.id, parent.user_id, "reply", reply.post_id)
    return reply

@router.get("/{post_id}/comments")
def get_comments(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    parents = db.query(Comment).filter(Comment.post_id == post_id, Comment.parent_id == None).all()
    return {"comments": [build_comment_response(c, db, current_user) for c in parents]}

@router.delete("/comment/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
    post = db.query(Post).filter(Post.id == comment.post_id).first()
    if comment.user_id != current_user.id and post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment.")
    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted successfully"}