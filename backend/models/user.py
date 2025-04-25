from sqlalchemy import Column, DateTime, Integer, String, Boolean
from database.session import Base
from sqlalchemy.orm import relationship
from datetime import timezone, datetime

CASCADE_DELETE_ORPHAN = "all, delete-orphan"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Tracks email verification status
    otp = Column(String, nullable=True)  # Stores the OTP temporarily
    otp_expiry = Column(DateTime(timezone=True), nullable=True)  # OTP expiry time with timezone awareness

    # ✅ Merged fields from UserProfile
    profile_picture = Column(String, nullable=True)  # Image URL
    university_name = Column(String, nullable=True)
    department = Column(String, nullable=True)
    fields_of_interest = Column(String, nullable=True)  # Comma-separated values
    profile_completed = Column(Boolean, default=False)  # To check completion

    papers = relationship("ResearchPaper", back_populates="uploader")
    research_posts = relationship("ResearchCollaboration", back_populates="creator")
    sent_requests = relationship("CollaborationRequest", back_populates="requester")
    

    posts = relationship("Post", back_populates="user", cascade=CASCADE_DELETE_ORPHAN)
    events = relationship("Event", back_populates="user", cascade=CASCADE_DELETE_ORPHAN)  # ✅ Fixed
    comments = relationship("Comment", back_populates="user", cascade=CASCADE_DELETE_ORPHAN)  # ✅ Added
    likes = relationship("Like", back_populates="user", cascade=CASCADE_DELETE_ORPHAN)  # ✅ Added
    shares = relationship("Share", back_populates="user", cascade=CASCADE_DELETE_ORPHAN)  # ✅ Added
    event_attendance = relationship("EventAttendee", back_populates="user", cascade=CASCADE_DELETE_ORPHAN)

    messages_sent = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id", cascade= CASCADE_DELETE_ORPHAN)
    messages_received = relationship("Message", back_populates="receiver", foreign_keys="Message.receiver_id", cascade= CASCADE_DELETE_ORPHAN)

    received_notifications = relationship("Notification", foreign_keys="Notification.user_id", back_populates="user")
    sent_notifications = relationship("Notification", foreign_keys="Notification.actor_id", back_populates="actor")





