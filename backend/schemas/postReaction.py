from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class LikeCreate(BaseModel):
    post_id: Optional[int] = None
    comment_id: Optional[int] = None

    class Config:
        from_attributes = True

class LikeResponse(BaseModel):
    id: int
    user_id: int
    post_id: Optional[int]
    comment_id: Optional[int]
    created_at: datetime
    total_likes: int
    user_liked: bool
    message: str

    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    post_id: int
    content: str
    parent_id: Optional[int] = None  # For replies

    class Config:
        from_attributes = True

class CommentNestedResponse(BaseModel):
    id: int
    user_id: int
    post_id: int
    content: str
    parent_id: Optional[int] = None
    created_at: datetime
    replies: List["CommentNestedResponse"] = []  # Nested replies

    class Config:
        from_attributes = True

class ShareCreate(BaseModel):
    post_id: int

    class Config:
        from_attributes = True

class ShareResponse(BaseModel):
    id: int
    user_id: int
    post_id: int
    share_link: str
    created_at: datetime

    class Config:
        from_attributes = True
