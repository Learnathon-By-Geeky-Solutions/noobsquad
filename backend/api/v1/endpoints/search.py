from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.session import SessionLocal
from typing import List
from pydantic import BaseModel
from models.connection import Connection
from models.post import Post, Event
from core.dependencies import get_db
import logging
from models.user import User
from api.v1.endpoints.auth import get_current_user


router = APIRouter()

# Define your Pydantic models for the response
class ConnectionBase(BaseModel):
    id: int
    user_id: int
    friend_id: int
    status: str

    class Config:
        from_attributes = True

class PostBase(BaseModel):
    id: int
    user_id: int
    content: str
    post_type: str
    created_at: str
    like_count: int

    class Config:
        from_attributes = True

class EventBase(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    location: str

    class Config:
        from_attributes = True


@router.get("/search")
def search_by_keyword(
    keyword: str = Query(..., min_length=1, title="Search Keyword"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search for posts and connections by a specific keyword.
    """
    try:
        # Search connections by username (both user and friend)
        connections = db.query(Connection).filter(
            (Connection.user.has(User.username.ilike(f"%{keyword}%"))) |
            (Connection.friend.has(User.username.ilike(f"%{keyword}%")))
        ).all()

        # Search posts by content or user
        posts = db.query(Post).filter(
            (Post.content.ilike(f"%{keyword}%")& (Post.event == None)) |
            (Post.user.has(User.username.ilike(f"%{keyword}%")))
        ).all()

        #Search events by title or description
        events = db.query(Event).filter(
            (Event.title.ilike(f"%{keyword}%")) |
            (Event.description.ilike(f"%{keyword}%")) |
            (Event.user.has(User.username.ilike(f"%{keyword}%")))
        ).all()

        # If no results are found for both connections and posts
        if not connections and not posts and not events:
            raise HTTPException(status_code=404, detail="No results found")

        # Prepare the results
        return {
            "connections": [
                {
                    "id": connection.id,
                    "user_id": connection.user_id,
                    "friend_id": connection.friend_id,
                    "status": connection.status
                }
                for connection in connections
            ],
            "posts": [
                {
                    "id": post.id,
                    "user_id": post.user_id,
                    "content": post.content,
                    "post_type": post.post_type,
                    "created_at": post.created_at.isoformat(),
                    "like_count": post.like_count
                }
                for post in posts
            ],
            "events": [
                {
                    "id": event.id,
                    "user_id": event.user_id,
                    "title": event.title,
                    "description": event.description,
                    "location":event.location
                }
                for event in events
            ]

        }

    except Exception as e:
        logging.error(f"Error searching for keyword '{keyword}': {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")