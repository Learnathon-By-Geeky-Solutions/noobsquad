from pydantic import BaseModel
from typing import Optional
from enum import Enum

class AttendeeStatus(str, Enum):
    going = "going"
    interested = "interested"
    not_going = "not going"

class EventAttendeeCreate(BaseModel):
    event_id: int
    status: AttendeeStatus

class EventAttendeeResponse(BaseModel):
    id: int
    event_id: int
    user_id: int
    status: AttendeeStatus

    class Config:
        from_attributes = True
