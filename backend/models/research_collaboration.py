from sqlalchemy import Table, Column, Integer, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from database.session import Base

# Many-to-Many table for research collaborators
research_collaborators = Table(
    "research_collaborators",
    Base.metadata,
    Column("research_id", Integer, ForeignKey("research_collaborations.id")),
    Column("user_id", Integer, ForeignKey("users.id"))
)

class ResearchCollaboration(Base):
    __tablename__ = "research_collaborations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    research_field = Column(String, index=True)
    details = Column(Text)
    creator_id = Column(Integer, ForeignKey("users.id"))

    creator = relationship("User", back_populates="research_posts")
    collaboration_requests = relationship("CollaborationRequest", back_populates="research")
    collaborators = relationship("User", secondary=research_collaborators)  # Many-to-Many
