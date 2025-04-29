import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.dependencies import get_db
from schemas.connection import ConnectionCreate, ConnectionResponse
from api.v1.endpoints.auth import get_current_user  # Ensure authentication middleware is implemented
from models.user import User
from models.connection import Connection, ConnectionStatus
from sqlalchemy import select, or_, case
from services.ConnectionHandler import ConnectionHandler

router = APIRouter()
logger = logging.getLogger(__name__)

internal_error = "Internal Server Error"
@router.post("/connect/")
def send_connection(
    friend_data: ConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a connection request to another user."""
    return ConnectionHandler.send_connection_request(
        db=db,
        user_id=current_user.id,
        friend_id=friend_data.friend_id
    )

@router.post("/accept/{request_id}")
def accept_connection(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accept a connection request."""
    return ConnectionHandler.accept_connection_request(
        db=db,
        request_id=request_id,
        user_id=current_user.id
    )

@router.post("/reject/{request_id}")
def reject_connection(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reject a connection request."""
    return ConnectionHandler.reject_connection_request(
        db=db,
        request_id=request_id,
        user_id=current_user.id
    )

@router.get("/connections")
def list_connections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all connections for the current user."""
    return ConnectionHandler.get_user_connections(
        db=db,
        user_id=current_user.id
    )

@router.get("/users")
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get users available for connection."""
    return ConnectionHandler.get_available_users(
        db=db,
        current_user_id=current_user.id
    )

@router.get("/pending")
def get_pending_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get pending connection requests."""
    return ConnectionHandler.get_pending_requests(
        db=db,
        user_id=current_user.id
    )

@router.get("/user/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific user by ID."""
    return ConnectionHandler.get_user_by_id(
        db=db,
        user_id=user_id
    )

