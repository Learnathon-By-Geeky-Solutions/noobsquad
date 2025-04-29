from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, case
from models.user import User
from models.connection import Connection, ConnectionStatus
import logging

logger = logging.getLogger(__name__)

def _validate_user_exists(db: Session, user_id: int) -> None:
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="User not found")

def _get_existing_connection(db: Session, user_id: int, friend_id: int) -> Optional[Connection]:
    return db.query(Connection).filter(
        or_(
            (Connection.user_id == user_id) & (Connection.friend_id == friend_id),
            (Connection.user_id == friend_id) & (Connection.friend_id == user_id)
        )
    ).first()

def _validate_connection_status(connection: Optional[Connection]) -> None:
    if not connection:
        return
    
    if connection.status == ConnectionStatus.ACCEPTED:
        raise HTTPException(status_code=400, detail="Already connected")
    if connection.status == ConnectionStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request already pending")

def _create_connection(db: Session, user_id: int, friend_id: int) -> Connection:
    new_request = Connection(
        user_id=user_id,
        friend_id=friend_id,
        status=ConnectionStatus.PENDING
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request

def _format_user_response(user: User) -> Dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "profile_picture": user.profile_picture
    }

class ConnectionHandler:
    @staticmethod
    def send_connection_request(
        db: Session,
        user_id: int,
        friend_id: int
    ) -> Connection:
        """Send a connection request to another user."""
        try:
            _validate_user_exists(db, friend_id)
            existing = _get_existing_connection(db, user_id, friend_id)
            _validate_connection_status(existing)
            return _create_connection(db, user_id, friend_id)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error sending connection request: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @staticmethod
    def accept_connection_request(
        db: Session,
        request_id: int,
        user_id: int
    ) -> Dict[str, str]:
        """Accept a connection request."""
        try:
            connection = db.query(Connection).filter(Connection.id == request_id).first()
            
            if not connection:
                raise HTTPException(status_code=404, detail="Connection request not found")
            if connection.friend_id != user_id:
                raise HTTPException(status_code=403, detail="Not authorized to accept this request")
            if connection.status != ConnectionStatus.PENDING:
                raise HTTPException(status_code=400, detail="Request is not pending")
            
            connection.status = ConnectionStatus.ACCEPTED
            db.commit()
            db.refresh(connection)
            
            return {"message": "Connection accepted!"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error accepting connection request: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @staticmethod
    def reject_connection_request(
        db: Session,
        request_id: int,
        user_id: int
    ) -> Dict[str, str]:
        """Reject a connection request."""
        try:
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
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error rejecting connection request: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @staticmethod
    def get_user_connections(
        db: Session,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """Get all connections for a user."""
        try:
            connections = db.query(Connection).filter(
                or_(
                    Connection.user_id == user_id,
                    Connection.friend_id == user_id
                ),
                Connection.status == ConnectionStatus.ACCEPTED
            ).all()
            
            return [
                {
                    "connection_id": conn.id,
                    "friend_id": conn.friend_id if conn.user_id == user_id else conn.user_id,
                    **(_format_user_response(db.query(User).filter(User.id == conn.friend_id if conn.user_id == user_id else conn.user_id).first()))
                }
                for conn in connections
            ]
        except Exception as e:
            logger.error(f"Error getting user connections: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @staticmethod
    def get_available_users(
        db: Session,
        current_user_id: int
    ) -> List[Dict[str, Any]]:
        """Get users available for connection (excluding existing connections)."""
        try:
            subquery = db.query(Connection).filter(
                or_(
                    Connection.user_id == current_user_id,
                    Connection.friend_id == current_user_id
                )
            ).subquery()
            
            available_users = db.query(User).filter(
                User.id != current_user_id,
                ~User.id.in_(
                    db.query(subquery.c.user_id).union(
                        db.query(subquery.c.friend_id)
                    )
                )
            ).all()
            
            return [_format_user_response(user) for user in available_users]
        except Exception as e:
            logger.error(f"Error getting available users: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @staticmethod
    def get_pending_requests(
        db: Session,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """Get pending connection requests for a user."""
        try:
            pending = db.query(Connection).filter(
                Connection.friend_id == user_id,
                Connection.status == ConnectionStatus.PENDING
            ).all()
            
            return [
                {
                    "request_id": request.id,
                    "sender_id": request.user_id,
                    **(_format_user_response(db.query(User).filter(User.id == request.user_id).first()))
                }
                for request in pending
            ]
        except Exception as e:
            logger.error(f"Error getting pending requests: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @staticmethod
    def get_user_by_id(
        db: Session,
        user_id: int
    ) -> User:
        """Get a user by their ID."""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error") 