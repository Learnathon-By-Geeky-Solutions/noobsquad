from unittest import TestCase
from unittest.mock import Mock, patch
from datetime import datetime
from services.PostTypeHandler import (
    _get_media_post_data,
    _get_document_post_data,
    _get_event_post_data,
    get_post_additional_data
)

class TestPostTypeHandler(TestCase):
    def setUp(self):
        self.mock_db = Mock()
        self.mock_post = Mock()
        self.post_id = 1

    def test_get_media_post_data_with_media(self):
        mock_media = Mock(media_url="http://example.com/image.jpg")
        self.mock_db.query().filter().first.return_value = mock_media
        
        result = _get_media_post_data(self.mock_post, self.mock_db)
        
        self.assertEqual(result["media_url"], "http://example.com/image.jpg")

    def test_get_media_post_data_without_media(self):
        self.mock_db.query().filter().first.return_value = None
        
        result = _get_media_post_data(self.mock_post, self.mock_db)
        
        self.assertIsNone(result["media_url"])

    def test_get_document_post_data_with_document(self):
        mock_document = Mock(document_url="http://example.com/doc.pdf")
        self.mock_db.query().filter().first.return_value = mock_document
        
        result = _get_document_post_data(self.mock_post, self.mock_db)
        
        self.assertEqual(result["document_url"], "http://example.com/doc.pdf")

    def test_get_document_post_data_without_document(self):
        self.mock_db.query().filter().first.return_value = None
        
        result = _get_document_post_data(self.mock_post, self.mock_db)
        
        self.assertIsNone(result["document_url"])

    def test_get_event_post_data_with_event(self):
        event_datetime = datetime.now()
        mock_event = Mock(
            title="Test Event",
            description="Test Description",
            event_datetime=event_datetime,
            location="Test Location"
        )
        self.mock_db.query().filter().first.return_value = mock_event
        
        result = _get_event_post_data(self.mock_post, self.mock_db)
        
        self.assertEqual(result["event"]["title"], "Test Event")
        self.assertEqual(result["event"]["description"], "Test Description")
        self.assertEqual(result["event"]["event_datetime"], event_datetime)
        self.assertEqual(result["event"]["location"], "Test Location")

    def test_get_event_post_data_without_event(self):
        self.mock_db.query().filter().first.return_value = None
        
        result = _get_event_post_data(self.mock_post, self.mock_db)
        
        self.assertEqual(result, {})

    def test_get_post_additional_data_media(self):
        self.mock_post.post_type = "media"
        mock_media = Mock(media_url="http://example.com/image.jpg")
        self.mock_db.query().filter().first.return_value = mock_media
        
        result = get_post_additional_data(self.mock_post, self.mock_db)
        
        self.assertEqual(result["media_url"], "http://example.com/image.jpg")

    def test_get_post_additional_data_document(self):
        self.mock_post.post_type = "document"
        mock_document = Mock(document_url="http://example.com/doc.pdf")
        self.mock_db.query().filter().first.return_value = mock_document
        
        result = get_post_additional_data(self.mock_post, self.mock_db)
        
        self.assertEqual(result["document_url"], "http://example.com/doc.pdf")

    def test_get_post_additional_data_unknown_type(self):
        self.mock_post.post_type = "unknown"
        
        result = get_post_additional_data(self.mock_post, self.mock_db)
        
        self.assertEqual(result, {})