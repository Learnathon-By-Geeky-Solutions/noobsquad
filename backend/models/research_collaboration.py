from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from database.session import Base

class ResearchCollaboration(Base):
    __tablename__ = "research_collaborations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    research_field = Column(String, index=True)
    details = Column(Text)
    creator_id = Column(Integer, ForeignKey("users.id"))

    creator = relationship("User", back_populates="research_posts")
    collaboration_requests = relationship("CollaborationRequest", back_populates="research")


