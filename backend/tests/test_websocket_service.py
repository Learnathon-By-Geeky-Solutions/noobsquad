from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, patch, AsyncMock
from fastapi import WebSocket
from services.websocket_service import (
    connect_socket,
    disconnect_socket,
    send_socket_message,
    broadcast_message,
    handle_chat_message,
    clients
)

class TestWebSocketService(IsolatedAsyncioTestCase):
    def setUp(self):
        self.user_id = 1
        self.mock_websocket = AsyncMock(spec=WebSocket)
        self.message = {"type": "text", "content": "Hello"}
        # Clear clients dictionary before each test
        clients.clear()

    async def test_connect_socket(self):
        await connect_socket(self.mock_websocket, self.user_id)
        
        self.mock_websocket.accept.assert_called_once()
        self.assertIn(self.user_id, clients)
        self.assertEqual(clients[self.user_id], self.mock_websocket)

    async def test_disconnect_socket(self):
        # First connect a socket
        clients[self.user_id] = self.mock_websocket
        
        await disconnect_socket(self.user_id)
        
        self.assertNotIn(self.user_id, clients)

    async def test_disconnect_socket_not_connected(self):
        # Should not raise any error when disconnecting non-existent client
        await disconnect_socket(999)
        
        self.assertNotIn(999, clients)

    async def test_send_socket_message_to_connected_client(self):
        clients[self.user_id] = self.mock_websocket
        
        await send_socket_message(self.user_id, self.message)
        
        self.mock_websocket.send_json.assert_called_once_with(self.message)

    async def test_send_socket_message_to_non_connected_client(self):
        # Should not raise error when client doesn't exist
        await send_socket_message(999, self.message)
        
        self.mock_websocket.send_json.assert_not_called()

    async def test_broadcast_message(self):
        user_ids = [1, 2, 3]
        mock_websockets = {
            1: AsyncMock(spec=WebSocket),
            2: AsyncMock(spec=WebSocket),
            3: AsyncMock(spec=WebSocket)
        }
        
        # Setup mock clients
        for user_id, websocket in mock_websockets.items():
            clients[user_id] = websocket
        
        await broadcast_message(user_ids, self.message)
        
        # Verify each client received the message
        for websocket in mock_websockets.values():
            websocket.send_json.assert_called_once_with(self.message)

    @patch('services.websocket_service.create_message')
    @patch('services.websocket_service.prepare_message_event')
    @patch('services.websocket_service.broadcast_message')
    async def test_handle_chat_message(
        self,
        mock_broadcast,
        mock_prepare_event,
        mock_create_message
    ):
        mock_db = Mock()
        message_data = {
            "receiver_id": "2",
            "content": "Hello",
            "file_url": None,
            "message_type": "text"
        }
        mock_message = Mock()
        mock_event = {"type": "message", "content": "Hello"}
        
        mock_create_message.return_value = mock_message
        mock_prepare_event.return_value = mock_event
        
        await handle_chat_message(mock_db, self.user_id, message_data)
        
        # Verify message creation
        mock_create_message.assert_called_once_with(
            mock_db,
            self.user_id,
            2,  # receiver_id as int
            "Hello",
            None,
            "text"
        )
        
        # Verify event preparation
        mock_prepare_event.assert_called_once_with(mock_message)
        
        # Verify broadcast
        mock_broadcast.assert_called_once_with([self.user_id, 2], mock_event)