from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from database.session import Base


class CollaborationRequest(Base):
    __tablename__ = "collaboration_requests"

    id = Column(Integer, primary_key=True, index=True)
    research_id = Column(Integer, ForeignKey("research_collaborations.id"))
    requester_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)

    research = relationship("ResearchCollaboration", back_populates="collaboration_requests")
    requester = relationship("User", back_populates="sent_requests")


