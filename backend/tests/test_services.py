from unittest import TestCase
from unittest.mock import Mock, patch
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import HTTPException
import pytest
from services.services import (
    _parse_datetime,
    _convert_to_utc,
    should_convert,
    try_convert_datetime,
    _update_field,
    update_fields,
    update_post_and_event,
    format_updated_event_response,
    get_post_and_event
)

class TestServices(TestCase):
    def setUp(self):
        self.mock_db = Mock()
        self.user_id = 1
        self.post_id = 1
        self.date_str = "2025-04-30"
        self.time_str = "14:30"
        self.timezone = "UTC"

    def test_parse_datetime(self):
        result = _parse_datetime(self.date_str, self.time_str)
        
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 4)
        self.assertEqual(result.day, 30)
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 30)

    def test_convert_to_utc(self):
        result = _convert_to_utc(
            self.date_str,
            self.time_str,
            "America/New_York"
        )
        
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.tzinfo, ZoneInfo("UTC"))

    def test_should_convert_all_present(self):
        result = should_convert(self.date_str, self.time_str, self.timezone)
        self.assertTrue(result)

    def test_should_convert_missing_values(self):
        test_cases = [
            (None, self.time_str, self.timezone),
            (self.date_str, None, self.timezone),
            (self.date_str, self.time_str, None),
        ]
        
        for date, time, tz in test_cases:
            result = should_convert(date, time, tz)
            self.assertFalse(result)

    def test_try_convert_datetime(self):
        fallback = datetime.now()
        result = try_convert_datetime(
            self.date_str,
            self.time_str,
            self.timezone,
            fallback
        )
        
        self.assertIsInstance(result, datetime)
        self.assertNotEqual(result, fallback)

    def test_try_convert_datetime_fallback(self):
        fallback = datetime.now()
        result = try_convert_datetime(None, None, None, fallback)
        
        self.assertEqual(result, fallback)

    def test_update_field_with_change(self):
        mock_model = Mock(test_field="old_value")
        
        result = _update_field(mock_model, "test_field", "new_value")
        
        self.assertTrue(result)
        self.assertEqual(mock_model.test_field, "new_value")

    def test_update_field_no_change(self):
        mock_model = Mock(test_field="same_value")
        
        result = _update_field(mock_model, "test_field", "same_value")
        
        self.assertFalse(result)

    def test_update_fields(self):
        mock_model = Mock(field1="old1", field2="old2")
        fields = {
            "field1": "new1",
            "field2": "new2"
        }
        
        result = update_fields(fields, mock_model, self.mock_db)
        
        self.assertTrue(result)
        self.assertEqual(mock_model.field1, "new1")
        self.assertEqual(mock_model.field2, "new2")
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(mock_model)

    def test_update_post_and_event(self):
        mock_post = Mock()
        mock_event = Mock()
        post_data = {"content": "new content"}
        event_data = {"title": "new title"}
        
        result = update_post_and_event(
            self.mock_db,
            mock_post,
            mock_event,
            post_data,
            event_data
        )
        
        self.assertTrue(result)
        self.assertEqual(mock_post.content, "new content")
        self.assertEqual(mock_event.title, "new title")

    def test_format_updated_event_response(self):
        mock_post = Mock(
            id=1,
            content="Test content"
        )
        mock_event = Mock(
            title="Test Event",
            description="Test Description",
            event_datetime=datetime.now(),
            location="Test Location"
        )
        
        result = format_updated_event_response(mock_post, mock_event)
        
        self.assertEqual(result["message"], "Event post updated successfully")
        self.assertEqual(result["updated_post"]["id"], 1)
        self.assertEqual(result["updated_post"]["content"], "Test content")
        self.assertEqual(result["updated_post"]["title"], "Test Event")

    def test_get_post_and_event_success(self):
        mock_post = Mock()
        mock_event = Mock()
        self.mock_db.query().filter().first.side_effect = [mock_post, mock_event]
        
        post, event = get_post_and_event(self.post_id, self.user_id, self.mock_db)
        
        self.assertEqual(post, mock_post)
        self.assertEqual(event, mock_event)

    def test_get_post_and_event_post_not_found(self):
        self.mock_db.query().filter().first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            get_post_and_event(self.post_id, self.user_id, self.mock_db)
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Post not found or not authorized"

    def test_get_post_and_event_event_not_found(self):
        mock_post = Mock()
        self.mock_db.query().filter().first.side_effect = [mock_post, None]
        
        with pytest.raises(HTTPException) as exc_info:
            get_post_and_event(self.post_id, self.user_id, self.mock_db)
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Event details not found"