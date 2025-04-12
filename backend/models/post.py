from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Date, Text, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from database.session import Base
from datetime import datetime, timezone
import enum
from sqlalchemy.sql import func
from zoneinfo import ZoneInfo


USER_ID_FOREIGN_KEY = "users.id"
CASCADE_DELETE_ORPHAN = "all, delete-orphan"
POSTS_ID_FOREIGN_KEY = "posts.id"

# Enum for different post types
class PostTypeEnum(str, enum.Enum):
    TEXT = "text"
    MEDIA = "media"
    DOCUMENT = "document"
    EVENT = "event"

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(USER_ID_FOREIGN_KEY), nullable=False)  # ✅ Ensures every post has a user
    content = Column(Text, nullable=True)  # Stores text content (if any)
    post_type = Column(Enum(PostTypeEnum), default=PostTypeEnum.TEXT)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    like_count = Column(Integer, default=0)
   

    # Relationships
    user = relationship("User", back_populates="posts")  # ✅ Added
    media = relationship("PostMedia", back_populates="post", cascade=CASCADE_DELETE_ORPHAN)
    documents = relationship("PostDocument", back_populates="post", cascade=CASCADE_DELETE_ORPHAN)
    event = relationship("Event", back_populates="post", uselist=False, cascade=CASCADE_DELETE_ORPHAN)  # ✅ Fixed
    likes = relationship("Like", back_populates="post", cascade=CASCADE_DELETE_ORPHAN)
    comments = relationship("Comment", back_populates="post", cascade=CASCADE_DELETE_ORPHAN)
    shares = relationship("Share", back_populates="post", cascade=CASCADE_DELETE_ORPHAN)

    notifications = relationship("Notification", back_populates="post", cascade="all, delete-orphan")
   
class PostMedia(Base):
    __tablename__ = "post_media"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey(POSTS_ID_FOREIGN_KEY, ondelete="CASCADE"), nullable=False)
    media_url = Column(String, nullable=False)  # Stores file path
    media_type = Column(String, nullable=False)  # Image or Video

    post = relationship("Post", back_populates="media")

class PostDocument(Base):
    __tablename__ = "post_documents"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey(POSTS_ID_FOREIGN_KEY, ondelete="CASCADE"), nullable=False)
    document_url = Column(String, nullable=False)  # Stores file path
    document_type = Column(String, nullable=False)  # PDF, DOCX, etc.

    post = relationship("Post", back_populates="documents")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey(POSTS_ID_FOREIGN_KEY, ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey(USER_ID_FOREIGN_KEY), nullable=False)  # ✅ Tracks who created the event
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    event_datetime = Column(DateTime, nullable=False) 
    location = Column(String, nullable=True)
    image_url = Column(String, nullable=True)

    post = relationship("Post", back_populates="event")
    user = relationship("User", back_populates="events")  # ✅ Tracks creator
    attendees = relationship("EventAttendee", back_populates="event", cascade=CASCADE_DELETE_ORPHAN)

class EventAttendee(Base):
    __tablename__ = "event_attendees"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey(USER_ID_FOREIGN_KEY), nullable=False)
    status = Column(Enum("going", "interested", "not going", name="attendee_status_enum"), nullable=False)

    event = relationship("Event", back_populates="attendees")
    user = relationship("User", back_populates="event_attendance")

    __table_args__ = (UniqueConstraint("event_id", "user_id", name="unique_event_attendance"),)

class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(USER_ID_FOREIGN_KEY), nullable=False)
    post_id = Column(Integer, ForeignKey(POSTS_ID_FOREIGN_KEY), nullable=True)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now(ZoneInfo("UTC")))

    __table_args__ = (
        CheckConstraint(
            "(post_id IS NOT NULL AND comment_id IS NULL) OR (post_id IS NULL AND comment_id IS NOT NULL)",
            name="check_like_target"
        ),
    )

    user = relationship("User", back_populates="likes")
    post = relationship("Post", back_populates="likes")
    comment = relationship("Comment", back_populates="likes")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(USER_ID_FOREIGN_KEY), nullable=False)
    post_id = Column(Integer, ForeignKey(POSTS_ID_FOREIGN_KEY), nullable=True)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)  # For replies
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    like_count = Column(Integer, default=0)

    user = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], back_populates="replies")
    replies = relationship("Comment", back_populates="parent", cascade="all, delete")
    likes = relationship("Like", back_populates="comment", cascade="all, delete")

class Share(Base):
    __tablename__ = "shares"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(USER_ID_FOREIGN_KEY), nullable=False)
    post_id = Column(Integer, ForeignKey(POSTS_ID_FOREIGN_KEY), nullable=False)
    share_token = Column(String, unique=True, nullable=False)  # Add this line
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="shares")
    post = relationship("Post", back_populates="shares")