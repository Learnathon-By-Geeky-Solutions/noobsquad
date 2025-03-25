import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.dependencies import get_db
from core.connection_crud import send_request, accept_request, reject_request, get_connections
from schemas.connection import ConnectionCreate, ConnectionResponse
from api.v1.endpoints.auth import get_current_user  # Ensure authentication middleware is implemented
from models.user import User
from models.connection import Connection
from typing import Optional

router = APIRouter()

internal_error = "Internal Server Error"
@router.post("/connect/")
def send_connection(
    friend_data: ConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ✅ Fix: Use `User` model, not `dict`
):
    try:
        new_request = send_request(db, current_user.id, friend_data.friend_id)  # ✅ Fix: Use `current_user.id`
        return new_request
    except Exception as e:
        logging.error(f"Connection error: {e}")
        raise HTTPException(status_code=500, detail=internal_error) from e

@router.post("/accept/{request_id}")
def accept_connection(request_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    # Verify the connection belongs to the current user
    connection_check = db.query(Connection).filter_by(id=request_id).first()  # ✅ Corrected to query Connection table

    if not connection_check or (connection_check.user_id != current_user.id and connection_check.friend_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to accept this connection.")
    
    connection = accept_request(db, request_id)
    if not connection:
        raise HTTPException(status_code=404, detail="No pending request found.")
    
    return {"message": "Connection accepted!"}

@router.post("/reject/{request_id}")
def reject_connection(request_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    connection = reject_request(db, request_id)
    if not connection:
        raise HTTPException(status_code=404, detail="No pending request found.")
    return {"message": "Connection rejected!"}

@router.get("/connections")
def list_connections(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Fetch user connections."""
    try:
        return get_connections(db, current_user.id)  # ✅ Use `current_user.id`
    except Exception as e:
        logging.error(f"Error fetching connections: {str(e)}")
        raise HTTPException(status_code=500, detail=internal_error)

@router.get("/users")
def get_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Fetch users who are NOT friends with the current user, 
    who have NOT sent a friend request, and who have NOT received one from the user."""
    
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Fetch users who are already friends
        friends = db.query(Connection.friend_id).filter(Connection.user_id == current_user.id)

        # Fetch users who have been sent a request by the current user
        sent_requests = db.query(Connection.friend_id).filter(
            Connection.user_id == current_user.id, 
            Connection.status == "pending"
        )

        # Fetch users who have sent a request to the current user
        received_requests = db.query(Connection.user_id).filter(
            Connection.friend_id == current_user.id, 
            Connection.status == "pending"
        )

        # Get users who are not in any of the above lists
        users = db.query(User).filter(
            User.id.notin_(friends),
            User.id.notin_(sent_requests),
            User.id.notin_(received_requests),
            User.id != current_user.id  # Exclude self
        ).all()

        return users

    except Exception as e:
        logging.error(f"Error fetching users: {str(e)}")
        raise HTTPException(status_code=500, detail=internal_error)
   
@router.get("/pending-requests")
def get_pending_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Fetch all pending connection requests where the current user is the recipient."""
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Unauthorized")

        from core.connection_crud import get_pending_requests
        pending_requests = get_pending_requests(db, current_user.id)
        
        return pending_requests
    except Exception as e:
        logging.error(f"Error fetching pending requests: {str(e)}")
        raise HTTPException(status_code=500, detail=internal_error)
    
@router.get("/user/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Fetch a specific user by user_id."""
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Unauthorized")

        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
    except Exception as e:
        logging.error(f"Error fetching user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=internal_error)    

