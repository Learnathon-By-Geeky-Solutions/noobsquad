from typing import List, Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.post import Post
from models.user import User
import logging

logger = logging.getLogger(__name__)

def _format_post_response(post: Post) -> Dict[str, Any]:
    return {
        "id": post.id,
        "user_id": post.user_id,
        "content": post.content,
        "post_type": post.post_type,
        "created_at": post.created_at.isoformat(),
        "like_count": post.like_count
    }

def _format_user_response(user: User) -> Dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "profile_picture": user.profile_picture
    }

def _search_posts_by_keyword(db: Session, keyword: str) -> List[Post]:
    return db.query(Post).filter(
        (Post.content.ilike(f"%{keyword}%") & (Post.event == None)) |  # Posts with matching content, not tied to events
        (Post.user.has(User.username.ilike(f"%{keyword}%")))  # Posts by users with matching username
    ).all()

def _search_users_by_keyword(db: Session, keyword: str) -> List[User]:
    return db.query(User).filter(
        User.username.ilike(f"%{keyword}%") |
        User.email.ilike(f"%{keyword}%")
    ).all()

class SearchHandler:
    @staticmethod
    def search_posts(
        db: Session,
        keyword: str
    ) -> List[Dict[str, Any]]:
        """Search for posts by keyword in content or username."""
        try:
            posts = _search_posts_by_keyword(db, keyword)
            return [_format_post_response(post) for post in posts]
        except Exception as e:
            logger.error(f"Error searching for keyword '{keyword}': {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @staticmethod
    def search_users(
        db: Session,
        keyword: str
    ) -> List[Dict[str, Any]]:
        """Search for users by username or email."""
        try:
            users = _search_users_by_keyword(db, keyword)
            return [_format_user_response(user) for user in users]
        except Exception as e:
            logger.error(f"Error searching users with keyword '{keyword}': {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @staticmethod
    def search_all(
        db: Session,
        keyword: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Search across all searchable entities (posts and users)."""
        try:
            posts = SearchHandler.search_posts(db, keyword)
            users = SearchHandler.search_users(db, keyword)
            
            return {
                "posts": posts,
                "users": users
            }
        except Exception as e:
            logger.error(f"Error performing global search with keyword '{keyword}': {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error") 