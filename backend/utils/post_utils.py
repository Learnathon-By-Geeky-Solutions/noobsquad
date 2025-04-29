from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from models.user import User
from models.post import Post, PostMedia, PostDocument, Event
from utils.cloudinary import upload_to_cloudinary

def validate_post_ownership(post_id: int, user_id: int, db: Session) -> Post:
    """Validate post ownership and return the post if valid."""
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == user_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or not authorized")
    return post

def prepare_post_response(post: Post, current_user: User, db: Session) -> Dict[str, Any]:
    """Prepare standardized post response with user and interaction data."""
    from services.PostHandler import get_user_like_status, get_post_additional_data
    
    user_liked = get_user_like_status(post.id, current_user.id, db)
    
    response = {
        "id": post.id,
        "post_type": post.post_type,
        "content": post.content,
        "created_at": post.created_at,
        "user": {
            "id": post.user.id,
            "username": post.user.username,
            "profile_picture": post.user.profile_picture
        },
        "total_likes": post.like_count,
        "user_liked": user_liked
    }
    
    # Add type-specific data
    response.update(get_post_additional_data(post, db))
    return response

async def handle_media_upload(
    media_file: UploadFile,
    folder_name: str
) -> Dict[str, str]:
    """Handle media file upload to cloudinary and return upload details."""
    upload_result = upload_to_cloudinary(
        media_file.file,
        folder_name=folder_name
    )
    return {
        "secure_url": upload_result["secure_url"],
        "resource_type": upload_result["resource_type"]
    }

def create_base_post(
    db: Session,
    user_id: int,
    content: Optional[str],
    post_type: str
) -> Post:
    """Create a base post entry with common fields."""
    post = Post(
        user_id=user_id,
        content=content,
        post_type=post_type
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post 