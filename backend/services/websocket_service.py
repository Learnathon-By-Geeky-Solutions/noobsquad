# services/websocket_service.py

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect
from typing import Dict
from services.message_service import create_message, prepare_message_event
from services.chat_service import fetch_chat_history
from models.chat import Message
from sqlalchemy.orm import Session

clients: Dict[int, WebSocket] = {}

async def connect_socket(websocket: WebSocket, user_id: int):
    await websocket.accept()
    clients[user_id] = websocket

async def disconnect_socket(user_id: int):
    clients.pop(user_id, None)

async def send_socket_message(user_id: int, message: dict):
    if user_id in clients:
        await clients[user_id].send_json(message)

async def broadcast_message(user_ids: list, message: dict):
    for uid in user_ids:
        await send_socket_message(uid, message)

async def handle_chat_message(db: Session, user_id: int, message_data: dict):
    from_id = user_id
    to_id = int(message_data.get("receiver_id"))
    content = message_data.get("content")
    file_url = message_data.get("file_url", None)
    message_type = message_data.get("message_type", "text")
    
    message = create_message(db, from_id, to_id, content, file_url, message_type)
    event = prepare_message_event(message)

    await broadcast_message([from_id, to_id], event)
