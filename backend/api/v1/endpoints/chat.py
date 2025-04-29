import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Dict, List
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


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def prepare_message_for_json(message: dict) -> dict:
    """Helper function to ensure message data is JSON serializable"""
    if 'message_type' in message:
        # Convert message_type to string value
        message['message_type'] = (
            message['message_type'].value
            if hasattr(message['message_type'], 'value')
            else str(message['message_type'])
        )
    if 'timestamp' in message and isinstance(message['timestamp'], datetime):
        message['timestamp'] = message['timestamp'].isoformat()
    return message


async def send_websocket_message(client: WebSocket, message: dict):
    """Helper function to send WebSocket messages"""
    try:
        serializable_message = prepare_message_for_json(message)
        await client.send_text(json.dumps(serializable_message))
    except Exception as e:
        print(f"Failed to send WebSocket message: {str(e)}")


async def broadcast_conversation_update(db: Session, user_id: int, friend_id: int):
    """Send conversation updates to both participants"""
    last_msg = db.query(Message).filter(
        ((Message.sender_id == user_id) & (Message.receiver_id == friend_id)) |
        ((Message.sender_id == friend_id) & (Message.receiver_id == user_id))
    ).order_by(Message.timestamp.desc()).first()

    if not last_msg:
        return

    unread_count = db.query(func.count(Message.id)).filter(
        Message.sender_id == friend_id,
        Message.receiver_id == user_id,
        Message.is_read.is_(False)
    ).scalar()

    update = {
        "type": "conversation_update",
        "user_id": friend_id,
        "conversation": {
            "last_message": last_msg.content,
            "message_type": (
                last_msg.message_type.value
                if hasattr(last_msg.message_type, 'value')
                else str(last_msg.message_type)
            ),
            "timestamp": last_msg.timestamp.isoformat(),
            "is_sender": last_msg.sender_id == user_id,
            "unread_count": unread_count
        }
    }

    for uid in [user_id, friend_id]:
        if uid in clients:
            await send_websocket_message(clients[uid], update)


async def _validate_message(message_type: str, content: str) -> bool:
    """Validate message type and content"""
    if message_type not in SchemaMessageType._value2member_map_:
        print(f"❌ Invalid message type: {message_type}")
        return False
    
    if (message_type == SchemaMessageType.LINK.value and 
        content and not is_valid_url(content)):
        print(f"❌ Invalid URL: {content}")
        return False
    
    return True


async def _save_message_to_db(
    db: Session,
    user_id: int,
    receiver_id: int,
    content: str,
    file_url: str,
    message_type: str
) -> Message:
    """Save message to database and return the saved message"""
    db_message = Message(
        sender_id=user_id,
        receiver_id=receiver_id,
        content=content,
        file_url=file_url,
        message_type=message_type,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


async def _send_message_to_participants(user_id: int, receiver_id: int, msg_event: dict):
    """Send message to both participants"""
    send_tasks = []
    for uid in [user_id, receiver_id]:
        if uid in clients and clients[uid].client_state == WebSocketState.CONNECTED:
            send_tasks.append(send_websocket_message(clients[uid], msg_event))
    
    if send_tasks:
        await asyncio.gather(*send_tasks)


async def _handle_websocket_message(websocket: WebSocket, user_id: int, data: str, db: Session) -> bool:
    """Handle individual WebSocket messages"""
    try:
        message_data = json.loads(data)
        success = await handle_chat_message(user_id, message_data, db)
        if not success:
            error_event = {"type": "error", "message": "Failed to send message"}
            await send_websocket_message(websocket, error_event)
        return True
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON from user {user_id}: {data}")
    except Exception as e:
        print(f"❌ Error processing message: {str(e)}")
    return False


async def handle_chat_message(user_id: int, message_data: dict, db: Session):
    """Handle incoming chat messages"""
    try:
        receiver_id = int(message_data.get("receiver_id"))
        content = message_data.get("content")
        file_url = message_data.get("file_url", None)
        message_type = message_data.get("message_type", "text").lower()

        if not await _validate_message(message_type, content):
            return False

        db_message = await _save_message_to_db(
            db, user_id, receiver_id, content, file_url, message_type
        )

        msg_event = {
            "type": "message",
            "id": db_message.id,
            "sender_id": user_id,
            "receiver_id": receiver_id,
            "content": content,
            "file_url": file_url,
            "message_type": message_type,
            "timestamp": db_message.timestamp.isoformat(),
            "is_read": False
        }

        await _send_message_to_participants(user_id, receiver_id, msg_event)

        if receiver_id in clients and clients[receiver_id].client_state == WebSocketState.CONNECTED:
            new_msg_event = {
                "type": "new_message",
                "sender_id": user_id,
                "receiver_id": receiver_id
            }
            await send_websocket_message(clients[receiver_id], new_msg_event)

        await broadcast_conversation_update(db, user_id, receiver_id)
        return True

    except Exception as e:
        print(f"Error in handle_chat_message: {str(e)}")
        db.rollback()
        return False


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    await websocket.accept()
    clients[user_id] = websocket
    print(f"✅ WebSocket connected: user {user_id}")

    try:
        while True:
            data = await websocket.receive_text()
            await _handle_websocket_message(websocket, user_id, data, db)
    except WebSocketDisconnect:
        clients.pop(user_id, None)
        print(f"🔌 WebSocket disconnected: user {user_id}")
    except Exception as e:
        print(f"❌ Unexpected error in websocket_endpoint: {str(e)}")
        clients.pop(user_id, None)


async def _get_unread_count(db: Session, friend_id: int, user_id: int) -> int:
    """Get count of unread messages from a specific friend"""
    return db.query(func.count(Message.id)).filter(
        Message.sender_id == friend_id,
        Message.receiver_id == user_id,
        Message.is_read.is_(False)
    ).scalar()


async def _process_conversation(
    db: Session,
    msg: Message,
    user_id: int,
    processed_users: set
) -> dict:
    """Process a single conversation and return its details"""
    friend_id = msg.receiver_id if msg.sender_id == user_id else msg.sender_id
    
    if friend_id in processed_users:
        return None
        
    processed_users.add(friend_id)
    friend = db.query(User).filter(User.id == friend_id).first()
    if not friend:
        return None

    unread_count = await _get_unread_count(db, friend_id, user_id)
    message_type = (
        msg.message_type.value
        if hasattr(msg.message_type, 'value')
        else str(msg.message_type)
    )
    
    return {
        "user_id": friend.id,
        "username": friend.username,
        "avatar": friend.profile_picture,
        "last_message": msg.content,
        "file_url": msg.file_url,
        "message_type": message_type,
        "timestamp": msg.timestamp,
        "is_sender": msg.sender_id == user_id,
        "unread_count": unread_count,
    }


@router.get("/chat/conversations", response_model=List[ConversationOut])
async def get_conversations(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user.id
    results = []
    processed_users = set()

    conversations = db.query(Message).filter(
        (Message.sender_id == user_id) | (Message.receiver_id == user_id)
    ).order_by(Message.timestamp.desc()).all()

    for msg in conversations:
        conversation = await _process_conversation(db, msg, user_id, processed_users)
        if conversation:
            results.append(conversation)

    return results


async def _mark_messages_as_read(
    db: Session,
    friend_id: int,
    user_id: int,
    messages: List[Message]
) -> tuple:
    """Mark messages as read and return read count and last message id"""
    unread = db.query(Message).filter(
        Message.sender_id == friend_id,
        Message.receiver_id == user_id,
        Message.is_read.is_(False)
    )
    
    read_count = unread.count()
    if read_count > 0:
        unread.update({Message.is_read: True})
        db.commit()
        return read_count, messages[-1].id if messages else None
    return 0, None


@router.get("/chat/history/{friend_id}", response_model=List[MessageOut])
async def get_chat_history(
    friend_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user.id
    
    messages = db.query(Message).filter(
        ((Message.sender_id == user_id) & (Message.receiver_id == friend_id)) |
        ((Message.sender_id == friend_id) & (Message.receiver_id == user_id))
    ).order_by(Message.timestamp.asc()).all()

    read_count, last_read_id = await _mark_messages_as_read(db, friend_id, user_id, messages)
    
    if read_count > 0:
        if friend_id in clients:
            read_receipt = {
                "type": "read_receipt",
                "chat_id": user_id,
                "last_read_id": last_read_id,
                "read_count": read_count
            }
            await send_websocket_message(clients[friend_id], read_receipt)

        await broadcast_conversation_update(db, user_id, friend_id)

    return messages


# Set of allowed extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".docx"}


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
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