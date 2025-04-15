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
