#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for handlers/commands.py
"""
import os
import sys
import pytest
from unittest.mock import patch, Mock

# Add the handlers directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'handlers'))

# Import the commands module functions
from commands import register_command_handlers

def test_register_command_handlers():
    """Test that command handlers are registered correctly"""
    # Create mock dispatcher and bot
    mock_dp = Mock()
    mock_bot = Mock()
    
    # Register handlers
    register_command_handlers(mock_dp, mock_bot)
    
    # Check that message handlers were registered
    assert mock_dp.message.call_count >= 6  # At least 6 command handlers
    
    # Check specific command registrations
    calls = [call[0][0].commands for call in mock_dp.message.call_args_list if hasattr(call[0][0], 'commands')]
    commands = [cmd for call_commands in calls for cmd in call_commands]
    
    expected_commands = ['start', 'help', 'weather', 'holidays', 'disconnections', 'add_group']
    for cmd in expected_commands:
        assert cmd in commands

if __name__ == "__main__":
    pytest.main([__file__])