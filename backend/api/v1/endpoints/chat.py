import os
import uuid
from urllib.parse import urlparse
from fastapi import APIRouter, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session
from models.chat import Message
from core.dependencies import get_db
import json
from datetime import datetime,timezone
from pydantic import BaseModel
from typing import List
from api.v1.endpoints.auth import get_current_user
from schemas.chat import MessageOut, ConversationOut, MessageType
from fastapi.staticfiles import StaticFiles

router = APIRouter()
clients = {}

def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])  # Must have scheme (http/https) and domain
    except:
        return False
    
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    await websocket.accept()
    clients[user_id] = websocket
    print(f"✅ WebSocket connected: user {user_id}")

    try:
        while True:
            data = await websocket.receive_text()

            try:
                # Parse incoming message
                message_data = json.loads(data)
                receiver_id = int(message_data.get("receiver_id"))
                content = message_data.get("content")
                file_url = message_data.get("file_url")  # Optional
                message_type = message_data.get("message_type", "text").lower() # Default to text

                                # Validate message type
                if message_type not in [mt.value for mt in MessageType]:
                    print(f"❌ Invalid message type: {message_type}")
                    continue

                # Validate link if message_type is link
                if message_type == "link" and content and not is_valid_url(content):
                    print(f"❌ Invalid URL: {content}")

                # ✅ Save message to database
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

                # Prepare outgoing message
                msg_json = json.dumps({
                    "sender_id": user_id,
                    "receiver_id": receiver_id,
                    "content": content,
                    "file_url": file_url,
                    "message_type": message_type,
                    "timestamp": db_message.timestamp.isoformat()
                })

                # ✅ Send to both sender and receiver
                for uid in [user_id, receiver_id]:
                    if uid in clients:
                        await clients[uid].send_text(msg_json)
                    else:
                        print(f"⚠️ User {uid} not connected")

            except json.JSONDecodeError:
                print(f"❌ Invalid JSON from user {user_id}: {data}")

    except WebSocketDisconnect:
        clients.pop(user_id, None)
        print(f"🔌 WebSocket disconnected: user {user_id}")

        
@router.get("/chat/history/{friend_id}", response_model=List[MessageOut])
def get_chat_history(friend_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    user_id = current_user.id

    # ✅ Step 1: Get all messages between current user and friend
    messages = db.query(Message).filter(
        ((Message.sender_id == user_id) & (Message.receiver_id == friend_id)) |
        ((Message.sender_id == friend_id) & (Message.receiver_id == user_id))
    ).order_by(Message.timestamp.asc()).all()

    # ✅ Step 2: Mark friend's messages to current user as read
    db.query(Message).filter(
        Message.sender_id == friend_id,
        Message.receiver_id == user_id,
        Message.is_read == False
    ).update({Message.is_read: True})

    db.commit()  # 💾 Save changes

    return messages


from sqlalchemy.orm import joinedload

@router.get("/chat/conversations", response_model=List[ConversationOut])
def get_conversations(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    user_id = current_user.id

    # Step 1: Get all latest messages for each conversation
    subquery = db.query(
        func.max(Message.id).label("latest_id")
    ).filter(
        or_(
            Message.sender_id == user_id,
            Message.receiver_id == user_id
        )
    ).group_by(
        func.least(Message.sender_id, Message.receiver_id),
        func.greatest(Message.sender_id, Message.receiver_id)
    ).subquery()

    # ✅ Eager-load sender and receiver user objects
    latest_messages = db.query(Message).options(
        joinedload(Message.sender),
        joinedload(Message.receiver)
    ).join(
        subquery, Message.id == subquery.c.latest_id
    ).order_by(desc(Message.timestamp)).all()

    results = []
    for msg in latest_messages:
        friend = msg.receiver if msg.sender_id == user_id else msg.sender
        other_user_id = friend.id

        # ✅ Get unread message count from that friend
        unread_count = db.query(func.count(Message.id)).filter(
            Message.sender_id == other_user_id,
            Message.receiver_id == user_id,
            Message.is_read == False
        ).scalar()
        # Normalize message_type to lowercase for consistency
        message_type = msg.message_type.lower() if isinstance(msg.message_type, str) else msg.message_type.value.lower()
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

# Create a secure file manager for chat uploads
class SecureFileManager:
    def __init__(self, directory):
        # Ensure the directory is absolute
        self.base_directory = os.path.abspath(directory)
        # Create the directory if it doesn't exist
        os.makedirs(self.base_directory, exist_ok=True)
    
    def save_file(self, file_content, extension):
        """
        Securely saves a file with a random name and the specified extension
        within the base directory.
        
        Returns the filename (not the full path) if successful
        """
        # Validate the extension (though this should be already validated)
        if not extension.startswith('.'):
            extension = '.' + extension
            
        # Generate a unique filename
        filename = f"{uuid.uuid4().hex}{extension}"
        
        # Create the full path (this is safe because we control both parts)
        file_path = os.path.join(self.base_directory, filename)
        
        # Verify the path is within the base directory (safety check)
        if not os.path.abspath(file_path).startswith(self.base_directory):
            return None
            
        # Write the file
        with open(file_path, "wb") as f:
            f.write(file_content)
            
        return filename

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        # Validate file type
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".docx"}
        # Get extension but only use it for validation
        original_ext = os.path.splitext(file.filename)[1].lower()
        if original_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Create a secure file manager for our uploads directory
        file_manager = SecureFileManager("uploads/chat")
        
        # Read file content fully before saving
        file_content = await file.read()
        
        # Use the file manager to save the file securely
        filename = file_manager.save_file(file_content, original_ext)
        
        if not filename:
            raise HTTPException(status_code=500, detail="Failed to save file securely")

        # Generate file URL (relative path)
        file_url = f"/uploads/chat/{filename}"

        return JSONResponse(content={"file_url": file_url})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")