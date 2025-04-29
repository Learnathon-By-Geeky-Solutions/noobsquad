from typing import List, Dict
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.user import User
from models.connection import Connection, ConnectionStatus

class ConnectionHandler:
    @staticmethod
    def send_connection_request(db: Session, user_id: int, friend_id: int) -> Connection:
        """Send a connection request to another user."""
        if not db.query(User).filter(User.id == friend_id).first():
            raise HTTPException(status_code=404, detail="User not found")
            
        existing = db.query(Connection).filter(
            (Connection.user_id == user_id) & (Connection.friend_id == friend_id) |
            (Connection.user_id == friend_id) & (Connection.friend_id == user_id)
        ).first()
        
        if existing:
            if existing.status == ConnectionStatus.ACCEPTED:
                raise HTTPException(status_code=400, detail="Already connected")
            if existing.status == ConnectionStatus.PENDING:
                raise HTTPException(status_code=400, detail="Request already pending")
        
        new_request = Connection(
            user_id=user_id,
            friend_id=friend_id,
            status=ConnectionStatus.PENDING
        )
        db.add(new_request)
        db.commit()
        db.refresh(new_request)
        return new_request

    @staticmethod
    def accept_connection_request(db: Session, request_id: int, user_id: int) -> Dict[str, str]:
        """Accept a connection request."""
        connection = db.query(Connection).filter(Connection.id == request_id).first()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection request not found")
        if connection.friend_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to accept this request")
        if connection.status != ConnectionStatus.PENDING:
            raise HTTPException(status_code=400, detail="Request is not pending")
        
        connection.status = ConnectionStatus.ACCEPTED
        db.commit()
        return {"message": "Connection accepted!"}

    @staticmethod
    def reject_connection_request(db: Session, request_id: int, user_id: int) -> Dict[str, str]:
        """Reject a connection request."""
        connection = db.query(Connection).filter(Connection.id == request_id).first()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection request not found")
        if connection.friend_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to reject this request")
        if connection.status != ConnectionStatus.PENDING:
            raise HTTPException(status_code=400, detail="Request is not pending")
        
        connection.status = ConnectionStatus.REJECTED
        db.commit()
        return {"message": "Connection request rejected"}

    @staticmethod
    def get_user_connections(db: Session, user_id: int) -> List[Dict]:
        """Get all connections for a user."""
        connections = db.query(Connection).filter(
            (Connection.user_id == user_id) | (Connection.friend_id == user_id),
            Connection.status == ConnectionStatus.ACCEPTED
        ).all()
        
        return [
            {
                "connection_id": conn.id,
                "friend_id": conn.friend_id if conn.user_id == user_id else conn.user_id,
                "username": db.query(User).filter(User.id == conn.friend_id if conn.user_id == user_id else conn.user_id).first().username,
                "email": db.query(User).filter(User.id == conn.friend_id if conn.user_id == user_id else conn.user_id).first().email,
                "profile_picture": db.query(User).filter(User.id == conn.friend_id if conn.user_id == user_id else conn.user_id).first().profile_picture
            }
            for conn in connections
        ]

    @staticmethod
    def get_pending_requests(db: Session, user_id: int) -> List[Dict]:
        """Get pending connection requests for a user."""
        pending = db.query(Connection).filter(
            Connection.friend_id == user_id,
            Connection.status == ConnectionStatus.PENDING
        ).all()
        
        return [
            {
                "request_id": request.id,
                "sender_id": request.user_id,
                "username": db.query(User).filter(User.id == request.user_id).first().username,
                "email": db.query(User).filter(User.id == request.user_id).first().email,
                "profile_picture": db.query(User).filter(User.id == request.user_id).first().profile_picture
            }
            for request in pending
        ]

    @staticmethod
    def get_available_users(db: Session, current_user_id: int) -> List[Dict]:
        """Get users available for connection (users who are not already connected or have pending requests)."""
        # Get all users except the current user
        all_users = db.query(User).filter(User.id != current_user_id).all()
        
        # Get existing connections and pending requests
        existing_connections = db.query(Connection).filter(
            (Connection.user_id == current_user_id) | (Connection.friend_id == current_user_id)
        ).all()
        
        # Create a set of user IDs that are already connected or have pending requests
        excluded_user_ids = set()
        for conn in existing_connections:
            if conn.user_id == current_user_id:
                excluded_user_ids.add(conn.friend_id)
            else:
                excluded_user_ids.add(conn.user_id)
        
        # Filter out users who are already connected or have pending requests
        available_users = [user for user in all_users if user.id not in excluded_user_ids]
        
        return [
            {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "profile_picture": user.profile_picture
            }
            for user in available_users
        ]

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Dict:
        """Get a specific user by ID."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "profile_picture": user.profile_picture
        } 