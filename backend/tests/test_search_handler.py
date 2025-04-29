from unittest import TestCase
from unittest.mock import Mock, patch
from datetime import datetime
from fastapi import HTTPException
import pytest
from services.SearchHandler import (
    SearchHandler,
    _format_post_response,
    _format_user_response,
    _search_posts_by_keyword,
    _search_users_by_keyword
)

class TestSearchHandler(TestCase):
    def setUp(self):
        self.mock_db = Mock()
        self.keyword = "test"

    def test_format_post_response(self):
        created_at = datetime.now()
        mock_post = Mock(
            id=1,
            user_id=1,
            content="Test content",
            post_type="text",
            created_at=created_at,
            like_count=5
        )
        
        result = _format_post_response(mock_post)
        
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["user_id"], 1)
        self.assertEqual(result["content"], "Test content")
        self.assertEqual(result["post_type"], "text")
        self.assertEqual(result["created_at"], created_at.isoformat())
        self.assertEqual(result["like_count"], 5)

    def test_format_user_response(self):
        mock_user = Mock(
            id=1,
            username="testuser",
            email="test@example.com",
            profile_picture="avatar.jpg"
        )
        
        result = _format_user_response(mock_user)
        
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["username"], "testuser")
        self.assertEqual(result["email"], "test@example.com")
        self.assertEqual(result["profile_picture"], "avatar.jpg")

    def test_search_posts_success(self):
        mock_post = Mock()
        mock_post.created_at = datetime.now()
        self.mock_db.query().filter().all.return_value = [mock_post]
        
        with patch('services.SearchHandler._format_post_response') as mock_format:
            mock_format.return_value = {"id": 1, "content": "test"}
            result = SearchHandler.search_posts(self.mock_db, self.keyword)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 1)
        self.assertEqual(result[0]["content"], "test")

    def test_search_posts_error(self):
        self.mock_db.query.side_effect = Exception("Database error")
        
        with pytest.raises(HTTPException) as exc_info:
            SearchHandler.search_posts(self.mock_db, self.keyword)
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Internal server error"

    def test_search_users_success(self):
        mock_user = Mock()
        self.mock_db.query().filter().all.return_value = [mock_user]
        
        with patch('services.SearchHandler._format_user_response') as mock_format:
            mock_format.return_value = {"id": 1, "username": "test"}
            result = SearchHandler.search_users(self.mock_db, self.keyword)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 1)
        self.assertEqual(result[0]["username"], "test")

    def test_search_users_error(self):
        self.mock_db.query.side_effect = Exception("Database error")
        
        with pytest.raises(HTTPException) as exc_info:
            SearchHandler.search_users(self.mock_db, self.keyword)
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Internal server error"

    def test_search_all_success(self):
        with patch('services.SearchHandler.SearchHandler.search_posts') as mock_search_posts:
            with patch('services.SearchHandler.SearchHandler.search_users') as mock_search_users:
                mock_search_posts.return_value = [{"id": 1, "content": "test"}]
                mock_search_users.return_value = [{"id": 1, "username": "test"}]
                
                result = SearchHandler.search_all(self.mock_db, self.keyword)
        
        self.assertIn("posts", result)
        self.assertIn("users", result)
        self.assertEqual(len(result["posts"]), 1)
        self.assertEqual(len(result["users"]), 1)
        self.assertEqual(result["posts"][0]["content"], "test")
        self.assertEqual(result["users"][0]["username"], "test")

    def test_search_all_error(self):
        with patch('services.SearchHandler.SearchHandler.search_posts', side_effect=Exception("Error")):
            with pytest.raises(HTTPException) as exc_info:
                SearchHandler.search_all(self.mock_db, self.keyword)
            
            assert exc_info.value.status_code == 500
            assert exc_info.value.detail == "Internal server error"