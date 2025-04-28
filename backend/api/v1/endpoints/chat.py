import os
import uuid
import secrets
from urllib.parse import urlparse
from fastapi import APIRouter, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session
from models.chat import Message
from models.user import User
from core.dependencies import get_db
from api.v1.endpoints.auth import get_current_user
from utils.cloudinary import upload_to_cloudinary
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from schemas.chat import MessageOut, ConversationOut, MessageType as SchemaMessageType
from pathlib import Path

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
        message['message_type'] = message['message_type'].value if hasattr(message['message_type'], 'value') else str(message['message_type'])
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
    # Get last message between users
    last_msg = db.query(Message).filter(
        ((Message.sender_id == user_id) & (Message.receiver_id == friend_id)) |
        ((Message.sender_id == friend_id) & (Message.receiver_id == user_id))
    ).order_by(Message.timestamp.desc()).first()

    if not last_msg:
        return

    # Get unread count
    unread_count = db.query(func.count(Message.id)).filter(
        Message.sender_id == friend_id,
        Message.receiver_id == user_id,
        Message.is_read == False
    ).scalar()

    # Prepare conversation update
    update = {
        "type": "conversation_update",
        "user_id": friend_id,
        "conversation": {
            "last_message": last_msg.content,
            "message_type": last_msg.message_type.value if hasattr(last_msg.message_type, 'value') else str(last_msg.message_type),
            "timestamp": last_msg.timestamp.isoformat(),
            "is_sender": last_msg.sender_id == user_id,
            "unread_count": unread_count
        }
    }

    # Send to both users
    for uid in [user_id, friend_id]:
        if uid in clients:
            await send_websocket_message(clients[uid], update)

async def handle_chat_message(user_id: int, message_data: dict, db: Session):
    """Handle incoming chat messages"""
    receiver_id = int(message_data.get("receiver_id"))
    content = message_data.get("content")
    file_url = message_data.get("file_url", None)
    message_type = message_data.get("message_type", "text").lower()

    # Validate message type using schema enum
    if message_type not in SchemaMessageType._value2member_map_:
        print(f"❌ Invalid message type: {message_type}")
        return

    if message_type == SchemaMessageType.LINK.value and content and not is_valid_url(content):
        print(f"❌ Invalid URL: {content}")
        return

    # Save message to database
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

    # Prepare message event
    msg_event = {
        "type": "message",
        "id": db_message.id,
        "sender_id": user_id,
        "receiver_id": receiver_id,
        "content": content,
        "file_url": file_url,
        "message_type": message_type,
        "timestamp": db_message.timestamp.isoformat()
    }

    # Send message to both users
    for uid in [user_id, receiver_id]:
        if uid in clients:
            await send_websocket_message(clients[uid], msg_event)

    # Send new message notification
    if receiver_id in clients:
        new_msg_event = {
            "type": "new_message",
            "sender_id": user_id,
            "receiver_id": receiver_id
        }
        await send_websocket_message(clients[receiver_id], new_msg_event)

    # Update conversations
    await broadcast_conversation_update(db, user_id, receiver_id)

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    await websocket.accept()
    clients[user_id] = websocket
    print(f"✅ WebSocket connected: user {user_id}")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                await handle_chat_message(user_id, message_data, db)
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON from user {user_id}: {data}")
            except Exception as e:
                print(f"❌ Error processing message: {str(e)}")
    except WebSocketDisconnect:
        clients.pop(user_id, None)
        print(f"🔌 WebSocket disconnected: user {user_id}")

@router.get("/chat/history/{friend_id}", response_model=List[MessageOut])
async def get_chat_history(friend_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    user_id = current_user.id
    
    # Get chat history
    messages = db.query(Message).filter(
        ((Message.sender_id == user_id) & (Message.receiver_id == friend_id)) |
        ((Message.sender_id == friend_id) & (Message.receiver_id == user_id))
    ).order_by(Message.timestamp.asc()).all()

    # Mark messages as read
    unread = db.query(Message).filter(
        Message.sender_id == friend_id,
        Message.receiver_id == user_id,
        Message.is_read == False
    )
    
    if unread.count() > 0:
        read_count = unread.count()
        unread.update({Message.is_read: True})
        db.commit()

        # Send read receipt via WebSocket
        if friend_id in clients:
            read_receipt = {
                "type": "read_receipt",
                "chat_id": user_id,
                "last_read_id": messages[-1].id if messages else None,
                "read_count": read_count
            }
            await send_websocket_message(clients[friend_id], read_receipt)

        # Update conversations after marking messages as read
        await broadcast_conversation_update(db, user_id, friend_id)

    return messages

@router.get("/chat/conversations", response_model=List[ConversationOut])
async def get_conversations(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    user_id = current_user.id
    results = []

    # Get all conversations with last message
    conversations = db.query(Message).filter(
        (Message.sender_id == user_id) | (Message.receiver_id == user_id)
    ).order_by(Message.timestamp.desc()).all()

    processed_users = set()
    
    for msg in conversations:
        friend_id = msg.receiver_id if msg.sender_id == user_id else msg.sender_id
        
        if friend_id in processed_users:
            continue
            
        processed_users.add(friend_id)
        
        # Get friend details
        friend = db.query(User).filter(User.id == friend_id).first()
        if not friend:
            continue

        # Get unread count
        unread_count = db.query(func.count(Message.id)).filter(
            Message.sender_id == friend_id,
            Message.receiver_id == user_id,
            Message.is_read == False
        ).scalar()

        message_type = msg.message_type.value if hasattr(msg.message_type, 'value') else str(msg.message_type)
        
        results.append({
            "user_id": friend.id,
            "username": friend.username,
            "avatar": friend.profile_picture,
            "last_message": msg.content,
            "file_url": msg.file_url,
            "message_type": message_type,
            "timestamp": msg.timestamp,
            "is_sender": msg.sender_id == user_id,
            "unread_count": unread_count,
        })

    return results

# Set of allowed extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".docx"}

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        # Validate the extension
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Upload to Cloudinary
        upload_result = upload_to_cloudinary(
            file.file,
            folder_name="noobsquad/chat_uploads"
        )

        secure_url = upload_result["secure_url"]
        
        return JSONResponse(content={"file_url": secure_url})
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="File upload failed")