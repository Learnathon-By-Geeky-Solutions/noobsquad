import pytest
from unittest.mock import Mock, create_autospec
from sqlalchemy.orm import Session
from fastapi import HTTPException
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from models.post import Comment, Post
from routes.PostReaction.CommentHelperFunc import get_comment_by_id, get_post_by_id

@pytest.fixture
def mock_db():
    return Mock(spec=Session)

@pytest.fixture
def mock_comment():
    comment = Mock(spec=Comment)
    comment.id = 1
    comment.content = "Test comment"
    comment.user_id = 1
    comment.post_id = 1
    return comment

@pytest.fixture
def mock_post():
    post = Mock(spec=Post)
    post.id = 1
    post.content = "Test post"
    post.user_id = 1
    return post

def test_get_comment_by_id_success(mock_db, mock_comment):
    # Setup
    mock_db.query.return_value.filter.return_value.first.return_value = mock_comment

    # Execute
    result = get_comment_by_id(mock_db, comment_id=1)

    # Assert
    assert result == mock_comment
    mock_db.query.assert_called_once_with(Comment)
    mock_db.query.return_value.filter.assert_called_once()

def test_get_comment_by_id_not_found(mock_db):
    # Setup
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Execute and Assert
    with pytest.raises(HTTPException) as exc_info:
        get_comment_by_id(mock_db, comment_id=999)
    
    assert exc_info.value.status_code == 404
    assert "Comment not found" in str(exc_info.value.detail)
    mock_db.query.assert_called_once_with(Comment)

def test_get_post_by_id_success(mock_db, mock_post):
    # Setup
    mock_db.query.return_value.filter.return_value.first.return_value = mock_post

    # Execute
    result = get_post_by_id(mock_db, post_id=1)

    # Assert
    assert result == mock_post
    mock_db.query.assert_called_once_with(Post)
    mock_db.query.return_value.filter.assert_called_once()

def test_get_post_by_id_not_found(mock_db):
    # Setup
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Execute and Assert
    with pytest.raises(HTTPException) as exc_info:
        get_post_by_id(mock_db, post_id=999)
    
    assert exc_info.value.status_code == 404
    assert "Post not found" in str(exc_info.value.detail)
    mock_db.query.assert_called_once_with(Post)