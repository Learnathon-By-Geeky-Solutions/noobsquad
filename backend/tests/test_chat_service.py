from unittest import TestCase, IsolatedAsyncioTestCase
from unittest.mock import Mock, patch
from services.chat_service import (
    fetch_conversations,
    fetch_chat_history,
    get_unread_count,
    mark_as_read
)
from datetime import datetime

class TestChatService(IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_db = Mock()
        self.user_id = 1
        self.friend_id = 2
        self.timestamp = datetime.now()

    async def test_fetch_conversations(self):
        mock_message = Mock(
            sender_id=self.user_id,
            receiver_id=self.friend_id,
            content="Test message",
            file_url=None,
            message_type="text",
            timestamp=self.timestamp
        )
        mock_friend = Mock(
            id=self.friend_id,
            username="friend",
            profile_picture="avatar.jpg"
        )

        self.mock_db.query().filter().order_by().all.return_value = [mock_message]
        self.mock_db.query().filter().first.return_value = mock_friend

        with patch('services.chat_service.get_unread_count', return_value=1):
            result = await fetch_conversations(self.mock_db, self.user_id)

        self.assertEqual(len(result), 1)
        conversation = result[0]
        self.assertEqual(conversation["user_id"], self.friend_id)
        self.assertEqual(conversation["username"], "friend")
        self.assertEqual(conversation["avatar"], "avatar.jpg")
        self.assertEqual(conversation["last_message"], "Test message")
        self.assertEqual(conversation["unread_count"], 1)

    async def test_fetch_chat_history(self):
        mock_messages = [
            Mock(
                sender_id=self.user_id,
                receiver_id=self.friend_id,
                content="Message 1"
            ),
            Mock(
                sender_id=self.friend_id,
                receiver_id=self.user_id,
                content="Message 2"
            )
        ]

        self.mock_db.query().filter().order_by().all.return_value = mock_messages

        with patch('services.chat_service.mark_as_read') as mock_mark_read:
            result = await fetch_chat_history(
                self.mock_db,
                self.user_id,
                self.friend_id
            )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].content, "Message 1")
        self.assertEqual(result[1].content, "Message 2")
        mock_mark_read.assert_called_once_with(
            self.mock_db,
            self.friend_id,
            self.user_id
        )

    def test_get_unread_count(self):
        self.mock_db.query().filter().count.return_value = 5

        result = get_unread_count(
            self.mock_db,
            self.friend_id,
            self.user_id
        )

        self.assertEqual(result, 5)

    def test_mark_as_read(self):
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.update.return_value = None

        mark_as_read(self.mock_db, self.friend_id, self.user_id)

        mock_query.update.assert_called_once_with({"is_read": True})
        self.mock_db.commit.assert_called_once()