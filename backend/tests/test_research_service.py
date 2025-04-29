from unittest import TestCase
from unittest.mock import Mock, patch
from fastapi import HTTPException
import pytest
from services.research_service import (
    get_paper_by_id,
    get_user_profile,
    get_research_by_id,
    search_papers,
    save_new_paper,
    save_new_research,
    save_collaboration_request,
    get_pending_collaboration_requests
)

class TestResearchService(TestCase):
    def setUp(self):
        self.mock_db = Mock()
        self.user_id = 1
        self.paper_id = 1
        self.research_id = 1

    def test_get_paper_by_id_success(self):
        mock_paper = Mock()
        self.mock_db.query().filter().first.return_value = mock_paper

        result = get_paper_by_id(self.mock_db, self.paper_id)
        
        self.assertEqual(result, mock_paper)

    def test_get_paper_by_id_not_found(self):
        self.mock_db.query().filter().first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            get_paper_by_id(self.mock_db, self.paper_id)
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Paper not found"

    def test_get_user_profile(self):
        mock_user = Mock()
        self.mock_db.query().filter().first.return_value = mock_user
        
        result = get_user_profile(self.mock_db, self.user_id)
        
        self.assertEqual(result, mock_user)

    def test_get_research_by_id_success(self):
        mock_research = Mock()
        self.mock_db.query().filter().first.return_value = mock_research
        
        result = get_research_by_id(self.mock_db, self.research_id)
        
        self.assertEqual(result, mock_research)

    def test_get_research_by_id_not_found(self):
        self.mock_db.query().filter().first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            get_research_by_id(self.mock_db, self.research_id)
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Research work not found"

    def test_search_papers(self):
        mock_papers = [Mock(), Mock()]
        self.mock_db.query().filter().all.return_value = mock_papers
        
        result = search_papers(self.mock_db, "AI")
        
        self.assertEqual(result, mock_papers)

    def test_save_new_paper(self):
        mock_paper = Mock()
        
        result = save_new_paper(self.mock_db, mock_paper)
        
        self.mock_db.add.assert_called_once_with(mock_paper)
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(mock_paper)
        self.assertEqual(result, mock_paper)

    def test_save_new_research(self):
        mock_research = Mock()
        
        result = save_new_research(self.mock_db, mock_research)
        
        self.mock_db.add.assert_called_once_with(mock_research)
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(mock_research)
        self.assertEqual(result, mock_research)

    def test_save_collaboration_request(self):
        mock_request = Mock()
        
        result = save_collaboration_request(self.mock_db, mock_request)
        
        self.mock_db.add.assert_called_once_with(mock_request)
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(mock_request)
        self.assertEqual(result, mock_request)

    def test_get_pending_collaboration_requests(self):
        mock_requests = [
            Mock(
                id=1,
                research_title="Research 1",
                message="Request 1",
                status="pending",
                requester_username="user1"
            )
        ]
        mock_query = self.mock_db.query.return_value
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_requests
        
        result = get_pending_collaboration_requests(self.mock_db, self.user_id)
        
        self.assertEqual(result, mock_requests)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[0].research_title, "Research 1")
        self.assertEqual(result[0].status, "pending")