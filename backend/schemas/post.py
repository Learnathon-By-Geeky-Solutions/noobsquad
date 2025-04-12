from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Base Post Response Schema
class PostResponse(BaseModel):
    id: int
    user_id: int
    post_type: str
    content: Optional[str] = None
    created_at: datetime  # Allow null values temporarily
    like_count: int  # Total likes
    comment_count: int  # Total comments
    user_liked: bool  # Has the current user liked it?

    class Config:
        from_attributes = True  # ORM compatibility

class MediaPostResponse(BaseModel):
    id: int
    post_id: int
    media_url: str  # Path instead of HttpUrl (since it's stored locally)
    media_type: str

    class Config:
        from_attributes = True

class DocumentPostResponse(BaseModel):
    id: int
    post_id: int
    document_url: str  # Path instead of HttpUrl
    document_type: str

    class Config:
        from_attributes = True

class EventResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    title: str
    description: Optional[str] = None
    event_datetime: datetime  # ✅ Use datetime instead of separate date and time
    location: Optional[str] = None
    image_url: Optional[str]

    class Config:
        from_attributes = True

class PostUpdateBase(BaseModel):
    content: Optional[str] = Field(None, example="Updated content here")

class TextPostUpdate(PostUpdateBase):
    pass  # No extra fields, only content



