# services/chat_service.py

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from models.chat import Message
from models.user import User
from typing import List

async def fetch_conversations(db: Session, user_id: int) -> List[dict]:
    messages = db.query(Message).filter(
        or_(
            Message.sender_id == user_id,
            Message.receiver_id == user_id
        )
    ).order_by(Message.timestamp.desc()).all()
    
    conversations = {}
    for msg in messages:
        friend_id = msg.receiver_id if msg.sender_id == user_id else msg.sender_id
        if friend_id not in conversations:
            friend = db.query(User).filter(User.id == friend_id).first()
            if not friend:
                continue
            conversations[friend_id] = {
                "user_id": friend_id,
                "username": friend.username,
                "avatar": friend.profile_picture,
                "last_message": msg.content,
                "file_url": msg.file_url,
                "message_type": msg.message_type,
                "timestamp": msg.timestamp,
                "is_sender": msg.sender_id == user_id,
                "unread_count": get_unread_count(db, friend_id, user_id)
            }
    return list(conversations.values())

async def fetch_chat_history(db: Session, user_id: int, friend_id: int) -> List[dict]:
    messages = db.query(Message).filter(
        or_(
            and_(Message.sender_id == user_id, Message.receiver_id == friend_id),
            and_(Message.sender_id == friend_id, Message.receiver_id == user_id)
        )
    ).order_by(Message.timestamp.asc()).all()
    
    mark_as_read(db, friend_id, user_id)
    return messages

def get_unread_count(db: Session, sender_id: int, receiver_id: int) -> int:
    return db.query(Message).filter(
        Message.sender_id == sender_id,
        Message.receiver_id == receiver_id,
        Message.is_read.is_(False)
    ).count()

def mark_as_read(db: Session, sender_id: int, receiver_id: int) -> None:
    db.query(Message).filter(
        Message.sender_id == sender_id,
        Message.receiver_id == receiver_id,
        Message.is_read.is_(False)
    ).update({"is_read": True})
    db.commit()
