from unittest import TestCase
from unittest.mock import Mock, patch
from services.PostHandler import (
    get_post_by_id,
    create_post_entry,
    extract_hashtags,
    get_user_like_status,
    STATUS_404_ERROR
)
from fastapi import HTTPException

class TestPostHandler(TestCase):
    def setUp(self):
        self.mock_db = Mock()
        self.mock_user_id = 1

    def test_extract_hashtags(self):
        text = "This is a #test post with #multiple #hashtags"
        hashtags = extract_hashtags(text)
        self.assertEqual(hashtags, ["test", "multiple", "hashtags"])

    def test_create_post_entry(self):
        mock_post = Mock()
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        
        with patch('services.PostHandler.Post', return_value=mock_post):
            result = create_post_entry(
                self.mock_db,
                self.mock_user_id,
                "Test content",
                "text"
            )
            
        self.mock_db.add.assert_called_once_with(mock_post)
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(mock_post)
        self.assertEqual(result, mock_post)

    # def test_get_post_by_id_not_found(self):
    #     self.mock_db.query().filter().first = Mock(return_value=None)
        
    #     with self.assertRaises(HTTPException) as context:
    #         get_post_by_id(self.mock_db, 1, self.mock_user_id)
        
    #     self.assertEqual(context.exception.status_code, 404)
    #     self.assertEqual(context.exception.detail, STATUS_404_ERROR)