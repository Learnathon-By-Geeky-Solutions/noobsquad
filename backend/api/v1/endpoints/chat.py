# routers/chat_router.py

from fastapi import APIRouter, Depends, WebSocket, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from core.dependencies import get_db
from api.v1.endpoints.auth import get_current_user
from services.chat_service import fetch_conversations, fetch_chat_history
from services.websocket_service import connect_socket, disconnect_socket, handle_chat_message
from services.upload_service import validate_and_upload

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    await connect_socket(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            await handle_chat_message(db, user_id, data)
    except:
        await disconnect_socket(user_id)

@router.get("/chat/conversations")
async def get_conversations(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return await fetch_conversations(db, current_user.id)

@router.get("/chat/history/{friend_id}")
async def get_chat_history(friend_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return await fetch_chat_history(db, current_user.id, friend_id)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    return {"file_url": await validate_and_upload(file)}
