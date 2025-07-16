"""
Pull Request Analyzer Module

This module analyzes GitHub Pull Request compliance with review controls.
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from src.utils.logging_config import setup_logging
from src.utils.cache import Cache
from src.analyzers.code_analyzer import CodeAnalyzer

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

class PullRequestAnalyzer:
    """
    Analyzes GitHub Pull Request compliance with review controls.
    """
    
    def __init__(self, github_token: str, repo: str, cache_ttl: int = 24):
        """
        Initialize analyzer.
        
        Args:
            github_token: GitHub API token
            repo: Repository in owner/repo format
            cache_ttl: Cache TTL in hours (default: 24)
        """
        self.repo = repo
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.diff_headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3.diff'
        }
        self.cache = Cache(ttl_hours=cache_ttl)
        self.code_analyzer = CodeAnalyzer()
        
    def analyze_compliance(self, days: int = 30, min_sample: int = 50) -> Dict:
        """
        Analyze PR review compliance.
        
        Args:
            days: Number of days to analyze
            min_sample: Minimum sample size
            
        Returns:
            Dictionary with analysis results
        """
        logger.info(f"\nAnalyzing PRs from {(datetime.utcnow() - timedelta(days=days)).date()} to {datetime.utcnow().date()}")
        logger.info(f"Target minimum sample size: {min_sample}")
        
        # Get merged PRs
        merged_prs = self._get_merged_prs(days, min_sample)
        logger.info(f"Found {len(merged_prs)} merged PRs for analysis\n")
        
        # Analyze each PR
        compliant_prs = []
        non_compliant_prs = []
        review_patterns = {}
        risk_distribution = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        
        for pr in merged_prs:
            analysis = self._analyze_pr(pr)
            
            # Track review patterns
            for reviewer in analysis['reviewers']:
                if reviewer not in review_patterns:
                    review_patterns[reviewer] = 0
                review_patterns[reviewer] += 1
                
            # Track risk levels
            risk_distribution[analysis['risk_level']] += 1
            
            # Track compliance
            if analysis['compliant']:
                compliant_prs.append(pr)
            else:
                non_compliant_prs.append({
                    'number': pr['number'],
                    'title': pr['title'],
                    'author': pr['user']['login'],
                    'url': pr['html_url'],
                    'created_at': pr['created_at'],
                    'risk_level': analysis['risk_level'],
                    'risk_factors': analysis['risk_factors'],
                    'stats': analysis['stats']
                })
        
        # Calculate metrics
        total_prs = len(merged_prs)
        compliance_rate = (len(compliant_prs) / total_prs * 100) if total_prs > 0 else 0
        
        # Prepare results
        results = {
            'analysis_metadata': {
                'analysis_date': datetime.utcnow().isoformat(),
                'days_analyzed': days,
                'sample_size': total_prs
            },
            'summary': {
                'total_prs': total_prs,
                'compliance_rate': compliance_rate,
                'compliant_prs': len(compliant_prs),
                'non_compliant_prs': len(non_compliant_prs),
                'high_risk_prs': risk_distribution['high'] + risk_distribution['critical'],
                'risk_distribution': risk_distribution
            },
            'review_patterns': review_patterns,
            'non_compliant_details': non_compliant_prs,
            'statistical_metrics': self._calculate_statistical_metrics(merged_prs)
        }
        
        # Log summary
        logger.info("Compliance Analysis Summary:")
        logger.info(f"Total PRs analyzed: {total_prs}")
        logger.info(f"Compliance rate: {compliance_rate:.2f}%")
        logger.info(f"High risk PRs: {results['summary']['high_risk_prs']}\n")
        
        logger.info("Risk Distribution:")
        for risk, count in risk_distribution.items():
            logger.info(f"- {risk}: {count}")
            
        if non_compliant_prs:
            logger.info("\nNon-compliant and High-risk PRs:\n")
            for pr in non_compliant_prs:
                logger.info(f"- PR #{pr['number']}: {pr['title']}")
                logger.info(f"  Risk Level: {pr['risk_level']}\n")
                
        return results
        
    def _get_merged_prs(self, days: int, min_sample: int) -> List[Dict]:
        """Get merged PRs from GitHub API with caching."""
        cache_key = f"merged_prs_{self.repo}_{days}_{min_sample}"
        cached = self.cache.get(cache_key)
        
        if cached:
            return cached
            
        merged_prs = []
        page = 1
        per_page = 100
        
        while True:
            # Get PRs from API
            url = f"https://api.github.com/repos/{self.repo}/pulls"
            params = {
                'state': 'closed',
                'sort': 'updated',
                'direction': 'desc',
                'per_page': per_page,
                'page': page
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            prs = response.json()
            if not prs:
                break
                
            # Filter merged PRs within time range
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            for pr in prs:
                if not pr['merged_at']:
                    continue
                    
                merged_at = datetime.strptime(pr['merged_at'], '%Y-%m-%dT%H:%M:%SZ')
                if merged_at < cutoff_date:
                    break
                    
                merged_prs.append(pr)
                
            if len(merged_prs) >= min_sample or len(prs) < per_page:
                break
                
            page += 1
            
        # Cache results
        self.cache.set(cache_key, merged_prs)
        return merged_prs
        
    def _get_pr_diff(self, pr_number: int) -> str:
        """Get PR diff from GitHub API."""
        cache_key = f"pr_diff_{self.repo}_{pr_number}"
        cached = self.cache.get(cache_key)
        
        if cached:
            return cached
            
        url = f"https://api.github.com/repos/{self.repo}/pulls/{pr_number}"
        response = requests.get(url, headers=self.diff_headers)
        response.raise_for_status()
        
        diff = response.text
        self.cache.set(cache_key, diff)
        return diff

    def _analyze_pr(self, pr: Dict) -> Dict:
        """Analyze a single PR."""
        cache_key = f"pr_analysis_{pr['number']}"
        cached = self.cache.get(cache_key)
        
        if cached:
            return cached
            
        # Get PR details
        url = f"https://api.github.com/repos/{self.repo}/pulls/{pr['number']}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        pr_details = response.json()
        
        # Get PR diff
        diff = self._get_pr_diff(pr['number'])
        
        # Get reviews
        reviews_url = f"{url}/reviews"
        response = requests.get(reviews_url, headers=self.headers)
        response.raise_for_status()
        reviews = response.json()
        
        # Analyze reviews
        author = pr['user']['login']
        reviewers = set()
        approved = False
        
        for review in reviews:
            reviewer = review['user']['login']
            if reviewer != author:
                reviewers.add(reviewer)
                if review['state'].lower() == 'approved':
                    approved = True
                    
        # Analyze code
        code_analysis = self.code_analyzer.analyze_diff(diff)
        
        # Determine compliance
        compliant = approved and len(reviewers) > 0
        
        analysis = {
            'compliant': compliant,
            'reviewers': list(reviewers),
            'risk_level': code_analysis['risk_level'],
            'risk_factors': code_analysis['risk_factors'],
            'complexity_score': code_analysis['complexity_score'],
            'sensitive_patterns': list(code_analysis['sensitive_patterns']),
            'stats': code_analysis['stats']
        }
        
        # Cache results
        self.cache.set(cache_key, analysis)
        return analysis
        
    def _calculate_statistical_metrics(self, prs: List[Dict]) -> Dict:
        """Calculate statistical metrics for PRs."""
        if not prs:
            return {}
            
        # Calculate time metrics
        review_times = []
        merge_times = []
        
        for pr in prs:
            created_at = datetime.strptime(pr['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            merged_at = datetime.strptime(pr['merged_at'], '%Y-%m-%dT%H:%M:%SZ')
            
            # Get first review time
            reviews_url = f"https://api.github.com/repos/{self.repo}/pulls/{pr['number']}/reviews"
            response = requests.get(reviews_url, headers=self.headers)
            response.raise_for_status()
            reviews = response.json()
            
            if reviews:
                first_review = min(
                    datetime.strptime(r['submitted_at'], '%Y-%m-%dT%H:%M:%SZ')
                    for r in reviews
                )
                review_times.append((first_review - created_at).total_seconds() / 3600)
                
            merge_times.append((merged_at - created_at).total_seconds() / 3600)
            
        return {
            'median_review_time': sorted(review_times)[len(review_times)//2] if review_times else None,
            'median_merge_time': sorted(merge_times)[len(merge_times)//2] if merge_times else None,
            'avg_review_time': sum(review_times)/len(review_times) if review_times else None,
            'avg_merge_time': sum(merge_times)/len(merge_times) if merge_times else None
        } 