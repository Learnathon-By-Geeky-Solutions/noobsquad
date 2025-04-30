import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from unittest.mock import Mock, create_autospec

from models.connection import Connection, ConnectionStatus
from core.connection_crud import (
    send_request,
    accept_request,
    reject_request,
    get_connections,
    get_pending_requests
)

@pytest.fixture
def mock_db(mocker):
    return mocker.Mock(spec=Session)

@pytest.fixture
def mock_user():
    user = Mock()
    user.id = 1
    user.username = "test_user"
    user.email = "test@example.com"
    return user

@pytest.fixture
def mock_friend():
    friend = Mock()
    friend.id = 2
    friend.username = "test_friend"
    friend.email = "friend@example.com"
    return friend

def test_send_request_success(mock_db, mock_user, mock_friend, mocker):
    # Setup
    mock_db.query.return_value.filter.return_value.first.return_value = mock_friend
    mock_db.query.return_value.filter_by.return_value.first.return_value = None

    # Mock Connection class
    mock_connection = Mock(spec=Connection)
    mock_connection.user_id = mock_user.id
    mock_connection.friend_id = mock_friend.id
    mock_connection.status = ConnectionStatus.PENDING
    mocker.patch('core.connection_crud.Connection', return_value=mock_connection)

    # Execute
    result = send_request(mock_db, mock_user.id, mock_friend.id)

    # Assert
    assert result.user_id == mock_user.id
    assert result.friend_id == mock_friend.id
    assert result.status == ConnectionStatus.PENDING
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

def test_send_request_friend_not_found(mock_db, mock_user):
    # Setup
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Execute and Assert
    with pytest.raises(HTTPException) as exc_info:
        send_request(mock_db, mock_user.id, 999)
    assert exc_info.value.status_code == 404
    assert "Friend ID does not exist" in str(exc_info.value.detail)

def test_send_request_already_exists(mock_db, mock_user, mock_friend):
    # Setup
    mock_db.query.return_value.filter.return_value.first.return_value = mock_friend
    existing_connection = Mock(spec=Connection)
    mock_db.query.return_value.filter_by.return_value.first.return_value = existing_connection

    # Execute and Assert
    with pytest.raises(HTTPException) as exc_info:
        send_request(mock_db, mock_user.id, mock_friend.id)
    assert exc_info.value.status_code == 400
    assert "Connection request already sent" in str(exc_info.value.detail)

def test_accept_request_success(mock_db):
    # Setup
    mock_connection = Mock(spec=Connection)
    mock_connection.id = 1
    mock_connection.status = ConnectionStatus.PENDING
    mock_db.query.return_value.filter_by.return_value.first.return_value = mock_connection

    # Execute
    result = accept_request(mock_db, request_id=1)

    # Assert
    assert result.status == ConnectionStatus.ACCEPTED
    mock_db.commit.assert_called_once()

def test_accept_request_not_found(mock_db):
    # Setup
    mock_db.query.return_value.filter_by.return_value.first.return_value = None

    # Execute and Assert
    with pytest.raises(HTTPException) as exc_info:
        accept_request(mock_db, request_id=999)
    assert exc_info.value.status_code == 404
    assert "No pending request found" in str(exc_info.value.detail)

def test_reject_request_success(mock_db):
    # Setup
    mock_connection = Mock(spec=Connection)
    mock_connection.id = 1
    mock_connection.status = ConnectionStatus.PENDING
    mock_db.query.return_value.filter_by.return_value.first.return_value = mock_connection

    # Execute
    result = reject_request(mock_db, request_id=1)

    # Assert
    assert result.status == ConnectionStatus.REJECTED
    mock_db.commit.assert_called_once()

def test_reject_request_not_found(mock_db):
    # Setup
    mock_db.query.return_value.filter_by.return_value.first.return_value = None

    # Execute
    result = reject_request(mock_db, request_id=999)

    # Assert
    assert result is None

def test_get_connections(mock_db):
    # Setup
    mock_conn1 = Mock(spec=Connection)
    mock_conn1.user_id = 1
    mock_conn1.friend_id = 2
    mock_conn1.status = ConnectionStatus.ACCEPTED

    mock_conn2 = Mock(spec=Connection)
    mock_conn2.user_id = 2
    mock_conn2.friend_id = 3
    mock_conn2.status = ConnectionStatus.ACCEPTED

    mock_db.query.return_value.filter.return_value.all.return_value = [mock_conn1, mock_conn2]

    # Execute
    result = get_connections(mock_db, user_id=1)

    # Assert
    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(conn, dict) for conn in result)
    assert all('user_id' in conn and 'friend_id' in conn for conn in result)

def test_get_pending_requests(mock_db):
    # Setup
    mock_conn1 = Mock(spec=Connection)
    mock_conn1.user_id = 2
    mock_conn1.friend_id = 1
    mock_conn1.status = ConnectionStatus.PENDING

    mock_conn2 = Mock(spec=Connection)
    mock_conn2.user_id = 3
    mock_conn2.friend_id = 1
    mock_conn2.status = ConnectionStatus.PENDING

    mock_db.query.return_value.filter.return_value.all.return_value = [mock_conn1, mock_conn2]

    # Execute
    result = get_pending_requests(mock_db, user_id=1)

    # Assert
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(req, Connection) for req in result)
    assert all(req.status == ConnectionStatus.PENDING for req in result)
    assert all(req.friend_id == 1 for req in result)