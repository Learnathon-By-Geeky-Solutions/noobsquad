from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from core.dependencies import get_db
from models.user import User
from api.v1.endpoints.auth import get_current_user
from services.SearchHandler import SearchHandler

router = APIRouter()

@router.get("/search")
def search_posts_by_keyword(
    keyword: str = Query(..., min_length=1, title="Search Keyword"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search for posts by keyword in content or username."""
    posts = SearchHandler.search_posts(db, keyword)
    return {"posts": posts}

@router.get("/search/users")
def search_users_by_keyword(
    keyword: str = Query(..., min_length=1, title="Search Keyword"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search for users by username or email."""
    users = SearchHandler.search_users(db, keyword)
    return {"users": users}

@router.get("/search/all")
def search_all_by_keyword(
    keyword: str = Query(..., min_length=1, title="Search Keyword"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search across all searchable entities (posts and users)."""
    return SearchHandler.search_all(db, keyword)