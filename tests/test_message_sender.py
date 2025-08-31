#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for handlers/message_sender.py
"""
import os
import sys
import pytest
from unittest.mock import patch, Mock

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import asyncio

def test_send_scheduled_message_weather():
    """Test sending scheduled weather message"""
    # Import the module
    from handlers import message_sender
    
    # Create mock bot
    mock_bot = Mock()
    
    # Mock database functions
    with patch('handlers.message_sender.get_db') as mock_get_db, \
         patch('handlers.message_sender.weather') as mock_weather, \
         patch('handlers.message_sender.holidays') as mock_holidays, \
         patch('handlers.message_sender.disconnections') as mock_disconnections:
        
        # Mock database session
        mock_db_session = Mock()
        mock_get_db.return_value.__next__ = Mock(return_value=mock_db_session)
        mock_scheduler_setting = Mock()
        mock_scheduler_setting.is_enabled = True
        mock_scheduler_setting.target_groups = None  # No specific groups
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_scheduler_setting
        mock_group = Mock()
        mock_group.group_id = "test_group_id"
        mock_group.group_name = "Test Group"
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_group]
        
        # Mock external APIs
        mock_weather.get_weather.return_value = {
            'description': 'clear sky',
            'temperature': 25.5,
            'feels_like': 27.0,
            'humidity': 65,
            'wind_speed': 3.5
        }
        mock_holidays.get_holidays.return_value = []
        mock_disconnections.get_disconnections.return_value = []
        
        # Mock bot.send_message to avoid actual sending
        mock_bot.send_message = Mock()
        
        # Run the async function in a new event loop
        async def run_test():
            await message_sender.send_scheduled_message(mock_bot, "weather")
        
        # Create a new event loop for this test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_test())
        finally:
            loop.close()
        
        # Assertions
        mock_db_session.query.assert_called()
        # Just check that get_weather was called (don't check exact count due to error handling)
        assert mock_weather.get_weather.called

def test_send_scheduled_message_disabled():
    """Test sending scheduled message when disabled"""
    # Import the module
    from handlers import message_sender
    
    # Create mock bot
    mock_bot = Mock()
    
    # Mock database functions
    with patch('handlers.message_sender.get_db') as mock_get_db:
        # Mock database session
        mock_db_session = Mock()
        mock_get_db.return_value.__next__ = Mock(return_value=mock_db_session)
        mock_scheduler_setting = Mock()
        mock_scheduler_setting.is_enabled = False
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_scheduler_setting
        
        # Run the async function in a new event loop
        async def run_test():
            await message_sender.send_scheduled_message(mock_bot, "weather")
        
        # Create a new event loop for this test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_test())
        finally:
            loop.close()
        
        # Assertions
        mock_db_session.query.assert_called()

if __name__ == "__main__":
    pytest.main([__file__])