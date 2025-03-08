from pydantic import BaseModel
from typing import List, Optional
from fastapi import Form

# ✅ Base User Schema
class UserBase(BaseModel):
    username: str
    email: str

# ✅ Signup Schema (Minimal Fields)
class UserCreate(UserBase):
    password: str

# ✅ Profile Completion Schema (Handled Separately)
class ProfileCompletionRequest(BaseModel):
    university_name: str
    department: str
    fields_of_interest: List[str]  # Expecting a list

    @classmethod
    def as_form(
        cls, university_name: str = Form(...), department: str = Form(...), fields_of_interest: str = Form(...)
    ):
        fields_list = fields_of_interest.split(",") if fields_of_interest else []  # ✅ Safe split
        return cls(
            university_name=university_name,
            department=department,
            fields_of_interest=fields_list
        )

# ✅ Profile Picture Upload Schema
class ProfilePictureUpload(BaseModel):
    profile_picture: Optional[str]  # File path stored in DB

# ✅ User Response Schema (For Auth & Profile APIs)
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    profile_picture: Optional[str] = None
    university_name: Optional[str] = None
    department: Optional[str] = None
    fields_of_interest: List[str] = []  # Default empty list
    profile_completed: bool 

    class Config:
        from_attributes = True  # ✅ Correct for Pydantic v2

    @staticmethod
    def from_orm(user):  # ✅ Safe conversion for merged table
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            profile_picture=user.profile_picture,
            university_name=user.university_name,
            department=user.department,
            fields_of_interest=user.fields_of_interest.split(",") if user.fields_of_interest else [],
            profile_completed=user.profile_completed
        )
