from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session
from models.chat import Message
from core.dependencies import get_db
import json
from datetime import datetime,timezone
from pydantic import BaseModel
from typing import List
from api.v1.endpoints.auth import get_current_user

router = APIRouter()
clients = {}

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

                print(f"📨 {user_id} ➡ {receiver_id}: {content}")

                # ✅ Save message to database
                db_message = Message(
                    sender_id=user_id,
                    receiver_id=receiver_id,
                    content=content,
                    timestamp=datetime.now(timezone.utc)  # Add if your model includes timestamp
                )
                db.add(db_message)
                db.commit()

                # Prepare outgoing message
                msg_json = json.dumps({
                    "sender_id": user_id,
                    "receiver_id": receiver_id,
                    "content": content,
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


# ✅ Response schema
class MessageOut(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True

class ConversationOut(BaseModel):
    user_id: int
    username: str
    avatar: str | None = None
    last_message: str
    timestamp: datetime
    is_sender: bool
    unread_count: int
    class Config:
        from_attributes = True
        
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

        results.append({
            "user_id": friend.id,
            "username": friend.username,
            "avatar": friend.profile_picture,
            "last_message": msg.content,
            "timestamp": msg.timestamp,
            "is_sender": msg.sender_id == user_id,
            "unread_count": unread_count,
        })

    return results
