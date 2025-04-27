import pytest
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from AI.moderation import moderate_text
from fastapi import HTTPException

def test_moderate_text_with_clean_content():
    """Test moderation with clean text"""
    text = "This is a nice and clean message"
    assert moderate_text(text) is False

def test_moderate_text_with_profanity():
    """Test moderation with text containing profanity"""
    text = "This message contains bad words like hell"
    assert moderate_text(text) is True

def test_moderate_text_with_empty_string():
    """Test moderation with empty string"""
    assert moderate_text("") is False

def test_moderate_text_with_none():
    """Test moderation with None input"""
    assert moderate_text(None) is False

def test_moderate_text_with_non_string():
    """Test moderation with non-string input"""
    assert moderate_text(123) is False

def test_moderate_text_with_special_characters():
    """Test moderation with special characters"""
    text = "Hello! @#$%^&*()_+ World"
    assert moderate_text(text) is False

def test_moderate_text_with_multiple_languages():
    """Test moderation with text in different languages"""
    text = "Hello こんにちは Bonjour"
    assert moderate_text(text) is False
