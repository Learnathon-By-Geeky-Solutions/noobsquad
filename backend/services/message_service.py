# services/message_service.py

from sqlalchemy.orm import Session
from models.chat import Message
from datetime import datetime, timezone

def create_message(db: Session, sender_id: int, receiver_id: int, content: str, file_url: str = None, message_type: str = "text") -> Message:
    message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content,
        file_url=file_url,
        message_type=message_type,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def prepare_message_event(message: Message) -> dict:
    return {
        "type": "message",
        "id": message.id,
        "sender_id": message.sender_id,
        "receiver_id": message.receiver_id,
        "content": message.content,
        "file_url": message.file_url,
        "message_type": message.message_type,
        "timestamp": message.timestamp.isoformat(),
        "is_read": message.is_read
    }
