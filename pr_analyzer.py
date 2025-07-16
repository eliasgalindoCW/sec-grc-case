"""
Pull Request Analyzer Module

This module implements the core logic for analyzing GitHub Pull Request compliance
with the control requirement that PRs must be approved by someone other than the author.

Verification Strategy:
1. Sampling:
   - Default window: 30 days rolling
   - Configurable sample size
   - Support for different sampling methods (time-based, count-based, or statistical)
   
2. Compliance Checks:
   - PR author != PR approver
   - Proper review sequence (review after last commit)
   - Review completeness (comments, approval status)
   - Time-based patterns (review duration, merge timing)

3. Risk Indicators:
   - Self-approvals
   - Quick approvals (< 10 minutes)
   - Review bypasses
   - Pattern anomalies
"""

import requests
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta, timezone
import json
from dataclasses import dataclass
from enum import Enum
import statistics
from collections import defaultdict

def parse_datetime(date_str: str) -> datetime:
    """Parse GitHub API datetime string to timezone-aware datetime object."""
    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))

class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    NEEDS_REVIEW = "needs_review"
    HIGH_RISK = "high_risk"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ReviewMetrics:
    """Detailed metrics for review analysis."""
    time_to_first_review: Optional[float] = None  # hours
    time_to_approval: Optional[float] = None      # hours
    commits_after_approval: int = 0
    review_comments: int = 0
    risk_level: RiskLevel = RiskLevel.LOW
    risk_factors: List[str] = None
    
    def __post_init__(self):
        self.risk_factors = []

@dataclass
class PullRequestMetrics:
    """Structured data for PR metrics, prepared for LLM analysis."""
    total_prs: int = 0
    compliant_prs: int = 0
    non_compliant_prs: int = 0
    high_risk_prs: int = 0
    avg_review_time: float = 0.0
    unique_reviewers: Set[str] = None
    review_patterns: Dict[str, int] = None
    risk_distribution: Dict[RiskLevel, int] = None
    statistical_data: Dict[str, float] = None
    
    def __post_init__(self):
        self.unique_reviewers = set()
        self.review_patterns = {}
        self.risk_distribution = {level: 0 for level in RiskLevel}
        self.statistical_data = {}

@dataclass
class PullRequestData:
    """Structured data for individual PR analysis."""
    number: int
    title: str
    author: str
    created_at: datetime
    merged_at: Optional[datetime]
    reviewers: List[str]
    status: ComplianceStatus
    metrics: ReviewMetrics
    url: str

class PullRequestAnalyzer:
    """
    Analyzes GitHub Pull Requests for compliance with approval controls.
    Implements comprehensive sampling and verification strategies.
    """
    
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo
        self.headers = {'Authorization': f'token {token}'}
        self.metrics = PullRequestMetrics()
        self.analyzed_prs: List[PullRequestData] = []
        
        # Configuration
        self.quick_review_threshold = 600  # seconds (10 minutes)
        self.high_risk_threshold = 0.95    # 95% compliance required
        
    def get_date_range(self, days: int = 30) -> tuple:
        """Calculate date range for analysis."""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        return start_date, end_date
    
    def fetch_pull_requests(self, days: int = 30, min_sample_size: int = 50) -> List[Dict]:
        """
        Enhanced PR fetching with smart sampling:
        - Ensures minimum sample size if available
        - Uses pagination efficiently
        - Implements time-based sampling
        """
        start_date, end_date = self.get_date_range(days)
        url = f"https://api.github.com/repos/{self.repo}/pulls"
        
        print(f"\nAnalyzing PRs from {start_date.date()} to {end_date.date()}")
        print(f"Target minimum sample size: {min_sample_size}")
        
        all_prs = []
        page = 1
        
        while True:
            params = {
                'state': 'closed',
                'per_page': 100,
                'page': page,
                'sort': 'updated',
                'direction': 'desc'
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            prs = response.json()
            
            if not prs:
                break
                
            # Filter and collect PRs
            for pr in prs:
                if pr.get('merged_at'):
                    merged_at = parse_datetime(pr['merged_at'])
                    if start_date <= merged_at <= end_date:
                        all_prs.append(pr)
            
            # Check if we have enough samples
            if len(all_prs) >= min_sample_size:
                break
                
            # Check if we're beyond our date range
            if prs and parse_datetime(prs[-1]['updated_at']) < start_date:
                break
                
            page += 1
            
        print(f"Found {len(all_prs)} merged PRs for analysis")
        return all_prs
    
    def analyze_review_sequence(self, pr: Dict, reviews: List[Dict]) -> Tuple[bool, List[str]]:
        """
        Analyze the review sequence for potential issues:
        - Check if reviews came after the last commit
        - Identify quick approvals
        - Check for review dismissals
        """
        risk_factors = []
        is_compliant = True
        
        # Get commit timeline
        commits_url = pr['commits_url']
        response = requests.get(commits_url, headers=self.headers)
        response.raise_for_status()
        commits = response.json()
        
        if commits:
            last_commit_date = parse_datetime(commits[-1]['commit']['committer']['date'])
            
            # Check reviews after last commit
            for review in reviews:
                review_date = parse_datetime(review['submitted_at'])
                
                # Check for quick approvals
                if review['state'] == 'APPROVED':
                    time_diff = (review_date - last_commit_date).total_seconds()
                    if time_diff < self.quick_review_threshold:
                        risk_factors.append(f"Quick approval ({time_diff:.0f} seconds after last commit)")
                        is_compliant = False
                
                # Check for reviews before last commit
                if review_date < last_commit_date:
                    risk_factors.append("Review before final commit")
                    is_compliant = False
        
        return is_compliant, risk_factors
    
    def calculate_review_metrics(self, pr: Dict, reviews: List[Dict]) -> ReviewMetrics:
        """Calculate detailed metrics for a PR review."""
        metrics = ReviewMetrics()
        
        if not reviews:
            return metrics
            
        # Calculate review timings
        created_at = parse_datetime(pr['created_at'])
        review_times = []
        approval_times = []
        
        for review in reviews:
            review_date = parse_datetime(review['submitted_at'])
            time_diff = (review_date - created_at).total_seconds() / 3600
            review_times.append(time_diff)
            
            if review['state'] == 'APPROVED':
                approval_times.append(time_diff)
        
        if review_times:
            metrics.time_to_first_review = min(review_times)
        if approval_times:
            metrics.time_to_approval = min(approval_times)
        
        # Count review comments
        metrics.review_comments = sum(1 for r in reviews if r.get('body'))
        
        # Check sequence compliance
        sequence_ok, risk_factors = self.analyze_review_sequence(pr, reviews)
        metrics.risk_factors.extend(risk_factors)
        
        # Determine risk level
        if not sequence_ok or metrics.time_to_approval is None:
            metrics.risk_level = RiskLevel.HIGH
        elif metrics.time_to_first_review and metrics.time_to_first_review < 0.17:  # 10 minutes
            metrics.risk_level = RiskLevel.MEDIUM
        elif metrics.review_comments == 0:
            metrics.risk_level = RiskLevel.MEDIUM
        
        return metrics
    
    def analyze_pr_compliance(self, pr: Dict) -> PullRequestData:
        """
        Enhanced PR analysis with detailed compliance checking and risk assessment.
        """
        pr_number = pr['number']
        author = pr['user']['login']
        
        # Fetch review data
        url = f"https://api.github.com/repos/{self.repo}/pulls/{pr_number}/reviews"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        reviews = response.json()
        
        # Calculate detailed metrics
        review_metrics = self.calculate_review_metrics(pr, reviews)
        
        # Extract review information
        approvers = {r['user']['login'] for r in reviews if r['state'] == 'APPROVED'}
        
        # Determine compliance status
        status = ComplianceStatus.COMPLIANT
        if not any(a != author for a in approvers):
            status = ComplianceStatus.NON_COMPLIANT
        elif review_metrics.risk_level == RiskLevel.HIGH:
            status = ComplianceStatus.HIGH_RISK
        
        # Update metrics
        if status == ComplianceStatus.COMPLIANT:
            self.metrics.compliant_prs += 1
        elif status == ComplianceStatus.HIGH_RISK:
            self.metrics.high_risk_prs += 1
        else:
            self.metrics.non_compliant_prs += 1
            
        self.metrics.risk_distribution[review_metrics.risk_level] += 1
        
        # Update reviewer patterns
        for reviewer in approvers:
            self.metrics.unique_reviewers.add(reviewer)
            self.metrics.review_patterns[reviewer] = self.metrics.review_patterns.get(reviewer, 0) + 1
        
        return PullRequestData(
            number=pr_number,
            title=pr['title'],
            author=author,
            created_at=parse_datetime(pr['created_at']),
            merged_at=parse_datetime(pr['merged_at']) if pr['merged_at'] else None,
            reviewers=list(approvers),
            status=status,
            metrics=review_metrics,
            url=pr['html_url']
        )
    
    def calculate_statistical_metrics(self):
        """Calculate statistical metrics for the analyzed PRs."""
        review_times = [pr.metrics.time_to_approval 
                       for pr in self.analyzed_prs 
                       if pr.metrics.time_to_approval is not None]
        
        if review_times:
            self.metrics.statistical_data.update({
                'median_review_time': statistics.median(review_times),
                'std_dev_review_time': statistics.stdev(review_times) if len(review_times) > 1 else 0,
                'min_review_time': min(review_times),
                'max_review_time': max(review_times)
            })
    
    def analyze_compliance(self, days: int = 30, min_sample_size: int = 50) -> Dict:
        """
        Enhanced compliance analysis with comprehensive metrics and risk assessment.
        """
        try:
            # Fetch and analyze PRs
            prs = self.fetch_pull_requests(days, min_sample_size)
            self.metrics.total_prs = len(prs)
            
            # Analyze each PR
            for pr in prs:
                pr_data = self.analyze_pr_compliance(pr)
                self.analyzed_prs.append(pr_data)
            
            # Calculate statistical metrics
            self.calculate_statistical_metrics()
            
            # Prepare comprehensive result structure
            result = {
                'summary': {
                    'total_prs': self.metrics.total_prs,
                    'compliant_prs': self.metrics.compliant_prs,
                    'non_compliant_prs': self.metrics.non_compliant_prs,
                    'high_risk_prs': self.metrics.high_risk_prs,
                    'compliance_rate': (self.metrics.compliant_prs / self.metrics.total_prs * 100) if self.metrics.total_prs > 0 else 0,
                    'risk_distribution': {k.value: v for k, v in self.metrics.risk_distribution.items()}
                },
                'statistical_metrics': self.metrics.statistical_data,
                'review_patterns': self.metrics.review_patterns,
                'non_compliant_details': [
                    {
                        'number': pr.number,
                        'title': pr.title,
                        'author': pr.author,
                        'url': pr.url,
                        'created_at': pr.created_at.isoformat(),
                        'merged_at': pr.merged_at.isoformat() if pr.merged_at else None,
                        'reviewers': pr.reviewers,
                        'risk_level': pr.metrics.risk_level.value,
                        'risk_factors': pr.metrics.risk_factors,
                        'review_time_hours': pr.metrics.time_to_approval
                    }
                    for pr in self.analyzed_prs
                    if pr.status in [ComplianceStatus.NON_COMPLIANT, ComplianceStatus.HIGH_RISK]
                ],
                'analysis_metadata': {
                    'repository': self.repo,
                    'analysis_date': datetime.utcnow().isoformat(),
                    'days_analyzed': days,
                    'sample_size': self.metrics.total_prs
                }
            }
            
            # Print detailed summary
            print("\nCompliance Analysis Summary:")
            print(f"Total PRs analyzed: {result['summary']['total_prs']}")
            print(f"Compliance rate: {result['summary']['compliance_rate']:.2f}%")
            print(f"High risk PRs: {result['summary']['high_risk_prs']}")
            print("\nRisk Distribution:")
            for risk, count in result['summary']['risk_distribution'].items():
                print(f"- {risk}: {count}")
            
            if result['statistical_metrics']:
                print("\nReview Time Statistics (hours):")
                for metric, value in result['statistical_metrics'].items():
                    print(f"- {metric}: {value:.2f}")
            
            if result['non_compliant_details']:
                print("\nNon-compliant and High-risk PRs:")
                for pr in result['non_compliant_details']:
                    print(f"\n- PR #{pr['number']}: {pr['title']}")
                    print(f"  Risk Level: {pr['risk_level']}")
                    if pr['risk_factors']:
                        print(f"  Risk Factors: {', '.join(pr['risk_factors'])}")
            
            return result
            
        except Exception as e:
            print(f"Error during compliance analysis: {str(e)}")
            raise 