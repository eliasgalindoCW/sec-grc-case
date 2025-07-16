"""
Tests for PR Analyzer Module
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.analyzers.pr_analyzer import PullRequestAnalyzer

def test_init():
    """Test analyzer initialization."""
    analyzer = PullRequestAnalyzer('token', 'owner/repo')
    assert analyzer.repo == 'owner/repo'
    assert analyzer.headers['Authorization'] == 'token token'
    assert analyzer.diff_headers['Accept'] == 'application/vnd.github.v3.diff'
    
@patch('requests.get')
def test_get_pr_diff_with_cache(mock_get, mock_cache):
    """Test getting PR diff with cache."""
    # Setup
    analyzer = PullRequestAnalyzer('token', 'owner/repo')
    analyzer.cache = mock_cache
    
    # Sample diff
    sample_diff = """diff --git a/test.py b/test.py
@@ -1,3 +1,5 @@
+def test_function():
+    pass
"""
    
    # First call - no cache
    mock_get.return_value = Mock(
        text=sample_diff,
        status_code=200,
        raise_for_status=Mock()
    )
    
    diff = analyzer._get_pr_diff(123)
    assert diff == sample_diff
    assert mock_get.call_count == 1
    
    # Second call - should use cache
    diff = analyzer._get_pr_diff(123)
    assert diff == sample_diff
    assert mock_get.call_count == 1  # No additional API calls
    
@patch('requests.get')
def test_get_merged_prs_with_cache(mock_get, mock_cache, mock_github_response, sample_pr_data):
    """Test fetching merged PRs with cache."""
    # Setup
    analyzer = PullRequestAnalyzer('token', 'owner/repo')
    analyzer.cache = mock_cache
    
    # First call - no cache
    mock_get.return_value = mock_github_response([sample_pr_data])
    prs = analyzer._get_merged_prs(days=30, min_sample=1)
    
    assert len(prs) == 1
    assert prs[0]['number'] == sample_pr_data['number']
    assert mock_get.call_count == 1
    
    # Second call - should use cache
    prs = analyzer._get_merged_prs(days=30, min_sample=1)
    assert len(prs) == 1
    assert prs[0]['number'] == sample_pr_data['number']
    assert mock_get.call_count == 1  # No additional API calls
    
@patch('requests.get')
def test_analyze_pr(mock_get, mock_github_response, sample_pr_data, sample_review_data):
    """Test PR analysis."""
    # Setup
    analyzer = PullRequestAnalyzer('token', 'owner/repo')
    
    # Sample diff
    sample_diff = """diff --git a/test.py b/test.py
@@ -1,3 +1,5 @@
+def test_function():
+    pass
"""
    
    # Mock API responses
    mock_get.side_effect = [
        mock_github_response(sample_pr_data),    # Get PR details
        Mock(                                    # Get PR diff
            text=sample_diff,
            status_code=200,
            raise_for_status=Mock()
        ),
        mock_github_response(sample_review_data) # Get reviews
    ]
    
    # Analyze PR
    analysis = analyzer._analyze_pr(sample_pr_data)
    
    # Verify results
    assert analysis['compliant'] == True
    assert len(analysis['reviewers']) == 2
    assert 'reviewer1' in analysis['reviewers']
    assert 'reviewer2' in analysis['reviewers']
    assert analysis['risk_level'] in ['low', 'medium', 'high', 'critical']
    assert isinstance(analysis['risk_factors'], list)
    assert isinstance(analysis['complexity_score'], float)
    assert isinstance(analysis['sensitive_patterns'], list)
    assert isinstance(analysis['stats'], dict)
    
@patch('requests.get')
def test_analyze_compliance(mock_get, mock_github_response, sample_pr_data, sample_review_data):
    """Test full compliance analysis."""
    # Setup
    analyzer = PullRequestAnalyzer('token', 'owner/repo')
    
    # Sample diff
    sample_diff = """diff --git a/test.py b/test.py
@@ -1,3 +1,5 @@
+def test_function():
+    pass
"""
    
    # Mock API responses
    mock_get.side_effect = [
        mock_github_response([sample_pr_data]),  # List PRs
        mock_github_response(sample_pr_data),    # Get PR details
        Mock(                                    # Get PR diff
            text=sample_diff,
            status_code=200,
            raise_for_status=Mock()
        ),
        mock_github_response(sample_review_data), # Get reviews
        mock_github_response([])                  # No more PRs
    ]
    
    # Run analysis
    results = analyzer.analyze_compliance(days=30, min_sample=1)
    
    # Verify results structure
    assert 'analysis_metadata' in results
    assert 'summary' in results
    assert 'review_patterns' in results
    assert 'non_compliant_details' in results
    assert 'statistical_metrics' in results
    
    # Verify summary metrics
    summary = results['summary']
    assert summary['total_prs'] == 1
    assert isinstance(summary['compliance_rate'], float)
    assert isinstance(summary['high_risk_prs'], int)
    assert isinstance(summary['risk_distribution'], dict)
    
    # Verify review patterns
    assert isinstance(results['review_patterns'], dict)
    assert 'reviewer1' in results['review_patterns']
    assert 'reviewer2' in results['review_patterns']
    
@patch('requests.get')
def test_non_compliant_pr(mock_get, mock_github_response, sample_pr_data):
    """Test analysis of non-compliant PR."""
    # Setup
    analyzer = PullRequestAnalyzer('token', 'owner/repo')
    
    # Sample diff
    sample_diff = """diff --git a/test.py b/test.py
@@ -1,3 +1,5 @@
+def test_function():
+    pass
"""
    
    # Modify sample data for non-compliance
    non_compliant_reviews = [
        {
            'user': {'login': sample_pr_data['user']['login']},  # Self-review
            'state': 'APPROVED',
            'submitted_at': '2025-01-01T12:00:00Z'
        }
    ]
    
    # Mock API responses
    mock_get.side_effect = [
        mock_github_response([sample_pr_data]),  # List PRs
        mock_github_response(sample_pr_data),    # Get PR details
        Mock(                                    # Get PR diff
            text=sample_diff,
            status_code=200,
            raise_for_status=Mock()
        ),
        mock_github_response(non_compliant_reviews), # Get reviews
        mock_github_response([])                     # No more PRs
    ]
    
    # Run analysis
    results = analyzer.analyze_compliance(days=30, min_sample=1)
    
    # Verify non-compliance
    assert results['summary']['compliance_rate'] == 0.0
    assert len(results['non_compliant_details']) == 1
    assert results['non_compliant_details'][0]['number'] == sample_pr_data['number']
    
@patch('requests.get')
def test_error_handling(mock_get, mock_github_response):
    """Test error handling in PR analysis."""
    # Setup
    analyzer = PullRequestAnalyzer('token', 'owner/repo')
    
    # Mock API error
    mock_get.return_value = mock_github_response(None, status_code=401)
    
    # Verify error handling
    with pytest.raises(Exception) as exc:
        analyzer.analyze_compliance(days=30, min_sample=1)
    assert "API Error" in str(exc.value)
    
def test_statistical_metrics():
    """Test statistical metrics calculation."""
    # Setup
    analyzer = PullRequestAnalyzer('token', 'owner/repo')
    
    # Sample PR data
    prs = [
        {
            'number': 1,
            'created_at': '2025-01-01T00:00:00Z',
            'merged_at': '2025-01-02T00:00:00Z'
        },
        {
            'number': 2,
            'created_at': '2025-01-01T00:00:00Z',
            'merged_at': '2025-01-03T00:00:00Z'
        }
    ]
    
    # Calculate metrics
    metrics = analyzer._calculate_statistical_metrics(prs)
    
    # Verify metrics
    assert 'median_merge_time' in metrics
    assert 'avg_merge_time' in metrics
    assert isinstance(metrics['median_merge_time'], float)
    assert isinstance(metrics['avg_merge_time'], float) 