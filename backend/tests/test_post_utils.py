import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.post import Post, Comment
from models.user import User
from models.university import University
from models.hashtag import Hashtag
from utils.post_utils import (
    validate_post_ownership,
    prepare_post_response,
    handle_media_upload,
    create_base_post
)

@pytest.fixture
def mock_db():
    return Mock(spec=Session)

@pytest.fixture
def mock_post():
    post = Mock(spec=Post)
    post.id = 1
    post.user_id = 1
    post.content = "Test post content"
    post.post_type = "text"
    post.created_at = "2025-04-30T13:42:04"
    post.like_count = 5
    post.user = Mock(spec=User)
    post.user.id = 1
    post.user.username = "testuser"
    post.user.profile_picture = "profile.jpg"
    post.hashtags = []
    return post

@pytest.fixture
def mock_user():
    user = Mock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.profile_picture = "profile.jpg"
    return user

def test_validate_post_ownership_success(mock_db, mock_post):
    # Setup
    mock_db.query.return_value.filter.return_value.first.return_value = mock_post

    # Execute
    result = validate_post_ownership(post_id=1, user_id=1, db=mock_db)

    # Assert
    assert result == mock_post
    mock_db.query.assert_called_once_with(Post)
    mock_db.query.return_value.filter.assert_called_once()

def test_validate_post_ownership_not_found(mock_db):
    # Setup
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Execute and Assert
    with pytest.raises(HTTPException) as exc_info:
        validate_post_ownership(post_id=999, user_id=1, db=mock_db)
    
    assert exc_info.value.status_code == 404
    assert "Post not found or not authorized" in str(exc_info.value.detail)

@patch('utils.post_utils.get_user_like_status')
@patch('utils.post_utils.get_post_additional_data')
def test_prepare_post_response(mock_additional_data, mock_like_status, mock_db, mock_post, mock_user):
    # Setup
    mock_like_status.return_value = True
    mock_additional_data.return_value = {"additional": "data"}
    mock_db.query.return_value.filter.return_value.count.return_value = 3

    # Execute
    result = prepare_post_response(mock_post, mock_user, mock_db)

    # Assert
    assert result["id"] == mock_post.id
    assert result["user_id"] == mock_post.user_id
    assert result["content"] == mock_post.content
    assert result["user"]["username"] == mock_post.user.username
    assert result["total_likes"] == mock_post.like_count
    assert result["user_liked"] is True
    assert result["comment_count"] == 3
    assert result["additional"] == "data"

@pytest.mark.asyncio
@patch('utils.post_utils.upload_to_cloudinary')
async def test_handle_media_upload(mock_upload):
    # Setup
    mock_file = Mock(spec=UploadFile)
    mock_file.file = Mock()
    mock_upload.return_value = {
        "secure_url": "https://example.com/image.jpg",
        "resource_type": "image"
    }

    # Execute
    result = await handle_media_upload(mock_file, "test_folder")

    # Assert
    assert result["secure_url"] == "https://example.com/image.jpg"
    assert result["resource_type"] == "image"
    mock_upload.assert_called_once_with(mock_file.file, folder_name="test_folder")

@patch('utils.post_utils.Post')
@patch('utils.post_utils.extract_hashtags')
def test_create_base_post_without_hashtags(mock_extract_hashtags, mock_post_class, mock_db):
    # Setup
    mock_extract_hashtags.return_value = []
    mock_post = Mock()
    mock_post.content = "Regular post content"
    mock_post.hashtags = []
    mock_post_class.return_value = mock_post
    
    mock_db.query.return_value.all.return_value = []
    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock()

    # Execute
    result = create_base_post(mock_db, user_id=1, content="Regular post content", post_type="text")

    # Assert
    mock_post_class.assert_called_once_with(
        user_id=1,
        content="Regular post content",
        post_type="text"
    )
    mock_db.add.assert_called_once_with(mock_post)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_post)

@patch('utils.post_utils.Post')
@patch('utils.post_utils.extract_hashtags')
def test_create_base_post_with_hashtags(mock_extract_hashtags, mock_post_class, mock_db):
    # Setup
    mock_extract_hashtags.return_value = ["TestUniversity"]
    
    # Mock universities query
    mock_universities = [("TestUniversity",)]
    mock_db.query.return_value.all.return_value = mock_universities
    
    # Mock existing hashtag
    existing_hashtag = Mock(spec=Hashtag)
    existing_hashtag.name = "testuniversity"
    existing_hashtag.usage_count = 1
    mock_db.query.return_value.filter_by.return_value.first.return_value = existing_hashtag

    # Mock post
    mock_post = Mock()
    mock_post.content = "Post with #TestUniversity hashtag"
    mock_post.hashtags = []
    mock_post_class.return_value = mock_post
    
    # Execute
    result = create_base_post(
        mock_db,
        user_id=1,
        content="Post with #TestUniversity hashtag",
        post_type="text"
    )

    # Assert
    mock_post_class.assert_called_once_with(
        user_id=1,
        content="Post with #TestUniversity hashtag",
        post_type="text"
    )
    assert existing_hashtag in mock_post.hashtags
    mock_db.add.assert_called_with(mock_post)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_post)