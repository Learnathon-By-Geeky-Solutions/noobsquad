# backend/chat/routes.py
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from chats.manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def chat_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Assume data includes recipient_id and message
            # Parse and route message here
            message_data = json.loads(data)
            receiver_id = message_data.get("recipient_id")
            message = message_data.get("message")
            await manager.send_personal_message(message, receiver_id)
    except WebSocketDisconnect:
        manager.disconnect(user_id)
