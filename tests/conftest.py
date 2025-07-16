"""
Test Configuration Module

This module provides common test fixtures and configuration.
"""

import pytest
from unittest.mock import Mock
from pathlib import Path
import json
import os

@pytest.fixture
def mock_github_response():
    """Mock GitHub API response."""
    def _create_response(data, status_code=200):
        response = Mock()
        response.json.return_value = data
        response.status_code = status_code
        response.raise_for_status = Mock()
        if status_code >= 400:
            response.raise_for_status.side_effect = Exception("API Error")
        return response
    return _create_response

@pytest.fixture
def sample_pr_data():
    """Sample PR data for testing."""
    return {
        'number': 123,
        'title': 'Test PR',
        'user': {'login': 'author'},
        'created_at': '2025-01-01T00:00:00Z',
        'merged_at': '2025-01-02T00:00:00Z',
        'html_url': 'https://github.com/org/repo/pull/123',
        'diff': """diff --git a/test.py b/test.py
index abc..def 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,5 @@
+def test_function():
+    pass
 """
    }

@pytest.fixture
def sample_review_data():
    """Sample review data for testing."""
    return [
        {
            'user': {'login': 'reviewer1'},
            'state': 'APPROVED',
            'submitted_at': '2025-01-01T12:00:00Z'
        },
        {
            'user': {'login': 'reviewer2'},
            'state': 'COMMENTED',
            'submitted_at': '2025-01-01T11:00:00Z'
        }
    ]

@pytest.fixture
def test_config(tmp_path):
    """Test configuration with temporary directories."""
    config = {
        'evidence_dir': tmp_path / 'evidence',
        'output_dir': tmp_path / 'output',
        'cache_dir': tmp_path / 'cache'
    }
    
    # Create directories
    for path in config.values():
        path.mkdir(parents=True, exist_ok=True)
        
    return config

@pytest.fixture
def mock_cache(test_config):
    """Mock cache implementation."""
    cache = {}
    
    def get(key):
        return cache.get(key)
        
    def set(key, value):
        cache[key] = value
        
    mock = Mock()
    mock.get = Mock(side_effect=get)
    mock.set = Mock(side_effect=set)
    mock.cache_dir = test_config['cache_dir']
    
    return mock 