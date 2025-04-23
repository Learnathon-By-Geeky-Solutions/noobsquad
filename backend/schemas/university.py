from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

class Member(BaseModel):
    username: str
    email: str

class UniversityPost(BaseModel):
    id: int
    content: str
    author: str
    created_at: datetime

class UniversityPage(BaseModel):
    university: str
    total_members: int
    departments: Dict[str, List[Member]]
    post_ids: List[int]

class UniversityListResponse(BaseModel):
    id: int
    name: str
    departments: List[str]
    has_more_departments: bool

class UniversityResponse(BaseModel):
    id: int
    name: str
    departments: List[str]
    total_members: int
    class Config:
        from_attributes = True