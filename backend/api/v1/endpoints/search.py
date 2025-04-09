from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from database.session import SessionLocal
from typing import List
from pydantic import BaseModel
from models.post import Post
from core.dependencies import get_db
import logging
from models.user import User
from api.v1.endpoints.auth import get_current_user

router = APIRouter()

# Pydantic model for the post response
class PostBase(BaseModel):
    id: int
    user_id: int
    content: str
    post_type: str
    created_at: str
    like_count: int

    class Config:
        from_attributes = True  # Allows mapping SQLAlchemy models to Pydantic

@router.get("/search", response_model=dict[str, List[PostBase]])
def search_posts_by_keyword(
    keyword: str = Query(..., min_length=1, title="Search Keyword"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search for posts by a specific keyword in content or username.
    Returns only posts for now, as per the requirement.
    """
    try:
        # Search posts by content or username
        posts = db.query(Post).filter(
            (Post.content.ilike(f"%{keyword}%") & (Post.event == None)) |  # Posts with matching content, not tied to events
            (Post.user.has(User.username.ilike(f"%{keyword}%")))  # Posts by users with matching username
        ).all()

        # If no posts are found
        if not posts:
            return {"posts": []}  # Return empty list instead of raising 404, for simplicity

        # Prepare the response
        return {
            "posts": [
                {
                    "id": post.id,
                    "user_id": post.user_id,
                    "content": post.content,
                    "post_type": post.post_type,
                    "created_at": post.created_at.isoformat(),  # Convert datetime to string
                    "like_count": post.like_count
                }
                for post in posts
            ]
        }

    except Exception as e:
        logging.error(f"Error searching for keyword '{keyword}': {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")