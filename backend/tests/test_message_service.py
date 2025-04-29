from unittest import TestCase
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from services.message_service import (
    create_message,
    prepare_message_event
)

class TestMessageService(TestCase):
    def setUp(self):
        self.mock_db = Mock()
        self.sender_id = 1
        self.receiver_id = 2
        self.content = "Test message"
        self.file_url = "http://example.com/file.pdf"
        self.message_type = "text"

    @patch('services.message_service.Message')
    def test_create_message(self, mock_message_class):
        mock_message = Mock()
        mock_message_class.return_value = mock_message
        
        result = create_message(
            self.mock_db,
            self.sender_id,
            self.receiver_id,
            self.content,
            self.file_url,
            self.message_type
        )
        
        self.mock_db.add.assert_called_once_with(mock_message)
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(mock_message)
        self.assertEqual(result, mock_message)

    def test_prepare_message_event(self):
        mock_time = datetime.now(timezone.utc)
        mock_message = Mock(
            id=1,
            sender_id=self.sender_id,
            receiver_id=self.receiver_id,
            content=self.content,
            file_url=self.file_url,
            message_type=self.message_type,
            timestamp=mock_time,
            is_read=False
        )
        
        result = prepare_message_event(mock_message)
        
        expected = {
            "type": "message",
            "id": 1,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "content": self.content,
            "file_url": self.file_url,
            "message_type": self.message_type,
            "timestamp": mock_time.isoformat(),
            "is_read": False
        }
        
        self.assertEqual(result, expected)