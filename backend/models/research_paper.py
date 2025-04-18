from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database.session import Base
from datetime import datetime, timezone

class ResearchPaper(Base):
    __tablename__ = "research_papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    research_field = Column(String, index=True)
    file_path = Column(Text)
    uploader_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    original_filename = Column(String, index=True)

    uploader = relationship("User", back_populates="papers")

