from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.post import Like, Comment, Share, Post, Event, EventAttendee
from schemas.postReaction import LikeCreate, LikeResponse, CommentCreate, ShareResponse, CommentNestedResponse, ShareCreate
from models.post import Post, PostMedia, PostDocument, Event, Like, Comment

# ----------------------------------------
# Helper Functions
# ----------------------------------------

def get_comment_by_id(db: Session, comment_id: int) -> Comment:
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
    return comment


def get_post_by_id(db: Session, post_id: int) -> Post:
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    return post