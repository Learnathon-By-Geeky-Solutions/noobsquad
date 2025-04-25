import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timezone
from sqlalchemy.orm import Session

# Add the backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))  # Adds the root project folder to path

from crud.notification import (
    create_notification,
    get_unread_notifications,
    get_all_notifications,
    mark_notification_as_read
)
from models.notifications import Notification
from models.user import User


# Mock the database session
@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)


# Mock User for testing
@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.profile_picture = "testuser.jpg"
    return user


# Mock Actor for testing
@pytest.fixture
def mock_actor():
    actor = MagicMock(spec=User)
    actor.id = 2
    actor.username = "actor_user"
    actor.profile_picture = "actor.jpg"
    return actor


# Mock Notification for testing
@pytest.fixture
def mock_notification(mock_user, mock_actor):
    notification = MagicMock(spec=Notification)
    notification.id = 1
    notification.user_id = mock_user.id  # recipient
    notification.actor_id = mock_actor.id  # actor
    notification.type = "new_post"
    notification.post_id = 10
    notification.is_read = False
    notification.created_at = datetime.now(timezone.utc)
    notification.actor = mock_actor  # Set the relationship
    return notification


# Test create_notification function
def test_create_notification(mock_db, mock_user, mock_actor):
    # Set up
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_notification = MagicMock()
    mock_notification.id = 1
    
    # Define the side effect for the refresh method to simulate setting an ID
    def refresh_side_effect(obj):
        obj.id = 1
    
    mock_db.refresh.side_effect = refresh_side_effect
    
    # Execute
    with patch('crud.notification.Notification', return_value=mock_notification):
        result = create_notification(
            db=mock_db,
            recipient_id=mock_user.id,
            actor_id=mock_actor.id,
            notif_type="new_post",
            post_id=10
        )
        
        # Verify
        assert result is not None
        
        # Verify the mock DB methods were called
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()


# Test get_unread_notifications function
def test_get_unread_notifications(mock_db, mock_notification):
    # Set up
    mock_query = MagicMock()
    mock_join = MagicMock()
    mock_filter = MagicMock()
    
    mock_filter.all.return_value = [mock_notification]
    mock_join.filter.return_value = mock_filter
    mock_query.join.return_value = mock_join
    mock_db.query.return_value = mock_query
    
    # Execute
    result = get_unread_notifications(db=mock_db, user_id=mock_notification.user_id)
    
    # Verify
    assert len(result) == 1
    assert result[0]["id"] == mock_notification.id
    assert result[0]["type"] == mock_notification.type
    assert result[0]["post_id"] == mock_notification.post_id
    assert result[0]["actor_id"] == mock_notification.actor_id
    assert result[0]["actor_username"] == mock_notification.actor.username
    assert result[0]["is_read"] == False
    assert "actor_image_url" in result[0]
    
    # Verify the mock DB methods were called correctly
    mock_db.query.assert_called_once() 


# Test get_all_notifications function
def test_get_all_notifications(mock_db, mock_notification):
    # Set up
    mock_query = MagicMock()
    mock_join = MagicMock()
    mock_filter = MagicMock()
    mock_order = MagicMock()
    
    mock_order.all.return_value = [mock_notification]
    mock_filter.order_by.return_value = mock_order
    mock_join.filter.return_value = mock_filter
    mock_query.join.return_value = mock_join
    mock_db.query.return_value = mock_query
    
    # Execute
    result = get_all_notifications(db=mock_db, user_id=mock_notification.user_id)
    
    # Verify
    assert len(result) == 1
    assert result[0]["id"] == mock_notification.id
    assert result[0]["type"] == mock_notification.type
    assert result[0]["post_id"] == mock_notification.post_id
    assert result[0]["actor_id"] == mock_notification.actor_id
    assert result[0]["actor_username"] == mock_notification.actor.username
    
    # Verify the mock DB methods were called correctly
    mock_db.query.assert_called_once()
    mock_query.join.assert_called_once()
    mock_join.filter.assert_called_once()
    mock_filter.order_by.assert_called_once()


# Test mark_notification_as_read function
def test_mark_notification_as_read(mock_db, mock_notification):
    # Set up
    mock_query = MagicMock()
    mock_join = MagicMock()
    mock_filter = MagicMock()
    
    mock_filter.first.return_value = mock_notification
    mock_join.filter.return_value = mock_filter
    mock_query.join.return_value = mock_join
    mock_db.query.return_value = mock_query
    
    # Execute
    result = mark_notification_as_read(db=mock_db, notif_id=mock_notification.id)
    
    # Verify
    assert result["id"] == mock_notification.id
    assert result["is_read"] == True  # Should be marked as read
    assert mock_notification.is_read == True  # The mock object should be updated
    
    # Verify the mock DB methods were called correctly
    mock_db.query.assert_called_once()
    mock_query.join.assert_called_once()
    mock_join.filter.assert_called_once()
    mock_db.commit.assert_called_once()


# Test mark_notification_as_read when notification is not found
def test_mark_notification_as_read_not_found(mock_db):
    # Set up
    mock_query = MagicMock()
    mock_join = MagicMock()
    mock_filter = MagicMock()
    
    mock_filter.first.return_value = None  # Notification not found
    mock_join.filter.return_value = mock_filter
    mock_query.join.return_value = mock_join
    mock_db.query.return_value = mock_query
    
    # Execute
    result = mark_notification_as_read(db=mock_db, notif_id=999)  # Non-existent ID
    
    # Verify
    assert result is None
    
    # Verify the mock DB methods were called correctly
    mock_db.query.assert_called_once()
    mock_db.commit.assert_not_called()  # Commit should not be called if notification not found
