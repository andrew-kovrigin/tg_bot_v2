#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for disconnections.py
"""
import os
import sys
import pytest
from unittest.mock import patch, Mock

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import disconnections

@patch('disconnections.requests.get')
@patch('disconnections.parse_html')
def test_get_disconnections_success(mock_parse_html, mock_requests_get):
    """Test successful disconnections data retrieval"""
    # Mock the requests response
    mock_response = Mock()
    mock_response.text = "<html>test content</html>"
    mock_response.encoding = 'windows-1251'
    mock_requests_get.return_value = mock_response
    
    # Mock the parser
    mock_parse_html.return_value = [
        {
            'addresses': ['Test Address 1', 'Test Address 2'],
            'reason': 'Test reason',
            'periods': ['Test period']
        }
    ]
    
    # Mock database functions
    with patch('disconnections.get_db') as mock_get_db:
        # Mock database session for first call (groups)
        mock_db_session1 = Mock()
        mock_db_session1.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        
        # Mock database session for second call (disconnections)
        mock_db_session2 = Mock()
        mock_db_session2.query.return_value.filter.return_value.delete.return_value = None
        
        # Configure the mock to return different sessions
        mock_get_db.return_value.__next__ = Mock(side_effect=[mock_db_session1, mock_db_session2])
        
        # Test the function
        result = disconnections.get_disconnections()
        
        # Assertions
        assert isinstance(result, list)
        mock_requests_get.assert_called_once()
        mock_parse_html.assert_called_once()

@patch('disconnections.requests.get')
def test_get_disconnections_failure(mock_requests_get):
    """Test disconnections data retrieval failure"""
    # Mock request exception
    mock_requests_get.side_effect = Exception("Network error")
    
    # Test the function
    result = disconnections.get_disconnections()
    
    # Assertions
    assert result == []

@patch('disconnections.requests.get')
@patch('disconnections.parse_html')
def test_get_disconnections_parse_failure(mock_parse_html, mock_requests_get):
    """Test disconnections data retrieval with parsing failure"""
    # Mock the requests response
    mock_response = Mock()
    mock_response.text = "<html>test content</html>"
    mock_response.encoding = 'windows-1251'
    mock_requests_get.return_value = mock_response
    
    # Mock parser exception
    mock_parse_html.side_effect = Exception("Parse error")
    
    # Test the function
    result = disconnections.get_disconnections()
    
    # Assertions
    assert isinstance(result, list)
    assert len(result) == 0

if __name__ == "__main__":
    pytest.main([__file__])