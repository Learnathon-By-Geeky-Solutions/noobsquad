from pydantic import BaseModel
from datetime import datetime

class NotificationCreate(BaseModel):
    user_id: int
    actor_id: int
    type: str
    post_id: int | None = None

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    actor_id: int
    type: str
    post_id: int | None
    is_read: bool
    created_at: datetime
    actor_username: str  # <-- Add this
    actor_image_url: str

    class Config:
        from_attributes = True
