#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for holidays.py
"""
import os
import sys
import pytest
from unittest.mock import patch, Mock

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import holidays

@patch('holidays.feedparser.parse')
def test_get_holidays_success(mock_parse):
    """Test successful holidays data retrieval"""
    # Mock the feedparser response
    mock_entry = Mock()
    mock_entry.title = "New Year"
    mock_entry.published_parsed = (2025, 1, 1, 0, 0, 0, 0, 0, 0)
    mock_entry.summary = "New Year Celebration"
    
    mock_feed = Mock()
    mock_feed.bozo = False
    mock_feed.entries = [mock_entry]
    mock_parse.return_value = mock_feed
    
    # Test the function
    result = holidays.get_holidays()
    
    # Assertions
    assert isinstance(result, list)
    if result:
        holiday = result[0]
        assert 'name' in holiday
        assert 'date' in holiday
        assert 'type' in holiday
        assert 'comment' in holiday
        assert holiday['name'] == "New Year"
        assert holiday['type'] == "Государственный праздник"

@patch('holidays.feedparser.parse')
def test_get_holidays_empty(mock_parse):
    """Test holidays data retrieval with no holidays"""
    # Mock empty feedparser response
    mock_feed = Mock()
    mock_feed.bozo = False
    mock_feed.entries = []
    mock_parse.return_value = mock_feed
    
    # Test the function
    result = holidays.get_holidays()
    
    # Assertions
    assert isinstance(result, list)
    assert len(result) == 0

@patch('holidays.feedparser.parse')
def test_get_holidays_error(mock_parse):
    """Test holidays data retrieval with parsing error"""
    # Mock feedparser error
    mock_feed = Mock()
    mock_feed.bozo = True
    mock_feed.bozo_exception = Exception("Parse error")
    mock_parse.return_value = mock_feed
    
    # Test the function
    result = holidays.get_holidays()
    
    # Assertions
    assert isinstance(result, list)
    assert len(result) == 0

@patch('holidays.feedparser.parse')
def test_get_holidays_exception(mock_parse):
    """Test holidays data retrieval with exception"""
    # Mock exception
    mock_parse.side_effect = Exception("Network error")
    
    # Test the function
    result = holidays.get_holidays()
    
    # Assertions
    assert isinstance(result, list)
    assert len(result) == 0

if __name__ == "__main__":
    pytest.main([__file__])