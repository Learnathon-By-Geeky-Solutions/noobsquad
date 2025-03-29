from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from database.session import Base
import enum

class RequestStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

class CollaborationRequest(Base):
    __tablename__ = "collaboration_requests"

    id = Column(Integer, primary_key=True, index=True)
    research_id = Column(Integer, ForeignKey("research_collaborations.id"))
    requester_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)
    status = Column(Enum(RequestStatus), default=RequestStatus.pending)  # Track request status

    research = relationship("ResearchCollaboration", back_populates="collaboration_requests")
    requester = relationship("User", back_populates="sent_requests")