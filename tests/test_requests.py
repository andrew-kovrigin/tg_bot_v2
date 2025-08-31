#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for handlers/requests.py
"""
import os
import sys
import pytest
from unittest.mock import patch, Mock

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_request_states_class():
    """Test that RequestStates class is properly defined"""
    # Import from handlers.requests
    from handlers import requests
    
    # Test that RequestStates is a StatesGroup subclass
    from aiogram.fsm.state import StatesGroup, State
    assert issubclass(requests.RequestStates, StatesGroup)
    assert hasattr(requests.RequestStates, 'waiting_for_request')
    assert isinstance(requests.RequestStates.waiting_for_request, State)

def test_register_request_handlers():
    """Test that request handlers are registered correctly"""
    # Import from handlers.requests
    from handlers import requests
    
    # Create mock dispatcher
    mock_dp = Mock()
    
    # Create a mock RequestStates class
    class MockRequestStates:
        waiting_for_request = Mock()
    
    # Register handlers
    requests.register_request_handlers(mock_dp, MockRequestStates)
    
    # Check that message handlers were registered
    assert mock_dp.message.call_count >= 2  # At least 2 handlers (request command and text handler)

if __name__ == "__main__":
    pytest.main([__file__])