from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from models.user import User
from models.post import Post, PostMedia, PostDocument, Event, Comment
from utils.cloudinary import upload_to_cloudinary
from services.PostHandler import get_user_like_status
from services.PostTypeHandler import get_post_additional_data
from services.PostHandler import extract_hashtags
from models.university import University
from models.hashtag import Hashtag

def validate_post_ownership(post_id: int, user_id: int, db: Session) -> Post:
    """Validate post ownership and return the post if valid."""
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == user_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or not authorized")
    return post

def prepare_post_response(post: Post, current_user: User, db: Session) -> Dict[str, Any]:
    """Prepare standardized post response with user and interaction data."""
    user_liked = get_user_like_status(post.id, current_user.id, db)
    comment_count = db.query(Comment).filter(Comment.post_id == post.id).count()
    
    response = {
        "id": post.id,
        "user_id": post.user_id,  # Changed from post.user.id to post.user_id
        "post_type": post.post_type,
        "content": post.content,
        "created_at": post.created_at,
        "user": {
            "id": post.user.id,
            "username": post.user.username,
            "profile_picture": post.user.profile_picture,
            "university_name": post.user.university_name
        },
        "total_likes": post.like_count,
        "user_liked": user_liked,
        "comment_count": comment_count
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
    hashtags = extract_hashtags(post.content)
    universities = db.query(University.name).all()
    university_names = {name.lower() for (name,) in universities}

    for tag in hashtags:
        if tag.lower() in university_names:
            existing_hashtag = db.query(Hashtag).filter_by(name=tag.lower()).first()
            if existing_hashtag:
                existing_hashtag.usage_count += 1
            else:
                existing_hashtag = Hashtag(name=tag.lower(), usage_count=1)
                db.add(existing_hashtag)

            post.hashtags.append(existing_hashtag)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post