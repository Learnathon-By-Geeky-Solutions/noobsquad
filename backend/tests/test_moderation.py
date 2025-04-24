import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add the backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1])) 
from AI.moderation import get_classifier, moderate_text

@pytest.fixture
def mock_classifier():
    """Fixture to mock the classifier returned by pipeline"""
    mock = MagicMock()
    return mock

def test_get_classifier_initialization():
    """Test that get_classifier initializes the classifier only once"""
    with patch('AI.moderation.pipeline') as mock_pipe:
        # Create a mock classifier
        mock_classifier = MagicMock()
        mock_pipe.return_value = mock_classifier
        
        # First call should initialize the classifier
        classifier1 = get_classifier()
        assert mock_pipe.call_count == 1
        assert classifier1 is mock_classifier
        
        # Second call should reuse the existing classifier
        classifier2 = get_classifier()
        assert mock_pipe.call_count == 1  # Still just one call
        assert classifier1 is classifier2  # Same instance

def test_moderate_text_positive():
    """Test moderate_text with positive text"""
    # Reset the classifier to ensure we start fresh
    with patch('AI.moderation._classifier', None):
        with patch('AI.moderation.get_classifier') as mock_get_classifier:
            # Create a mock classifier
            mock_classifier = MagicMock()
            mock_classifier.return_value = [{'label': 'POSITIVE', 'score': 0.9}]
            mock_get_classifier.return_value = mock_classifier
            
            # Call the function with a positive text
            result = moderate_text("This is a great day!")
            
            # Verify the mock classifier was used
            mock_get_classifier.assert_called_once()
            mock_classifier.assert_called_once()
            
            # Since the label is POSITIVE, moderate_text should return False (not toxic)
            assert result is False

def test_moderate_text_negative():
    """Test moderate_text with negative/toxic text"""
    # Reset the classifier to ensure we start fresh
    with patch('AI.moderation._classifier', None):
        with patch('AI.moderation.get_classifier') as mock_get_classifier:
            # Create a mock classifier
            mock_classifier = MagicMock()
            mock_classifier.return_value = [{'label': 'NEGATIVE', 'score': 0.8}]
            mock_get_classifier.return_value = mock_classifier
            
            # Call the function with a negative text
            result = moderate_text("This is terrible content!")
            
            # Verify the mock classifier was used
            mock_get_classifier.assert_called_once()
            mock_classifier.assert_called_once()
            
            # Since the label is NEGATIVE, moderate_text should return True (toxic)
            assert result is True

def test_moderate_text_empty():
    """Test moderate_text with empty text"""
    # Reset the classifier to ensure we start fresh
    with patch('AI.moderation._classifier', None):
        with patch('AI.moderation.get_classifier') as mock_get_classifier:
            # Create a mock classifier
            mock_classifier = MagicMock()
            mock_classifier.return_value = [{'label': 'POSITIVE', 'score': 0.5}]
            mock_get_classifier.return_value = mock_classifier
            
            # Call with empty text
            result = moderate_text("")
            
            # Verify the mock classifier was used
            mock_get_classifier.assert_called_once()
            mock_classifier.assert_called_once()
            
            # Should return the result based on the mock
            assert result is False

@pytest.mark.parametrize("text,label,expected", [
    ("Great content", "POSITIVE", False),
    ("Terrible content", "NEGATIVE", True),
    ("Neutral content", "POSITIVE", False),
    ("Bad language", "NEGATIVE", True),
])
def test_moderate_text_parametrized(text, label, expected):
    """Parametrized test for moderate_text with various inputs"""
    # Reset the classifier to ensure we start fresh
    with patch('AI.moderation._classifier', None):
        with patch('AI.moderation.get_classifier') as mock_get_classifier:
            # Create a mock classifier
            mock_classifier = MagicMock()
            mock_classifier.return_value = [{'label': label, 'score': 0.7}]
            mock_get_classifier.return_value = mock_classifier
            
            # Call moderate_text
            result = moderate_text(text)
            
            # Verify the result
            assert result is expected
            mock_get_classifier.assert_called_once()
            mock_classifier.assert_called_once()

def test_moderate_text_with_long_content():
    """Test moderate_text with very long text"""
    # Create a very long text
    long_text = "This is a test. " * 100
    
    # Reset the classifier to ensure we start fresh
    with patch('AI.moderation._classifier', None):
        with patch('AI.moderation.get_classifier') as mock_get_classifier:
            # Create a mock classifier
            mock_classifier = MagicMock()
            mock_classifier.return_value = [{'label': 'POSITIVE', 'score': 0.6}]
            mock_get_classifier.return_value = mock_classifier
            
            # Call the function
            result = moderate_text(long_text)
            
            # Verify it was processed correctly
            mock_get_classifier.assert_called_once()
            mock_classifier.assert_called_once()
            assert result is False

@pytest.mark.skipif(True, reason="Integration test that requires actual model")
def test_moderate_text_integration():
    """Integration test with actual model - skipped by default"""
    # Test with actual positive text
    assert moderate_text("I love this beautiful day!") is False
    
    # Test with actual negative text
    assert moderate_text("I hate everything about this terrible product!") is True

def test_moderate_text_with_special_characters():
    """Test moderate_text with special characters"""
    special_text = "!@#$%^&*()_+<>?:"
    
    # Reset the classifier to ensure we start fresh
    with patch('AI.moderation._classifier', None):
        with patch('AI.moderation.get_classifier') as mock_get_classifier:
            # Create a mock classifier
            mock_classifier = MagicMock()
            mock_classifier.return_value = [{'label': 'POSITIVE', 'score': 0.5}]
            mock_get_classifier.return_value = mock_classifier
            
            # Call the function
            result = moderate_text(special_text)
            
            # Verify it was processed correctly
            mock_get_classifier.assert_called_once()
            mock_classifier.assert_called_once()
            assert result is False
