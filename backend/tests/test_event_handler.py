from unittest import TestCase
from unittest.mock import Mock, patch
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import HTTPException, UploadFile
import pytest
from services.EventHandler import (
    _parse_datetime_string,
    _convert_to_utc,
    parse_event_datetime,
    _handle_event_image,
    create_event_post,
    update_event_post,
    format_event_response
)

class TestEventHandler(TestCase):
    def setUp(self):
        self.mock_db = Mock()
        self.user_id = 1
        self.event_date = "2025-04-30"
        self.event_time = "14:30"
        self.user_timezone = "UTC"
        self.content = "Test event content"
        self.event_data = {
            "event_title": "Test Event",
            "event_description": "Test Description",
            "event_date": self.event_date,
            "event_time": self.event_time,
            "location": "Test Location",
            "user_timezone": self.user_timezone
        }

    def test_parse_datetime_string_success(self):
        result = _parse_datetime_string(self.event_date, self.event_time)
        
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 30)

    def test_parse_datetime_string_invalid_format(self):
        with pytest.raises(HTTPException) as exc_info:
            _parse_datetime_string("2025/04/30", "14:30")
        
        assert exc_info.value.status_code == 400
        assert "Invalid datetime format" in str(exc_info.value.detail)

    def test_convert_to_utc_success(self):
        local_dt = datetime(2025, 4, 30, 14, 30)
        timezone = "America/New_York"
        
        result = _convert_to_utc(local_dt, timezone)
        
        self.assertEqual(result.tzinfo, ZoneInfo("UTC"))

    def test_convert_to_utc_invalid_timezone(self):
        local_dt = datetime(2025, 4, 30, 14, 30)
        
        with pytest.raises(HTTPException) as exc_info:
            _convert_to_utc(local_dt, "Invalid/Timezone")
        
        assert exc_info.value.status_code == 400
        assert "Error processing datetime" in str(exc_info.value.detail)

    def test_parse_event_datetime(self):
        result = parse_event_datetime(self.event_date, self.event_time, self.user_timezone)
        
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.tzinfo, ZoneInfo("UTC"))

    @patch('services.EventHandler.save_upload_file')
    @patch('services.EventHandler.generate_secure_filename')
    def test_handle_event_image(self, mock_generate_filename, mock_save_file):
        mock_image = Mock(spec=UploadFile)
        mock_generate_filename.return_value = "test_image.jpg"
        upload_dir = "test/uploads"
        
        result = _handle_event_image(mock_image, self.user_id, upload_dir)
        
        mock_generate_filename.assert_called_once_with(self.user_id, ".jpg")
        mock_save_file.assert_called_once_with(mock_image, upload_dir, "test_image.jpg")
        self.assertEqual(result, "test_image.jpg")

    def test_handle_event_image_no_image(self):
        result = _handle_event_image(None, self.user_id, "test/uploads")
        self.assertIsNone(result)

    @patch('services.EventHandler.create_base_post')
    @patch('services.EventHandler._handle_event_image')
    def test_create_event_post(self, mock_handle_image, mock_create_base_post):
        mock_post = Mock(id=1)
        mock_event = Mock()
        mock_image = Mock(spec=UploadFile)
        mock_create_base_post.return_value = mock_post
        mock_handle_image.return_value = "test_image.jpg"
        
        self.mock_db.refresh = Mock()
        
        post, event = create_event_post(
            self.mock_db,
            self.user_id,
            self.content,
            self.event_data,
            mock_image
        )
        
        mock_create_base_post.assert_called_once_with(
            self.mock_db,
            self.user_id,
            self.content,
            "event"
        )
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.assertEqual(post, mock_post)

    def test_update_event_post(self):
        mock_post = Mock(id=1)
        mock_event = Mock()
        update_data = {
            "content": "Updated content",
            "event_title": "Updated Title",
            "event_description": "Updated Description",
            "event_date": self.event_date,
            "event_time": self.event_time,
            "location": "Updated Location"
        }
        
        post, event = update_event_post(self.mock_db, mock_post, mock_event, update_data)
        
        self.assertEqual(mock_post.content, "Updated content")
        self.assertEqual(mock_event.title, "Updated Title")
        self.assertEqual(mock_event.description, "Updated Description")
        self.assertEqual(mock_event.location, "Updated Location")
        self.mock_db.commit.assert_called_once()

    def test_format_event_response(self):
        mock_post = Mock(
            id=1,
            content=self.content
        )
        mock_event = Mock(
            title="Test Event",
            description="Test Description",
            event_datetime=datetime.now(ZoneInfo("UTC")),
            location="Test Location",
            image_url="test_image.jpg"
        )
        
        result = format_event_response(mock_post, mock_event)
        
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["content"], self.content)
        self.assertEqual(result["title"], "Test Event")
        self.assertEqual(result["description"], "Test Description")
        self.assertEqual(result["location"], "Test Location")
        self.assertEqual(result["image_url"], "test_image.jpg")