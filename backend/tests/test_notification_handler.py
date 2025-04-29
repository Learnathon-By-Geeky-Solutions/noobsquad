from unittest import TestCase
from unittest.mock import Mock, patch
from services.NotificationHandler import (
    create_notification,
    send_post_notifications,
    mark_notification_as_read,
    get_user_notifications,
    get_unread_notification_count,
    clear_all_notifications
)

class TestNotificationHandler(TestCase):
    def setUp(self):
        self.mock_db = Mock()
        self.user_id = 1
        self.actor_id = 2
        self.post_id = 1

    def test_create_notification(self):
        mock_notification = Mock()
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()

        with patch('services.NotificationHandler.Notification', return_value=mock_notification):
            result = create_notification(
                self.mock_db,
                self.user_id,
                self.actor_id,
                "new_post",
                self.post_id
            )

        self.mock_db.add.assert_called_once_with(mock_notification)
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(mock_notification)
        self.assertEqual(result, mock_notification)

    def test_mark_notification_as_read(self):
        mock_notification = Mock(is_read=False)
        self.mock_db.query().filter().first.return_value = mock_notification
        
        result = mark_notification_as_read(
            self.mock_db,
            notification_id=1,
            user_id=self.user_id
        )

        self.assertTrue(result.is_read)
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(mock_notification)

    def test_get_user_notifications(self):
        mock_notifications = [Mock(), Mock()]
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_notifications

        result = get_user_notifications(
            self.mock_db,
            self.user_id,
            limit=10,
            offset=0
        )

        self.assertEqual(result, mock_notifications)

    def test_get_unread_notification_count(self):
        expected_count = 5
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = expected_count

        result = get_unread_notification_count(
            self.mock_db,
            self.user_id
        )

        self.assertEqual(result, expected_count)

    def test_clear_all_notifications(self):
        expected_count = 3
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.update.return_value = expected_count

        result = clear_all_notifications(
            self.mock_db,
            self.user_id
        )

        self.assertEqual(result, expected_count)
        self.mock_db.commit.assert_called_once()