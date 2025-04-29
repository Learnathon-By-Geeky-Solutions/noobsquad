from typing import List, Dict
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.user import User
from models.connection import Connection, ConnectionStatus

class ConnectionService:
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """Fetch user by ID, or raise HTTPException if not found."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    @staticmethod
    def check_existing_connection(db: Session, user_id: int, friend_id: int) -> Connection:
        """Check if an existing connection exists between two users."""
        return db.query(Connection).filter(
            ((Connection.user_id == user_id) & (Connection.friend_id == friend_id)) |
            ((Connection.user_id == friend_id) & (Connection.friend_id == user_id))
        ).first()

    @staticmethod
    def get_user_connections(db: Session, user_id: int) -> List[Dict]:
        """Get all accepted connections for a user."""
        connections = db.query(Connection).filter(
            (Connection.user_id == user_id) | (Connection.friend_id == user_id),
            Connection.status == ConnectionStatus.ACCEPTED
        ).all()

        return [
            {
                "connection_id": conn.id,
                "friend_id": conn.friend_id if conn.user_id == user_id else conn.user_id,
                "username": ConnectionService.get_user_by_id(db, conn.friend_id if conn.user_id == user_id else conn.user_id).username,
                "email": ConnectionService.get_user_by_id(db, conn.friend_id if conn.user_id == user_id else conn.user_id).email,
                "profile_picture": ConnectionService.get_user_by_id(db, conn.friend_id if conn.user_id == user_id else conn.user_id).profile_picture
            }
            for conn in connections
        ]

    @staticmethod
    def get_pending_requests(db: Session, user_id: int) -> List[Dict]:
        """Get all pending connection requests for a user."""
        pending = db.query(Connection).filter(
            Connection.friend_id == user_id,
            Connection.status == ConnectionStatus.PENDING
        ).all()

        return [
            {
                "request_id": request.id,
                "sender_id": request.user_id,
                "username": ConnectionService.get_user_by_id(db, request.user_id).username,
                "email": ConnectionService.get_user_by_id(db, request.user_id).email,
                "profile_picture": ConnectionService.get_user_by_id(db, request.user_id).profile_picture
            }
            for request in pending
        ]

    @staticmethod
    def get_available_users(db: Session, current_user_id: int) -> List[Dict]:
        """Get users who are available for connection (not already connected or have pending requests)."""
        all_users = db.query(User).filter(User.id != current_user_id).all()

        # Fetch existing connections and pending requests
        existing_connections = db.query(Connection).filter(
            (Connection.user_id == current_user_id) | (Connection.friend_id == current_user_id)
        ).all()

        excluded_user_ids = {conn.friend_id if conn.user_id == current_user_id else conn.user_id for conn in existing_connections}

        # Filter available users
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


class ConnectionHandler:
    @staticmethod
    def send_connection_request(db: Session, user_id: int, friend_id: int) -> Connection:
        """Send a connection request to another user."""
        # Check if the user to connect with exists
        friend = ConnectionService.get_user_by_id(db, friend_id)

        # Check if a connection already exists between the two users
        existing = ConnectionService.check_existing_connection(db, user_id, friend_id)
        if existing:
            if existing.status == ConnectionStatus.ACCEPTED:
                raise HTTPException(status_code=400, detail="Already connected")
            if existing.status == ConnectionStatus.PENDING:
                raise HTTPException(status_code=400, detail="Request already pending")

        # Create a new connection request
        new_request = Connection(user_id=user_id, friend_id=friend_id, status=ConnectionStatus.PENDING)
        db.add(new_request)
        db.commit()
        db.refresh(new_request)
        return new_request

    @staticmethod
    def accept_connection_request(db: Session, request_id: int, user_id: int) -> Dict[str, str]:
        """Accept a connection request."""
        # Fetch the connection request by ID
        connection = db.query(Connection).filter(Connection.id == request_id).first()
        if not connection:
            raise HTTPException(status_code=404, detail="Connection request not found")
        if connection.friend_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to accept this request")
        if connection.status != ConnectionStatus.PENDING:
            raise HTTPException(status_code=400, detail="Request is not pending")

        # Update the connection status to accepted
        connection.status = ConnectionStatus.ACCEPTED
        db.commit()
        return {"message": "Connection accepted!"}

    @staticmethod
    def reject_connection_request(db: Session, request_id: int, user_id: int) -> Dict[str, str]:
        """Reject a connection request."""
        # Fetch the connection request by ID
        connection = db.query(Connection).filter(Connection.id == request_id).first()
        if not connection:
            raise HTTPException(status_code=404, detail="Connection request not found")
        if connection.friend_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to reject this request")
        if connection.status != ConnectionStatus.PENDING:
            raise HTTPException(status_code=400, detail="Request is not pending")

        # Update the connection status to rejected
        connection.status = ConnectionStatus.REJECTED
        db.commit()
        return {"message": "Connection request rejected"}

    @staticmethod
    def get_user_connections(db: Session, user_id: int) -> List[Dict]:
        """Get all accepted connections for a user."""
        return ConnectionService.get_user_connections(db, user_id)

    @staticmethod
    def get_pending_requests(db: Session, user_id: int) -> List[Dict]:
        """Get all pending connection requests for a user."""
        return ConnectionService.get_pending_requests(db, user_id)

    @staticmethod
    def get_available_users(db: Session, current_user_id: int) -> List[Dict]:
        """Get users available for connection."""
        return ConnectionService.get_available_users(db, current_user_id)

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Dict:
        """Get a specific user by ID."""
        user = ConnectionService.get_user_by_id(db, user_id)
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "profile_picture": user.profile_picture
        }
