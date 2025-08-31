#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for send_message.py
"""
import os
import sys
import pytest
from unittest.mock import patch, Mock, AsyncMock

# Add the utils directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

import send_message

@pytest.mark.asyncio
async def test_send_message_to_group_success():
    """Test successful message sending to group"""
    with patch('send_message.Bot') as mock_bot_class:
        mock_bot_instance = AsyncMock()
        mock_bot_class.return_value = mock_bot_instance
        mock_bot_instance.send_message = AsyncMock(return_value=True)
        mock_bot_instance.session.close = AsyncMock()
        
        result = await send_message.send_message_to_group("test_group_id", "Test message")
        
        assert result is True
        mock_bot_instance.send_message.assert_called_once_with("test_group_id", "Test message")
        mock_bot_instance.session.close.assert_called_once()

@pytest.mark.asyncio
async def test_send_message_to_group_failure():
    """Test failed message sending to group"""
    with patch('send_message.Bot') as mock_bot_class:
        mock_bot_instance = AsyncMock()
        mock_bot_class.return_value = mock_bot_instance
        mock_bot_instance.send_message = AsyncMock(side_effect=Exception("Send error"))
        mock_bot_instance.session.close = AsyncMock()
        
        result = await send_message.send_message_to_group("test_group_id", "Test message")
        
        assert result is False
        mock_bot_instance.session.close.assert_called_once()

@pytest.mark.asyncio
async def test_send_message_sync():
    """Test synchronous message sending"""
    with patch('send_message.asyncio.run') as mock_run:
        mock_run.return_value = True
        
        result = send_message.send_message_sync("test_group_id", "Test message")
        
        assert result is True
        mock_run.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__])