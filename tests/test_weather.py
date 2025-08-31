#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for weather.py
"""
import os
import sys
import pytest
from unittest.mock import patch, Mock

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import weather

@patch('weather.requests.get')
def test_get_weather_success(mock_get):
    """Test successful weather data retrieval"""
    # Mock the response
    mock_response = Mock()
    mock_response.json.return_value = {
        'weather': [{'description': 'clear sky'}],
        'main': {'temp': 25.5, 'feels_like': 27.0, 'humidity': 65},
        'wind': {'speed': 3.5}
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    
    # Test the function
    result = weather.get_weather()
    
    # Assertions
    assert result is not None
    assert isinstance(result, dict)
    assert 'description' in result
    assert 'temperature' in result
    assert 'feels_like' in result
    assert 'humidity' in result
    assert 'wind_speed' in result
    assert result['description'] == 'clear sky'
    assert result['temperature'] == 25.5
    assert result['feels_like'] == 27.0
    assert result['humidity'] == 65
    assert result['wind_speed'] == 3.5

@patch('weather.requests.get')
def test_get_weather_failure(mock_get):
    """Test weather data retrieval failure"""
    # Mock an exception
    mock_get.side_effect = Exception("Network error")
    
    # Test the function
    result = weather.get_weather()
    
    # Assertions
    assert result is None

@patch('weather.requests.get')
def test_get_weather_http_error(mock_get):
    """Test weather data retrieval with HTTP error"""
    # Mock HTTP error
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = Exception("HTTP Error")
    mock_get.return_value = mock_response
    
    # Test the function
    result = weather.get_weather()
    
    # Assertions
    assert result is None

if __name__ == "__main__":
    pytest.main([__file__])