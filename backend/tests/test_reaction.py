from unittest import TestCase
from unittest.mock import Mock, patch
from fastapi import HTTPException
import pytest
from services.reaction import *

class TestReactionService(TestCase):
    def setUp(self):
        self.mock_db = Mock()
        self.user_id = 1
        self.post_id = 1
        self.comment_id = 1
        self.comment_content = "Test comment"

    # @patch('services.reaction.Like')
    # def test_create_like_success(self, mock_like_class):
    #     mock_like = Mock()
    #     mock_like_class.return_value = mock_like
    #     self.mock_db.query().filter().first.return_value = None
        
    #     result = create_like(self.mock_db, self.user_id, self.post_id)
        
    #     self.mock_db.add.assert_called_once_with(mock_like)
    #     self.mock_db.commit.assert_called_once()
    #     self.mock_db.refresh.assert_called_once_with(mock_like)
    #     self.assertEqual(result, mock_like)

    # def test_create_like_already_exists(self):
    #     self.mock_db.query().filter().first.return_value = Mock()
        
    #     with pytest.raises(HTTPException) as exc_info:
    #         create_like(self.mock_db, self.user_id, self.post_id)
        
    #     assert exc_info.value.status_code == 400
    #     assert "already liked" in str(exc_info.value.detail)

    # def test_delete_like_success(self):
    #     mock_like = Mock()
    #     self.mock_db.query().filter().first.return_value = mock_like
        
    #     result = delete_like(self.mock_db, self.user_id, self.post_id)
        
    #     self.mock_db.delete.assert_called_once_with(mock_like)
    #     self.mock_db.commit.assert_called_once()
    #     self.assertEqual(result, {"message": "Like removed successfully"})

    # def test_delete_like_not_found(self):
    #     self.mock_db.query().filter().first.return_value = None
        
    #     with pytest.raises(HTTPException) as exc_info:
    #         delete_like(self.mock_db, self.user_id, self.post_id)
        
    #     assert exc_info.value.status_code == 404
    #     assert "Like not found" in str(exc_info.value.detail)

    # @patch('services.reaction.Comment')
    # def test_create_comment_success(self, mock_comment_class):
    #     mock_comment = Mock()
    #     mock_comment_class.return_value = mock_comment
        
    #     result = create_comment(
    #         self.mock_db,
    #         self.user_id,
    #         self.post_id,
    #         self.comment_content
    #     )
        
    #     self.mock_db.add.assert_called_once_with(mock_comment)
    #     self.mock_db.commit.assert_called_once()
    #     self.mock_db.refresh.assert_called_once_with(mock_comment)
    #     self.assertEqual(result, mock_comment)

    # def test_get_post_comments(self):
    #     mock_comments = [Mock(), Mock()]
    #     self.mock_db.query().filter().all.return_value = mock_comments
        
    #     result = get_post_comments(self.mock_db, self.post_id)
        
    #     self.assertEqual(result, mock_comments)

    # def test_get_comment_by_id_success(self):
    #     mock_comment = Mock(user_id=self.user_id)
    #     self.mock_db.query().filter().first.return_value = mock_comment
        
    #     result = get_comment_by_id(self.mock_db, self.comment_id, self.user_id)
        
    #     self.assertEqual(result, mock_comment)

    # def test_get_comment_by_id_not_found(self):
    #     self.mock_db.query().filter().first.return_value = None
        
    #     with pytest.raises(HTTPException) as exc_info:
    #         get_comment_by_id(self.mock_db, self.comment_id, self.user_id)
        
    #     assert exc_info.value.status_code == 404
    #     assert "Comment not found" in str(exc_info.value.detail)

    # def test_update_comment_success(self):
    #     mock_comment = Mock(user_id=self.user_id)
    #     self.mock_db.query().filter().first.return_value = mock_comment
    #     new_content = "Updated comment"
        
    #     result = update_comment(
    #         self.mock_db,
    #         self.comment_id,
    #         self.user_id,
    #         new_content
    #     )
        
    #     self.assertEqual(mock_comment.content, new_content)
    #     self.mock_db.commit.assert_called_once()
    #     self.assertEqual(result, mock_comment)

    # def test_delete_comment_success(self):
    #     mock_comment = Mock(user_id=self.user_id)
    #     self.mock_db.query().filter().first.return_value = mock_comment
        
    #     result = delete_comment(self.mock_db, self.comment_id, self.user_id)
        
    #     self.mock_db.delete.assert_called_once_with(mock_comment)
    #     self.mock_db.commit.assert_called_once()
    #     self.assertEqual(result, {"message": "Comment deleted successfully"})