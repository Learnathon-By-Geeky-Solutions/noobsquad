from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    TEXT = "text"
    LINK = "link"
    IMAGE = "image"
    FILE = "file"

class MessageOut(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str | None
    file_url: str | None
    message_type: MessageType
    timestamp: datetime

    class Config:
        from_attributes = True

class ConversationOut(BaseModel):
    user_id: int
    username: str
    avatar: str | None = None
    last_message: str | None
    file_url: str | None
    message_type: MessageType
    timestamp: datetime
    is_sender: bool
    unread_count: int

    class Config:
        from_attributes = True