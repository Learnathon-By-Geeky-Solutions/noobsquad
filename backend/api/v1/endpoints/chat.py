import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketState

from api.v1.endpoints.auth import get_current_user
from core.dependencies import get_db
from models.chat import Message
from models.user import User
from schemas.chat import MessageOut, ConversationOut, MessageType as SchemaMessageType
from utils.cloudinary import upload_to_cloudinary


router = APIRouter()
clients: Dict[int, WebSocket] = {}


class WebSocketManager:
    @staticmethod
    async def connect(websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        clients[user_id] = websocket

    @staticmethod
    async def disconnect(user_id: int) -> None:
        clients.pop(user_id, None)

    @staticmethod
    async def send_message(websocket: WebSocket, message: dict) -> None:
        await websocket.send_json(message)

    @staticmethod
    async def broadcast(user_id: int, receiver_id: int, message: dict) -> None:
        for uid in [user_id, receiver_id]:
            if uid in clients:
                await WebSocketManager.send_message(clients[uid], message)


class MessageService:
    @staticmethod
    def create_message(
        db: Session,
        user_id: int,
        receiver_id: int,
        content: str,
        file_url: Optional[str] = None,
        message_type: str = "text"
    ) -> Message:
        message = Message(
            sender_id=user_id,
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

    @staticmethod
    def get_unread_count(db: Session, sender_id: int, receiver_id: int) -> int:
        return db.query(Message).filter(
            Message.sender_id == sender_id,
            Message.receiver_id == receiver_id,
            Message.is_read.is_(False)
        ).count()

    @staticmethod
    def mark_as_read(db: Session, sender_id: int, receiver_id: int) -> None:
        db.query(Message).filter(
            Message.sender_id == sender_id,
            Message.receiver_id == receiver_id,
            Message.is_read.is_(False)
        ).update({"is_read": True})
        db.commit()


class MessageValidator:
    @staticmethod
    def is_valid_url(url: str) -> bool:
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    @staticmethod
    def validate_message(message_type: str, content: str) -> bool:
        if message_type not in SchemaMessageType._value2member_map_:
            return False
        if message_type == SchemaMessageType.LINK.value and content and not MessageValidator.is_valid_url(content):
            return False
        return True


class ChatHandler:
    @staticmethod
    async def handle_message(user_id: int, message_data: dict, db: Session) -> bool:
        receiver_id = int(message_data.get("receiver_id"))
        content = message_data.get("content")
        file_url = message_data.get("file_url")
        message_type = message_data.get("message_type", "text").lower()

        if not MessageValidator.validate_message(message_type, content):
            return False

        message = MessageService.create_message(db, user_id, receiver_id, content, file_url, message_type)
        
        message_event = {
            "type": "message",
            "id": message.id,
            "sender_id": user_id,
            "receiver_id": receiver_id,
            "content": content,
            "file_url": file_url,
            "message_type": message_type,
            "timestamp": message.timestamp.isoformat(),
            "is_read": False
        }

        await WebSocketManager.broadcast(user_id, receiver_id, message_event)
        return True


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    await WebSocketManager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            await ChatHandler.handle_message(user_id, data, db)
    except WebSocketDisconnect:
        await WebSocketManager.disconnect(user_id)


@router.get("/chat/conversations", response_model=List[ConversationOut])
async def get_conversations(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    messages = db.query(Message).filter(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).order_by(Message.timestamp.desc()).all()
    
    conversations = {}
    for msg in messages:
        friend_id = msg.receiver_id if msg.sender_id == current_user.id else msg.sender_id
        if friend_id not in conversations:
            # Get friend's user info
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
                "is_sender": msg.sender_id == current_user.id,
                "unread_count": MessageService.get_unread_count(db, friend_id, current_user.id)
            }
    
    return list(conversations.values())


@router.get("/chat/history/{friend_id}", response_model=List[MessageOut])
async def get_chat_history(friend_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    messages = db.query(Message).filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == friend_id)) |
        ((Message.sender_id == friend_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp.asc()).all()
    
    MessageService.mark_as_read(db, friend_id, current_user.id)
    return messages


# Set of allowed extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".docx"}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        file_url = await upload_to_cloudinary(file)
        return {"file_url": file_url}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="File upload failed")