from unittest import TestCase
from unittest.mock import Mock, patch
from fastapi import HTTPException
import pytest
from services.ConnectionHandler import ConnectionService, ConnectionHandler
from models.connection import ConnectionStatus

class TestConnectionService(TestCase):
    def setUp(self):
        self.mock_db = Mock()
        self.user_id = 1
        self.friend_id = 2

    def test_get_user_by_id_success(self):
        mock_user = Mock(id=self.user_id)
        self.mock_db.query().filter().first.return_value = mock_user
        
        result = ConnectionService.get_user_by_id(self.mock_db, self.user_id)
        
        self.assertEqual(result, mock_user)

    def test_get_user_by_id_not_found(self):
        self.mock_db.query().filter().first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            ConnectionService.get_user_by_id(self.mock_db, self.user_id)
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found"

    def test_check_existing_connection(self):
        mock_connection = Mock()
        self.mock_db.query().filter().first.return_value = mock_connection
        
        result = ConnectionService.check_existing_connection(
            self.mock_db,
            self.user_id,
            self.friend_id
        )
        
        self.assertEqual(result, mock_connection)

    def test_get_user_connections(self):
        mock_connection = Mock(
            id=1,
            user_id=self.user_id,
            friend_id=self.friend_id,
            status=ConnectionStatus.ACCEPTED
        )
        mock_friend = Mock(
            id=self.friend_id,
            username="friend",
            email="friend@example.com",
            profile_picture="avatar.jpg"
        )
        
        self.mock_db.query().filter().all.return_value = [mock_connection]
        with patch('services.ConnectionHandler.ConnectionService.get_user_by_id', return_value=mock_friend):
            result = ConnectionService.get_user_connections(self.mock_db, self.user_id)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["friend_id"], self.friend_id)
        self.assertEqual(result[0]["username"], "friend")

class TestConnectionHandler(TestCase):
    def setUp(self):
        self.mock_db = Mock()
        self.user_id = 1
        self.friend_id = 2

    @patch('services.ConnectionHandler.ConnectionService.get_user_by_id')
    @patch('services.ConnectionHandler.ConnectionService.check_existing_connection')
    def test_send_connection_request_success(self, mock_check_connection, mock_get_user):
        mock_get_user.return_value = Mock(id=self.friend_id)
        mock_check_connection.return_value = None
        mock_new_request = Mock()
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        
        with patch('services.ConnectionHandler.Connection', return_value=mock_new_request):
            result = ConnectionHandler.send_connection_request(
                self.mock_db,
                self.user_id,
                self.friend_id
            )
        
        self.mock_db.add.assert_called_once_with(mock_new_request)
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(mock_new_request)
        self.assertEqual(result, mock_new_request)

    def test_accept_connection_request_success(self):
        mock_connection = Mock(
            friend_id=self.user_id,
            status=ConnectionStatus.PENDING
        )
        self.mock_db.query().filter().first.return_value = mock_connection
        
        result = ConnectionHandler.accept_connection_request(
            self.mock_db,
            request_id=1,
            user_id=self.user_id
        )
        
        self.assertEqual(mock_connection.status, ConnectionStatus.ACCEPTED)
        self.mock_db.commit.assert_called_once()
        self.assertEqual(result["message"], "Connection accepted!")

    def test_reject_connection_request_success(self):
        mock_connection = Mock(
            friend_id=self.user_id,
            status=ConnectionStatus.PENDING
        )
        self.mock_db.query().filter().first.return_value = mock_connection
        
        result = ConnectionHandler.reject_connection_request(
            self.mock_db,
            request_id=1,
            user_id=self.user_id
        )
        
        self.assertEqual(mock_connection.status, ConnectionStatus.REJECTED)
        self.mock_db.commit.assert_called_once()
        self.assertEqual(result["message"], "Connection request rejected")