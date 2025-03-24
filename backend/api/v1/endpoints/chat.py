from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from models.chat import Chat, ChatUser, Message
from models.user import User
from database.session import SessionLocal
from api.v1.endpoints.auth import get_current_user
from core.dependencies import get_db
from sqlalchemy import func
import json

router = APIRouter()

# WebSocket clients dictionary to store active WebSocket connections
clients = {}

# =====================================
# Pydantic Schemas for Request/Response
# =====================================



# =====================
#        ENDPOINTS
# =====================

# WebSocket real-time messaging endpoint
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    clients[user_id] = websocket
    print(f"✅ WebSocket connected: user {user_id}")

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message_data = json.loads(data)
                receiver_id = int(message_data.get("receiver_id"))
                content = message_data.get("content")

                print(f"📨 {user_id} ➡ {receiver_id}: {content}")

                if receiver_id in clients:
                    await clients[receiver_id].send_text(json.dumps({
                        "sender_id": user_id,
                        "receiver_id": receiver_id,
                        "content": content,
                    }))
                if user_id in clients:
                    await clients[user_id].send_text(json.dumps({
                        "sender_id": user_id,
                        "receiver_id": receiver_id,
                        "content": content,
                    }))
                else:
                    print(f"⚠️ Receiver {receiver_id} not connected.")

            except json.JSONDecodeError:
                print(f"❌ Invalid JSON from {user_id}: {data}")

    except WebSocketDisconnect:
        clients.pop(user_id, None)
        print(f"🔌 User {user_id} disconnected")