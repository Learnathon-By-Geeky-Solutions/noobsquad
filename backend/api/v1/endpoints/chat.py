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

router = APIRouter()

# WebSocket clients dictionary to store active WebSocket connections
clients = {}

# =====================================
# Pydantic Schemas for Request/Response
# =====================================

class MessageCreate(BaseModel):
    content: str

class MessageRead(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    content: str
    is_read: bool

    class Config:
        from_attributes = True

class ChatRead(BaseModel):
    id: int
    is_group: bool  # We will set this to False for one-on-one chats

    class Config:
        orm_mode = True


# =====================
#        ENDPOINTS
# =====================

@router.post("/{receiver_user_id}/send", response_model=MessageRead)
async def send_message(
    receiver_user_id: int,  # The user you are sending the message to
    msg_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a message to the specified user, by finding or creating a one-on-one chat.
    """
    # Ensure you're not sending a message to yourself
    if receiver_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Cannot send a message to yourself."
        )

    # Check if a chat already exists between the current user and the receiver
    existing_chat = (
        db.query(Chat)
        .join(ChatUser)
        .filter(ChatUser.user_id.in_([current_user.id, receiver_user_id]))
        .group_by(Chat.id)
        .having(func.count(ChatUser.user_id) == 2)  # Only two users allowed in a chat
        .first()
    )

    # If no chat exists, create a new one
    if not existing_chat:
        new_chat = Chat(is_group=False)  # is_group is False for one-on-one chat
        db.add(new_chat)
        db.commit()
        db.refresh(new_chat)

        # Add both users to the new chat
        db.add_all([
            ChatUser(chat_id=new_chat.id, user_id=current_user.id),
            ChatUser(chat_id=new_chat.id, user_id=receiver_user_id),
        ])
        db.commit()

        chat_to_use = new_chat
    else:
        chat_to_use = existing_chat

    # Create the message and store it in the selected chat
    new_msg = Message(
        chat_id=chat_to_use.id,
        sender_id=current_user.id,
        content=msg_data.content
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)

    # If the receiver is online (connected via WebSocket), send the message in real time
    if receiver_user_id in clients:
        await clients[receiver_user_id].send_text(f"New message from {current_user.username}: {msg_data.content}")

    return new_msg


@router.get("/messages/{user_id}", response_model=List[MessageRead])
def get_chat_messages(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve messages between the current user and the specified user (by user_id).
    """
    # Ensure you're not trying to get messages with yourself
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot get messages with yourself."
        )

    # Find the chat_id where both the current_user and the user_id are part of
    chat = db.query(Chat).join(ChatUser).filter(
        ChatUser.user_id.in_([current_user.id, user_id])
    ).group_by(Chat.id).having(func.count(ChatUser.user_id) == 2).first()

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found between these users."
        )

    # Get the messages for this chat
    messages = db.query(Message).filter(Message.chat_id == chat.id).order_by(Message.timestamp.asc()).all()
    return messages


# WebSocket real-time messaging endpoint
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    Real-time messaging: allows users to connect to the WebSocket to send and receive messages.
    """
    await websocket.accept()
    clients[user_id] = websocket  # Store the connection

    try:
        while True:
            data = await websocket.receive_text()
            # In this example, we simply echo back the message for now
            # This can be enhanced to handle messaging logic
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        del clients[user_id]  # Remove the connection when the user disconnects
        print(f"User {user_id} disconnected")
