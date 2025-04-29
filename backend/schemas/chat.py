from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional

class MessageType(str, Enum):
    TEXT = "text"
    LINK = "link"
    IMAGE = "image"
    FILE = "file"

class MessageOut(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: Optional[str]
    file_url: Optional[str]
    message_type: str
    timestamp: datetime
    is_read: bool

    class Config:
        from_attributes = True

class ConversationOut(BaseModel):
    user_id: int
    username: str
    avatar: str | None = None
    last_message: str | None
    file_url: str | None
    message_type: str
    timestamp: datetime
    is_sender: bool
    unread_count: int

    class Config:
        from_attributes = True