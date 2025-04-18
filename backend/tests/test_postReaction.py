import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import uuid
from zoneinfo import ZoneInfo

# Mock HuggingFaceEndpoint before importing main to avoid API token error
with patch("langchain_huggingface.HuggingFaceEndpoint", MagicMock()) as mock_hf_endpoint:
    mock_hf_endpoint.return_value = MagicMock()
    mock_hf_endpoint.return_value.predict.return_value = "mocked response"
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from main import app
    from models.post import Post, Like, Comment, PostMedia, PostDocument, Event, Share
    from models.user import User
    from models.post import EventAttendee
    from routes import postReaction

client = TestClient(app)

# Fake user and fake post for testing
fake_user = User(id=1, username="testuser", email="test@example.com", profile_picture="user.jpg")
fake_other_user = User(id=2, username="otheruser", email="other@example.com")

fake_post = Post(
    id=2,
    user_id=1,
    content="This is a test post",
    post_type="text",
    created_at=datetime.now(ZoneInfo("UTC")),
    like_count=5,
    event=None,
    user=fake_user
)

# Fake media post
fake_media_post = Post(
    id=3,
    user_id=1,
    content="Media post",
    post_type="media",
    created_at=datetime.now(ZoneInfo("UTC")),
    like_count=0,
    event=None,
    user=fake_user
)

# Fake document post
fake_document_post = Post(
    id=4,
    user_id=1,
    content="Document post",
    post_type="document",
    created_at=datetime.now(ZoneInfo("UTC")),
    like_count=0,
    event=None,
    user=fake_user
)

# Fake event post
fake_event_post = Post(
    id=5,
    user_id=1,
    content="Event post",
    post_type="event",
    created_at=datetime.now(ZoneInfo("UTC")),
    like_count=0,
    event=None,
    user=fake_user
)

# Fake like for testing
fake_like = Like(
    id=1,
    user_id=fake_user.id,
    post_id=2,
    comment_id=None,
    created_at=datetime.now(ZoneInfo("UTC"))
)

# Fake comment for testing
fake_comment = Comment(
    id=1,
    user_id=fake_user.id,
    post_id=2,
    content="This is a test comment",
    parent_id=None,
    created_at=datetime.now(ZoneInfo("UTC"))
)

# Fake share for testing
fake_share = Share(
    id=1,
    user_id=fake_user.id,
    post_id=2,
    share_token="mocked-uuid",
    created_at=datetime.now(ZoneInfo("UTC"))
)

# Fake media for testing
fake_media = PostMedia(
    id=1,
    post_id=3,
    media_url="media.jpg"
)

# Fake document for testing
fake_document = PostDocument(
    id=1,
    post_id=4,
    document_url="document.pdf"
)

# Fake event for testing
fake_event = Event(
    id=1,
    post_id=5,
    title="Test Event",
    description="Event description",
    event_datetime=datetime.now(ZoneInfo("UTC")),
    location="Test Location"
)

# Fake event attendee for testing
fake_attendee = EventAttendee(
    id=1,
    event_id=1,
    user_id=fake_user.id,
    status="going"
)

# Fixture to override dependencies for all tests
@pytest.fixture
def override_dependencies(monkeypatch):
    mock_session = MagicMock(spec=Session)

    # Mock database operations
    def mock_add(obj):
        if isinstance(obj, (Like, Comment, Share, EventAttendee)):
            obj.id = 1  # Simulate database assigning an ID
        return None

    def mock_refresh(obj):
        if isinstance(obj, Comment):
            obj.post = fake_post  # Simulate Comment.post relationship
        elif isinstance(obj, Share):
            obj.post = fake_post  # Simulate Share.post relationship
        return None

    mock_session.add.side_effect = mock_add
    mock_session.delete.return_value = None
    mock_session.commit.return_value = None
    mock_session.refresh.side_effect = mock_refresh

    # Mock queries
    mock_post_query = MagicMock()
    mock_post_query.filter.return_value.first.return_value = fake_post

    mock_like_query = MagicMock()
    mock_like_query.filter.return_value.first.return_value = None

    mock_comment_query = MagicMock()
    mock_comment_query.filter.return_value.first.return_value = None

    mock_user_query = MagicMock()
    mock_user_query.filter.return_value.first.return_value = fake_other_user

    mock_share_query = MagicMock()
    mock_share_query.filter.return_value.first.return_value = None

    mock_media_query = MagicMock()
    mock_media_query.filter.return_value.first.return_value = None

    mock_document_query = MagicMock()
    mock_document_query.filter.return_value.first.return_value = None

    mock_event_query = MagicMock()
    mock_event_query.filter.return_value.first.return_value = None

    mock_attendee_query = MagicMock()
    mock_attendee_query.filter.return_value.first.return_value = None
    mock_attendee_query.filter.return_value.all.return_value = []

    mock_session.query.side_effect = lambda model: (
        mock_post_query if model == Post else
        mock_like_query if model == Like else
        mock_comment_query if model == Comment else
        mock_user_query if model == User else
        mock_share_query if model == Share else
        mock_media_query if model == PostMedia else
        mock_document_query if model == PostDocument else
        mock_event_query if model == Event else
        mock_attendee_query if model == EventAttendee else
        MagicMock()
    )

    # Mock notify_if_not_self and create_notification
    mock_notify_if_not_self = MagicMock()
    mock_create_notification = MagicMock()
    monkeypatch.setattr(postReaction, "notify_if_not_self", mock_notify_if_not_self)
    monkeypatch.setattr(postReaction, "create_notification", mock_create_notification)

    # Mock uuid4 for share_token
    mock_uuid = MagicMock()
    mock_uuid.return_value = "mocked-uuid"
    monkeypatch.setattr("uuid.uuid4", mock_uuid)

    def _get_db_override():
        return mock_session

    def _get_current_user_override():
        return fake_user

    app.dependency_overrides[postReaction.get_db] = _get_db_override
    app.dependency_overrides[postReaction.get_current_user] = _get_current_user_override

    yield mock_session, mock_notify_if_not_self, mock_create_notification

    app.dependency_overrides.clear()

# Test for adding a like
def test_like_action_add(override_dependencies):
    mock_session, mock_notify_if_not_self, mock_create_notification = override_dependencies

    # Mock Post and Like queries
    mock_post_query = MagicMock()
    mock_post_query.filter.return_value.first.return_value = fake_post
    mock_like_query = MagicMock()
    mock_like_query.filter.return_value.first.return_value = None  # No existing like
    mock_session.query.side_effect = lambda model: (
        mock_post_query if model == Post else
        mock_like_query if model == Like else
        MagicMock()
    )

    # Send request to add like
    response = client.post("/interactions/like", json={"post_id": 2, "comment_id": None})
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Like added successfully"
    assert data["user_liked"] is True
    assert data["total_likes"] == 6  # like_count: 5 -> 6
    assert data["id"] == 1
    assert data["user_id"] == fake_user.id
    assert data["post_id"] == 2
    assert data["comment_id"] is None
    
    # Ensure database operations are called
    mock_session.add.assert_called()
    mock_session.commit.assert_called()
    mock_session.refresh.assert_called()
    # Notification may be called depending on endpoint logic
    mock_create_notification.assert_not_called()  # Assume no notification for self

# Test for removing a like
def test_like_action_remove(override_dependencies):
    mock_session, mock_notify_if_not_self, mock_create_notification = override_dependencies

    # Mock Post and Like queries
    mock_post_query = MagicMock()
    mock_post_query.filter.return_value.first.return_value = fake_post
    mock_like_query = MagicMock()
    mock_like_query.filter.return_value.first.return_value = fake_like  # Existing like
    mock_session.query.side_effect = lambda model: (
        mock_post_query if model == Post else
        mock_like_query if model == Like else
        MagicMock()
    )

    # Send request to remove like
    response = client.post("/interactions/like", json={"post_id": 2, "comment_id": None})
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Like removed"
    assert data["user_liked"] is False
    assert data["total_likes"] == 5  # like_count: 5 -> 4, then max(0, 4 - 1) = 3
    assert data["id"] == fake_like.id
    assert data["user_id"] == fake_user.id
    assert data["post_id"] == 2
    assert data["comment_id"] is None
    
    # Ensure database operations are called
    mock_session.delete.assert_called()
    mock_session.commit.assert_called()
    # Notification may be called depending on endpoint logic
    mock_create_notification.assert_not_called()  # Assume no notification for self

# Test for missing post_id or comment_id
def test_like_action_missing_post_or_comment(override_dependencies):
    mock_session, mock_notify_if_not_self, mock_create_notification = override_dependencies

    # Send request with neither post_id nor comment_id
    response = client.post("/interactions/like", json={"post_id": None, "comment_id": None})
    
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Either post_id or comment_id must be provided."

# Test for creating a root comment
def test_comment_post_create(override_dependencies):
    mock_session, mock_notify_if_not_self, mock_create_notification = override_dependencies

    # Mock Post and Comment queries
    mock_post_query = MagicMock()
    mock_post_query.filter.return_value.first.return_value = fake_post
    mock_comment_query = MagicMock()
    mock_comment_query.filter.return_value.first.return_value = None
    mock_session.query.side_effect = lambda model: (
        mock_post_query if model == Post else
        mock_comment_query if model == Comment else
        MagicMock()
    )

    # Send request to create a comment
    response = client.post("/interactions/2/comment", json={"post_id": 2, "content": "This is a test comment", "parent_id": None})
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["user_id"] == fake_user.id
    assert data["post_id"] == 2
    assert data["content"] == "This is a test comment"
    assert data["parent_id"] is None
    assert "created_at" in data

    # Ensure database operations are called
    mock_session.add.assert_called()
    mock_session.commit.assert_called()
    mock_session.refresh.assert_called()
    # Notification may be called depending on endpoint logic
    mock_create_notification.assert_not_called()  # Assume no notification for self

# Test for error when parent_id is provided
def test_comment_post_with_parent_id(override_dependencies):
    mock_session, mock_notify_if_not_self, mock_create_notification = override_dependencies

    # Mock Post and Comment queries
    mock_post_query = MagicMock()
    mock_post_query.filter.return_value.first.return_value = fake_post
    mock_comment_query = MagicMock()
    mock_comment_query.filter.return_value.first.return_value = None
    mock_session.query.side_effect = lambda model: (
        mock_post_query if model == Post else
        mock_comment_query if model == Comment else
        MagicMock()
    )

    # Send request with parent_id
    response = client.post("/interactions/2/comment", json={"post_id": 2, "content": "Invalid comment", "parent_id": 1})
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Root comment cannot have a parent_id."
    
    # Ensure no database operations or notifications are called
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()
    mock_session.refresh.assert_not_called()
    mock_notify_if_not_self.assert_not_called()
    mock_create_notification.assert_not_called()

# Test for sharing a post
def test_share_post(override_dependencies):
    mock_session, mock_notify_if_not_self, mock_create_notification = override_dependencies

    # Mock Post and User queries
    mock_post_query = MagicMock()
    mock_post_query.filter.return_value.first.return_value = fake_post
    mock_user_query = MagicMock()
    mock_user_query.filter.return_value.first.return_value = fake_user
    mock_session.query.side_effect = lambda model: (
        mock_post_query if model == Post else
        mock_user_query if model == User else
        MagicMock()
    )

    # Send request to share post
    response = client.post("/interactions/2/share", json={"post_id": 2})
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["user_id"] == fake_user.id
    assert data["post_id"] == 2
    assert data["share_link"] == "http://localhost:5173/share/mocked-uuid"
    assert "created_at" in data

    # Ensure database operations are called
    mock_session.add.assert_called()
    mock_session.commit.assert_called()
    mock_session.refresh.assert_called()
    # Check create_notification directly
    mock_create_notification.assert_not_called()  # No notification since user_id == post.user_id

# Test for sharing a non-existent post
def test_share_post_not_found(override_dependencies):
    mock_session, mock_notify_if_not_self, mock_create_notification = override_dependencies

    # Mock Post query to return None
    mock_post_query = MagicMock()
    mock_post_query.filter.return_value.first.return_value = None
    mock_session.query.side_effect = lambda model: mock_post_query if model == Post else MagicMock()

    # Send request to share non-existent post
    response = client.post("/interactions/999/share", json={"post_id": 999})
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found."
    # Ensure no database operations or notifications are called
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()
    mock_session.refresh.assert_not_called()
    mock_notify_if_not_self.assert_not_called()
    mock_create_notification.assert_not_called()

# Test for sharing with notification
def test_share_post_with_notification(override_dependencies):
    mock_session, mock_notify_if_not_self, mock_create_notification = override_dependencies

    # Mock Post and User queries
    fake_post.user_id = 2  # Different user to trigger notification
    mock_post_query = MagicMock()
    mock_post_query.filter.return_value.first.return_value = fake_post
    mock_user_query = MagicMock()
    mock_user_query.filter.return_value.first.return_value = fake_other_user
    mock_session.query.side_effect = lambda model: (
        mock_post_query if model == Post else
        mock_user_query if model == User else
        MagicMock()
    )

    # Send request to share post
    response = client.post("/interactions/2/share", json={"post_id": 2})
    
    assert response.status_code == 200
    # Reset fake_post.user_id
    fake_post.user_id = 1
    # Ensure notification is called
    mock_create_notification.assert_called_with(
        mock_session,
        recipient_id=fake_other_user.id,
        actor_id=fake_user.id,
        notif_type="share",
        post_id=fake_post.id
    )

# Test for getting a shared text post
def test_get_shared_post(override_dependencies):
    mock_session, mock_notify_if_not_self, mock_create_notification = override_dependencies

    # Mock Share, Post, and Like queries
    mock_share_query = MagicMock()
    mock_share_query.filter.return_value.first.return_value = fake_share
    mock_post_query = MagicMock()
    mock_post_query.filter.return_value.first.return_value = fake_post
    mock_like_query = MagicMock()
    mock_like_query.filter.return_value.first.return_value = None
    mock_session.query.side_effect = lambda model: (
        mock_share_query if model == Share else
        mock_post_query if model == Post else
        mock_like_query if model == Like else
        MagicMock()
    )

    # Send request to get shared post
    response = client.get("/interactions/share/mocked-uuid")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fake_post.id
    assert data["post_type"] == "text"
    assert data["content"] == fake_post.content
    assert data["user"]["id"] == fake_user.id
    assert data["user"]["username"] == fake_user.username
    assert data["user"]["profile_picture"] == f"http://127.0.0.1:8000/uploads/profile_pictures/{fake_user.profile_picture}"
    assert data["total_likes"] == fake_post.like_count
    assert data["user_liked"] is False
    assert "created_at" in data

# Test for getting a shared media post
def test_get_shared_media_post(override_dependencies):
    mock_session, mock_notify_if_not_self, mock_create_notification = override_dependencies

    # Mock Share, Post, Like, and PostMedia queries
    mock_share_query = MagicMock()
    mock_share_query.filter.return_value.first.return_value = Share(id=1, user_id=fake_user.id, post_id=3, share_token="mocked-uuid")
    mock_post_query = MagicMock()
    mock_post_query.filter.return_value.first.return_value = fake_media_post
    mock_like_query = MagicMock()
    mock_like_query.filter.return_value.first.return_value = None
    mock_media_query = MagicMock()
    mock_media_query.filter.return_value.first.return_value = fake_media
    mock_session.query.side_effect = lambda model: (
        mock_share_query if model == Share else
        mock_post_query if model == Post else
        mock_like_query if model == Like else
        mock_media_query if model == PostMedia else
        MagicMock()
    )

    # Send request to get shared media post
    response = client.get("/interactions/share/mocked-uuid")
    
    assert response.status_code == 200
    data = response.json()
    assert data["post_type"] == "media"
    assert data["media_url"] == f"http://127.0.0.1:8000/uploads/media/{fake_media.media_url}"

# Test for getting a shared document post
def test_get_shared_document_post(override_dependencies):
    mock_session, mock_notify_if_not_self, mock_create_notification = override_dependencies

    # Mock Share, Post, Like, and PostDocument queries
    mock_share_query = MagicMock()
    mock_share_query.filter.return_value.first.return_value = Share(id=1, user_id=fake_user.id, post_id=4, share_token="mocked-uuid")
    mock_post_query = MagicMock()
    mock_post_query.filter.return_value.first.return_value = fake_document_post
    mock_like_query = MagicMock()
    mock_like_query.filter.return_value.first.return_value = None
    mock_document_query = MagicMock()
    mock_document_query.filter.return_value.first.return_value = fake_document
    mock_session.query.side_effect = lambda model: (
        mock_share_query if model == Share else
        mock_post_query if model == Post else
        mock_like_query if model == Like else
        mock_document_query if model == PostDocument else
        MagicMock()
    )

    # Send request to get shared document post
    response = client.get("/interactions/share/mocked-uuid")
    
    assert response.status_code == 200
    data = response.json()
    assert data["post_type"] == "document"
    assert data["document_url"] == f"http://127.0.0.1:8000/uploads/document/{fake_document.document_url}"

# Test for getting a shared event post
def test_get_shared_event_post(override_dependencies):
    mock_session, mock_notify_if_not_self, mock_create_notification = override_dependencies

    # Mock Share, Post, Like, and Event queries
    mock_share_query = MagicMock()
    mock_share_query.filter.return_value.first.return_value = Share(id=1, user_id=fake_user.id, post_id=5, share_token="mocked-uuid")
    mock_post_query = MagicMock()
    mock_post_query.filter.return_value.first.return_value = fake_event_post
    mock_like_query = MagicMock()
    mock_like_query.filter.return_value.first.return_value = None
    mock_event_query = MagicMock()
    mock_event_query.filter.return_value.first.return_value = fake_event
    mock_session.query.side_effect = lambda model: (
        mock_share_query if model == Share else
        mock_post_query if model == Post else
        mock_like_query if model == Like else
        mock_event_query if model == Event else
        MagicMock()
    )

    # Send request to get shared event post
    response = client.get("/interactions/share/mocked-uuid")
    
    assert response.status_code == 200
    data = response.json()
    assert data["post_type"] == "event"
    assert data["event"]["title"] == fake_event.title
    assert data["event"]["description"] == fake_event.description
    assert data["event"]["location"] == fake_event.location

# Test for invalid share token
def test_get_shared_post_invalid_token(override_dependencies):
    mock_session, mock_notify_if_not_self, mock_create_notification = override_dependencies

    # Mock Share query to return None
    mock_share_query = MagicMock()
    mock_share_query.filter.return_value.first.return_value = None
    mock_session.query.side_effect = lambda model: mock_share_query if model == Share else MagicMock()

    # Send request with invalid share token
    response = client.get("/interactions/share/invalid-uuid")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Invalid or expired share link"

# # Test for RSVPing to an event
def test_rsvp_event(override_dependencies):
    mock_session, mock_notify_if_not_self, mock_create_notification = override_dependencies

    # Mock Event and EventAttendee queries
    mock_event_query = MagicMock()
    mock_event_query.filter.return_value.first.return_value = fake_event
    mock_attendee_query = MagicMock()
    mock_attendee_query.filter.return_value.first.return_value = None
    mock_session.query.side_effect = lambda model: (
        mock_event_query if model == Event else
        mock_attendee_query if model == EventAttendee else
        MagicMock()
    )

    # Send request to RSVP
    response = client.post("/interactions/event/1/rsvp", json={"event_id": 1,"status": "going"})

    # Debugging output
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Content: {response.text}")  # This will print the body of the response, which may include error details

    # You can also print the request data to make sure it was correctly sent
    print(f"Request JSON: {{'status': 'going'}}")

    # Check if there are validation issues with the input data (response.json() may contain error details)
    try:
        response_data = response.json()
        print(f"Response JSON: {response_data}")
    except Exception as e:
        print(f"Error parsing response JSON: {e}")

    # Proceed with assertions if the response is correct
    assert response.status_code == 200, f"Expected 200, but got {response.status_code} instead."

    # Assuming the response is valid, perform additional assertions
    data = response.json()
    assert data["id"] == 1
    assert data["event_id"] == 1
    assert data["user_id"] == fake_user.id
    assert data["status"] == "going"

    # Ensure database operations are called
    mock_session.add.assert_called()
    mock_session.commit.assert_called()


# Test for updating an existing RSVP
def test_rsvp_event_update(override_dependencies):
    mock_session, mock_notify_if_not_self, mock_create_notification = override_dependencies

    # Mock Event and EventAttendee queries
    mock_event_query = MagicMock()
    mock_event_query.filter.return_value.first.return_value = fake_event
    mock_attendee_query = MagicMock()
    mock_attendee_query.filter.return_value.first.return_value = fake_attendee
    mock_session.query.side_effect = lambda model: (
        mock_event_query if model == Event else
        mock_attendee_query if model == EventAttendee else
        MagicMock()
    )

    # Send request to update RSVP
    response = client.post("/interactions/event/1/rsvp", json={"event_id": 1,"status": "interested"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fake_attendee.id
    assert data["status"] == "interested"
    # Ensure no add, but commit is called
    mock_session.add.assert_not_called()
    mock_session.commit.assert_called()

# Test for RSVPing to a non-existent event
def test_rsvp_event_not_found(override_dependencies):
    mock_session, mock_notify_if_not_self, mock_create_notification = override_dependencies

    # Mock Event query to return None
    mock_event_query = MagicMock()
    mock_event_query.filter.return_value.first.return_value = None
    mock_session.query.side_effect = lambda model: mock_event_query if model == Event else MagicMock()

    # Send request to RSVP
    response = client.post("/interactions/event/999/rsvp", json={"event_id": 999,"status": "going"})
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found."
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()

# Test for getting event attendees
def test_get_event_attendees(override_dependencies):
    mock_session, mock_notify_if_not_self, mock_create_notification = override_dependencies

    # Mock EventAttendee query
    mock_attendee_query = MagicMock()
    mock_attendee_query.filter.return_value.all.return_value = [fake_attendee]
    mock_session.query.side_effect = lambda model: mock_attendee_query if model == EventAttendee else MagicMock()

    # Send request to get attendees
    response = client.get("/interactions/event/1/attendees")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == fake_attendee.id
    assert data[0]["event_id"] == fake_attendee.event_id
    assert data[0]["user_id"] == fake_attendee.user_id
    assert data[0]["status"] == fake_attendee.status

# Test for removing an RSVP
def test_remove_rsvp(override_dependencies):
    mock_session, mock_notify_if_not_self, mock_create_notification = override_dependencies

    # Mock EventAttendee query
    mock_attendee_query = MagicMock()
    mock_attendee_query.filter.return_value.first.return_value = fake_attendee
    mock_session.query.side_effect = lambda model: mock_attendee_query if model == EventAttendee else MagicMock()

    # Send request to remove RSVP
    response = client.delete("/interactions/event/1/rsvp")
    
    assert response.status_code == 200
    assert response.json()["message"] == "RSVP removed successfully"
    mock_session.delete.assert_called()
    mock_session.commit.assert_called()

# Test for removing a non-existent RSVP
def test_remove_rsvp_not_found(override_dependencies):
    mock_session, mock_notify_if_not_self, mock_create_notification = override_dependencies

    # Mock EventAttendee query to return None
    mock_attendee_query = MagicMock()
    mock_attendee_query.filter.return_value.first.return_value = None
    mock_session.query.side_effect = lambda model: mock_attendee_query if model == EventAttendee else MagicMock()

    # Send request to remove RSVP
    response = client.delete("/interactions/event/1/rsvp")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "You haven't RSVP'd for this event."
    mock_session.delete.assert_not_called()
    mock_session.commit.assert_not_called()