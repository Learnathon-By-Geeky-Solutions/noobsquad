from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class ConnectionStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class ConnectionCreate(BaseModel):
    friend_id: int

class ConnectionResponse(BaseModel):
    id: int
    user_id: int
    friend_id: int
    status: ConnectionStatus
    created_at: datetime

    class Config:
        from_attributes = True

class ConnectionUserResponse(BaseModel):
    id: int
    username: str
    email: str
    profile_picture: str | None

    class Config:
        from_attributes = True

class ConnectionListResponse(BaseModel):
    connection_id: int
    friend_id: int
    username: str
    email: str
    profile_picture: str | None

    class Config:
        from_attributes = True

class PendingRequestResponse(BaseModel):
    request_id: int
    sender_id: int
    username: str
    email: str
    profile_picture: str | None

    class Config:
        from_attributes = True
