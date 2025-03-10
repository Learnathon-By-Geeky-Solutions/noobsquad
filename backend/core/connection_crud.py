from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.connection import Connection, ConnectionStatus
from schemas.connection import ConnectionCreate
from models.user import User

def send_request(db: Session, user_id: int, friend_id: int):
    # ✅ Check if friend_id exists in the database
    friend_exists = db.query(User).filter(User.id == friend_id).first()
    if not friend_exists:
        raise HTTPException(status_code=404, detail="Friend ID does not exist!")

    # ✅ Check if a request already exists
    existing_request = db.query(Connection).filter_by(user_id=user_id, friend_id=friend_id).first()
    if existing_request:
         raise HTTPException(status_code=400, detail="Connection request already sent!")


    # ✅ Create a new connection request
    connection = Connection(user_id=user_id, friend_id=friend_id, status=ConnectionStatus.PENDING)
    db.add(connection)
    db.commit()
    db.refresh(connection)
    return connection

def accept_request(db: Session, request_id: int):
    connection = db.query(Connection).filter_by(id=request_id, status=ConnectionStatus.PENDING).first()
    if not connection:
        raise HTTPException(status_code=404, detail="No pending request found.")

    connection.status = ConnectionStatus.ACCEPTED
    db.commit()
    db.refresh(connection)  # Ensure the changes reflect in the session
    return connection


def reject_request(db: Session, request_id: int):
    connection = db.query(Connection).filter_by(id=request_id, status=ConnectionStatus.PENDING).first()
    if connection:
        connection.status = ConnectionStatus.REJECTED
        db.commit()
        return connection
    return None

def get_connections(db: Session, user_id: int):
    return db.query(Connection).filter(
        (Connection.user_id == user_id) | (Connection.friend_id == user_id),
        Connection.status == ConnectionStatus.ACCEPTED
    ).all()

def get_pending_requests(db: Session, user_id: int):
    """Fetch all pending connection requests where the user is the recipient."""
    return db.query(Connection).filter(
        Connection.friend_id == user_id,
        Connection.status == ConnectionStatus.PENDING
    ).all()
