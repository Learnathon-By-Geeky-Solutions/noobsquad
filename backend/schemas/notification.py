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

    class Config:
        from_attributes = True
