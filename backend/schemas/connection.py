from pydantic import BaseModel
from enum import Enum

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
