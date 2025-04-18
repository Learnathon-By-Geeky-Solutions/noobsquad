from pydantic import BaseModel
from datetime import datetime


# Response model for a research paper
class ResearchPaperOut(BaseModel):
    id: int
    title: str
    author: str
    research_field: str
    file_path: str  # This can be renamed to something like `file_url` if needed
    created_at: datetime
    uploader_id: int
    original_filename: str

    class Config:
        from_attributes = True  # ORM compatibility
