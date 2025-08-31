#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for handlers/main.py
"""
import os
import sys
import pytest
from unittest.mock import patch, Mock, AsyncMock

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test that handlers/main.py imports correctly"""
    try:
        with patch('aiogram.Bot') as mock_bot_class, \
             patch('aiogram.Dispatcher') as mock_dispatcher_class, \
             patch('apscheduler.schedulers.asyncio.AsyncIOScheduler') as mock_scheduler_class:
            
            mock_bot_instance = Mock()
            mock_bot_class.return_value = mock_bot_instance
            
            mock_dispatcher_instance = Mock()
            mock_dispatcher_class.return_value = mock_dispatcher_instance
            
            mock_scheduler_instance = Mock()
            mock_scheduler_class.return_value = mock_scheduler_instance
            
            from handlers import main
            assert hasattr(main, 'register_handlers')
    except Exception as e:
        pytest.fail(f"Failed to import handlers/main.py: {e}")

def test_scheduler_functions():
    """Test scheduler function definitions"""
    with patch('aiogram.Bot'), \
         patch('aiogram.Dispatcher'), \
         patch('apscheduler.schedulers.asyncio.AsyncIOScheduler'):
        
        from handlers import main
        
        # Check that scheduler functions exist
        assert hasattr(main, 'send_daily_message')
        assert hasattr(main, 'send_weather_report')
        assert hasattr(main, 'send_holidays_report')
        assert hasattr(main, 'send_disconnections_report')

def test_register_handlers():
    """Test handler registration function"""
    with patch('aiogram.Bot'), \
         patch('aiogram.Dispatcher'), \
         patch('apscheduler.schedulers.asyncio.AsyncIOScheduler'):
        
        from handlers import main
        
        # Check that register_handlers function exists
        assert hasattr(main, 'register_handlers')

if __name__ == "__main__":
    pytest.main([__file__])