#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pytest configuration file
"""
import sys
import os
import pytest

# Add the project root and databases directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'databases'))

# Set up test environment with valid token format
os.environ['TELEGRAM_TOKEN'] = '123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ123456789'
os.environ['ADMIN_ID'] = '123456789'
os.environ['OPENWEATHER_API_KEY'] = 'test_api_key'
os.environ['ADMIN_PASSWORD_HASH'] = 'test_hash'

@pytest.fixture
def mock_db():
    """Mock database session fixture"""
    pass