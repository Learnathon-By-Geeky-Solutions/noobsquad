from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Boolean
from sqlalchemy.sql.sqltypes import Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database.session import Base
import enum

class MessageType(enum.Enum):
    text = "text"
    link = "link"
    image = "image"
    file = "file"

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=True)  # Allow null for image/file messages
    file_url = Column(String, nullable=True)
    message_type = Column(Enum(MessageType, native_enum=False), default=MessageType.text)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_read = Column(Boolean, default=False)

    sender = relationship("User", foreign_keys=[sender_id], back_populates="messages_sent")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="messages_received")