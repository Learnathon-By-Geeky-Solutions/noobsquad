from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from database.session import Base
from sqlalchemy.orm import relationship

class Hashtag(Base):
    __tablename__ = "hashtags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    usage_count = Column(Integer, default=1)

    posts = relationship("Post", secondary="post_hashtags", back_populates="hashtags")


post_hashtags = Table(
"post_hashtags",
Base.metadata,
Column("post_id", ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
Column("hashtag_id", ForeignKey("hashtags.id", ondelete="CASCADE"), primary_key=True),
)