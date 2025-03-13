from sqlalchemy import Column, Integer, String, Boolean
from database.session import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    # ✅ Merged fields from UserProfile
    profile_picture = Column(String, nullable=True)  # Image URL
    university_name = Column(String, nullable=True)
    department = Column(String, nullable=True)
    fields_of_interest = Column(String, nullable=True)  # Comma-separated values
    profile_completed = Column(Boolean, default=False)  # To check completion
    papers = relationship("ResearchPaper", back_populates="uploader")
    research_posts = relationship("ResearchCollaboration", back_populates="creator")
    sent_requests = relationship("CollaborationRequest", back_populates="requester")