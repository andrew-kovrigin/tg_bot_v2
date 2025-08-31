#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for config.py
"""
import os
import sys
import pytest

# Add the databases directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'databases'))

import config

def test_config_constants():
    """Test that config constants are properly defined"""
    # Test database URL
    assert config.DATABASE_URL == 'sqlite:///bot_data.db'
    
    # Test disconnections URL
    assert config.DISCONNECTIONS_URL == 'http://93.92.65.26/aspx/Gorod.htm'
    
    # Test holidays RSS URL
    assert config.HOLIDAYS_RSS_URL == 'https://www.calend.ru/rss/russtate.rss'
    
    # Test scheduler flag file
    assert config.SCHEDULER_FLAG_FILE == 'scheduler_update.flag'
    
    # Test disconnections HTML file
    assert config.DISCONNECTIONS_HTML_FILE == 'parse.html'
    
    # Test OpenWeatherMap coordinates
    assert config.KRASNOYARSK_LAT == 56.0155
    assert config.KRASNOYARSK_LON == 92.8692

def test_hash_password():
    """Test password hashing function"""
    password = "test_password"
    hashed = config.hash_password(password)
    assert isinstance(hashed, str)
    assert len(hashed) == 128  # SHA512 hash length
    assert hashed == config.hash_password(password)  # Consistent hashing

if __name__ == "__main__":
    pytest.main([__file__])