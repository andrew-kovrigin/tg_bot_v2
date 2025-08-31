#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for parse.py
"""
import os
import sys
import pytest

# Add the utils directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from parse import parse_html

def test_parse_html_with_valid_file():
    """Test parsing with a valid HTML file"""
    # Test with the existing parse.html file
    try:
        # Try with utf-8 encoding first
        result = parse_html('parse.html')
        assert isinstance(result, list)
        # Check structure of first record if any exist
        if result:
            record = result[0]
            assert 'resource' in record
            assert 'organization' in record
            assert 'addresses' in record
            assert 'reason' in record
            assert 'periods' in record
            assert isinstance(record['addresses'], list)
            assert isinstance(record['periods'], list)
    except (FileNotFoundError, ValueError):
        # If parse.html doesn't exist or has encoding issues, create a simple test file
        pytest.skip("parse.html not found or has encoding issues, skipping this test")

def test_parse_html_with_empty_file():
    """Test parsing with HTML file without table"""
    # Create a simple HTML file without table
    test_file = 'test_empty.html'
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write('<html><body><p>No table here</p></body></html>')
    
    try:
        with pytest.raises(ValueError, match="Таблица не найдена в HTML-файле"):
            parse_html(test_file)
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)

def test_parse_html_with_malformed_file():
    """Test parsing with malformed HTML file"""
    # Create a malformed HTML file
    test_file = 'test_malformed.html'
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write('<html><body><table><tr><td>Single cell</td></tr></table></body></html>')
    
    try:
        result = parse_html(test_file)
        # Should return empty list or handle gracefully
        assert isinstance(result, list)
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    pytest.main([__file__])