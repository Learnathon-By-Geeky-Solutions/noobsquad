from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, DateTime
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from database import Base
from zoneinfo import ZoneInfo

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Receiver
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Action performer
    type = Column(String, nullable=False)  # "like", "comment", "share", "follow"
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)  # Optional post reference
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="received_notifications")  # Receiver
    actor = relationship("User", foreign_keys=[actor_id], back_populates="sent_notifications")  # Action performer
    post = relationship("Post", foreign_keys=[post_id], lazy="joined", back_populates="notifications")  # Related post (if applicable)