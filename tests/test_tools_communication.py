"""Tests for communication tools."""

import pytest

from otter_code.tools.communication import ask_question


# Test ask_question adds QUESTION: prefix
def test_ask_question_format():
    """Test that ask_question adds the QUESTION: prefix."""
    question = "What is the meaning of life?"
    result = ask_question(question)
    
    assert result.startswith("QUESTION:")
    assert question in result


# Test ask_question preserves context
def test_ask_question_with_context():
    """Test that ask_question preserves the full question content including context."""
    full_question = """
    ISSUE: I need to understand the data format
    CONTEXT: Working with JSON files in src/data/
    CLARIFICATION NEEDED: What schema should be used?
    """
    result = ask_question(full_question)
    
    assert result.startswith("QUESTION:")
    assert "ISSUE:" in result
    assert "CONTEXT:" in result
    assert "CLARIFICATION NEEDED:" in result


# Test ask_question with simple question
def test_ask_question_simple():
    """Test ask_question with a simple one-line question."""
    question = "How do I implement this feature?"
    result = ask_question(question)
    
    expected = "QUESTION: How do I implement this feature?"
    assert result == expected


# Test ask_question preserves newlines
def test_ask_question_multiline():
    """Test that ask_question preserves multiline formatting."""
    question = "Line 1\nLine 2\nLine 3"
    result = ask_question(question)
    
    assert result == "QUESTION: Line 1\nLine 2\nLine 3"


# Test ask_question with special characters
def test_ask_question_special_characters():
    """Test ask_question handles special characters correctly."""
    question = '''What about symbols: @#$%^&*()_+-=[]{}|;':",./<>?'''
    result = ask_question(question)
    
    assert question in result
    assert result.startswith("QUESTION:")


# Test ask_question with empty string
def test_ask_question_empty():
    """Test ask_question with an empty question."""
    result = ask_question("")
    
    assert result == "QUESTION: "


# Test ask_question returns string type
def test_ask_question_type():
    """Test that ask_question returns a string."""
    result = ask_question("test question")
    
    assert isinstance(result, str)
    assert len(result) > len("QUESTION: ")