"""
MCP Evidence Analyzer

This module provides MCP (Model Context Protocol) integration for analyzing
PR review control evidence and suggesting improvements.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import logging
from evidence_store import EvidenceStore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPEvidenceAnalyzer:
    """
    Analyzes control evidence using MCP for intelligent insights.
    """
    
    def __init__(self, evidence_dir: str = "evidence"):
        """Initialize analyzer with evidence directory."""
        self.store = EvidenceStore(evidence_dir)
    
    def get_evidence_context(
        self,
        control_id: Optional[int] = None,
        days: int = 30
    ) -> Dict:
        """
        Get structured context about control evidence for MCP.
        
        Args:
            control_id: Optional control ID to filter
            days: Number of days of history to include
            
        Returns:
            Dictionary with structured context for MCP
        """
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get evidence history
        evidence_list = self.store.get_evidence_history(
            control_id=control_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate trends
        compliance_trend = self._analyze_compliance_trend(evidence_list)
        review_patterns = self._analyze_review_patterns(evidence_list)
        risk_patterns = self._analyze_risk_patterns(evidence_list)
        
        # Structure context for MCP
        context = {
            'evidence_summary': {
                'total_records': len(evidence_list),
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'compliance_trend': compliance_trend,
                'latest_status': evidence_list[0]['status'] if evidence_list else 'unknown'
            },
            'review_patterns': {
                'patterns': review_patterns,
                'concerns': self._identify_review_concerns(review_patterns)
            },
            'risk_analysis': {
                'patterns': risk_patterns,
                'concerns': self._identify_risk_concerns(risk_patterns)
            },
            'improvement_opportunities': self._identify_improvements(
                compliance_trend,
                review_patterns,
                risk_patterns
            )
        }
        
        return context
    
    def _analyze_compliance_trend(self, evidence_list: List[Dict]) -> Dict:
        """Analyze compliance rate trends."""
        if not evidence_list:
            return {'trend': 'unknown', 'details': {}}
            
        # Extract compliance rates
        rates = []
        for evidence in evidence_list:
            if 'metrics' in evidence and 'compliance_rate' in evidence['metrics']:
                rates.append({
                    'date': evidence['timestamp'],
                    'rate': evidence['metrics']['compliance_rate']
                })
        
        if not rates:
            return {'trend': 'unknown', 'details': {}}
            
        # Calculate trend
        rates.sort(key=lambda x: x['date'])
        first_rate = rates[0]['rate']
        last_rate = rates[-1]['rate']
        
        trend = {
            'direction': 'improving' if last_rate > first_rate else 'declining' if last_rate < first_rate else 'stable',
            'change': last_rate - first_rate,
            'current_rate': last_rate,
            'historical_rates': rates
        }
        
        return trend
    
    def _analyze_review_patterns(self, evidence_list: List[Dict]) -> Dict:
        """Analyze PR review patterns."""
        patterns = {
            'reviewer_distribution': {},
            'review_times': [],
            'common_issues': []
        }
        
        for evidence in evidence_list:
            if 'metrics' not in evidence:
                continue
                
            # Analyze reviewer distribution
            if 'review_patterns' in evidence['metrics']:
                for reviewer, count in evidence['metrics']['review_patterns'].items():
                    if reviewer not in patterns['reviewer_distribution']:
                        patterns['reviewer_distribution'][reviewer] = 0
                    patterns['reviewer_distribution'][reviewer] += count
            
            # Collect review times
            if 'statistical_metrics' in evidence['metrics']:
                stats = evidence['metrics']['statistical_metrics']
                if 'median_review_time' in stats:
                    patterns['review_times'].append(stats['median_review_time'])
            
            # Analyze non-compliant PRs
            if 'non_compliant_details' in evidence:
                for pr in evidence['non_compliant_details']:
                    if 'risk_factors' in pr:
                        patterns['common_issues'].extend(pr['risk_factors'])
        
        # Summarize common issues
        if patterns['common_issues']:
            from collections import Counter
            issues_count = Counter(patterns['common_issues'])
            patterns['common_issues'] = [
                {'issue': issue, 'count': count}
                for issue, count in issues_count.most_common()
            ]
        
        return patterns
    
    def _analyze_risk_patterns(self, evidence_list: List[Dict]) -> Dict:
        """Analyze risk patterns in evidence."""
        patterns = {
            'risk_distribution': {},
            'high_risk_trend': [],
            'risk_factors': []
        }
        
        for evidence in evidence_list:
            if 'metrics' not in evidence:
                continue
                
            # Analyze risk distribution
            if 'risk_distribution' in evidence['metrics']:
                for risk, count in evidence['metrics']['risk_distribution'].items():
                    if risk not in patterns['risk_distribution']:
                        patterns['risk_distribution'][risk] = []
                    patterns['risk_distribution'][risk].append({
                        'date': evidence['timestamp'],
                        'count': count
                    })
            
            # Track high risk PRs
            if 'high_risk_prs' in evidence['metrics']:
                patterns['high_risk_trend'].append({
                    'date': evidence['timestamp'],
                    'count': evidence['metrics']['high_risk_prs']
                })
            
            # Collect risk factors
            if 'non_compliant_details' in evidence:
                for pr in evidence['non_compliant_details']:
                    if 'risk_factors' in pr:
                        patterns['risk_factors'].extend(pr['risk_factors'])
        
        return patterns
    
    def _identify_review_concerns(self, patterns: Dict) -> List[Dict]:
        """Identify concerns in review patterns."""
        concerns = []
        
        # Check reviewer distribution
        if patterns.get('reviewer_distribution'):
            total_reviews = sum(patterns['reviewer_distribution'].values())
            for reviewer, count in patterns['reviewer_distribution'].items():
                percentage = (count / total_reviews) * 100
                if percentage > 50:
                    concerns.append({
                        'type': 'reviewer_concentration',
                        'description': f"Reviewer {reviewer} is responsible for {percentage:.1f}% of reviews",
                        'severity': 'high' if percentage > 75 else 'medium'
                    })
        
        # Check review times
        if patterns.get('review_times'):
            avg_time = sum(patterns['review_times']) / len(patterns['review_times'])
            if avg_time < 0.25:  # Less than 15 minutes
                concerns.append({
                    'type': 'quick_reviews',
                    'description': f"Average review time of {avg_time:.2f} hours is very short",
                    'severity': 'high'
                })
        
        # Check common issues
        if patterns.get('common_issues'):
            for issue in patterns['common_issues']:
                if issue['count'] > 3:
                    concerns.append({
                        'type': 'recurring_issue',
                        'description': f"Recurring issue: {issue['issue']} (occurred {issue['count']} times)",
                        'severity': 'medium'
                    })
        
        return concerns
    
    def _identify_risk_concerns(self, patterns: Dict) -> List[Dict]:
        """Identify concerns in risk patterns."""
        concerns = []
        
        # Analyze high risk trend
        if patterns.get('high_risk_trend'):
            recent_high_risk = patterns['high_risk_trend'][-3:]  # Last 3 records
            if all(entry['count'] > 0 for entry in recent_high_risk):
                concerns.append({
                    'type': 'persistent_high_risk',
                    'description': "Persistent high-risk PRs in recent checks",
                    'severity': 'high'
                })
        
        # Analyze risk distribution
        if patterns.get('risk_distribution'):
            for risk_level, trend in patterns['risk_distribution'].items():
                if risk_level.lower() in ['high', 'critical']:
                    recent_count = sum(entry['count'] for entry in trend[-3:])  # Last 3 records
                    if recent_count > 5:
                        concerns.append({
                            'type': 'high_risk_volume',
                            'description': f"High volume of {risk_level} risk PRs ({recent_count} in recent checks)",
                            'severity': 'high'
                        })
        
        return concerns
    
    def _identify_improvements(
        self,
        compliance_trend: Dict,
        review_patterns: Dict,
        risk_patterns: Dict
    ) -> List[Dict]:
        """Identify potential improvements based on analysis."""
        improvements = []
        
        # Check compliance trend
        if compliance_trend.get('direction') == 'declining':
            improvements.append({
                'area': 'compliance',
                'suggestion': "Review and reinforce PR review policy as compliance rate is declining",
                'priority': 'high'
            })
        
        # Check reviewer distribution
        if review_patterns.get('reviewer_distribution'):
            total_reviewers = len(review_patterns['reviewer_distribution'])
            if total_reviewers < 3:
                improvements.append({
                    'area': 'reviewers',
                    'suggestion': "Expand reviewer pool to reduce dependency on few reviewers",
                    'priority': 'medium'
                })
        
        # Check review times
        if review_patterns.get('review_times'):
            avg_time = sum(review_patterns['review_times']) / len(review_patterns['review_times'])
            if avg_time < 0.5:  # Less than 30 minutes
                improvements.append({
                    'area': 'review_quality',
                    'suggestion': "Consider implementing minimum review time guidelines",
                    'priority': 'medium'
                })
        
        # Check risk patterns
        if risk_patterns.get('high_risk_trend'):
            recent_trend = risk_patterns['high_risk_trend'][-3:]
            if any(entry['count'] > 2 for entry in recent_trend):
                improvements.append({
                    'area': 'risk_management',
                    'suggestion': "Implement pre-review checklist for high-risk changes",
                    'priority': 'high'
                })
        
        return improvements
    
    def generate_mcp_prompt(
        self,
        control_id: Optional[int] = None,
        days: int = 30
    ) -> str:
        """
        Generate an MCP-ready prompt for analyzing evidence.
        
        Args:
            control_id: Optional control ID to filter
            days: Number of days of history to include
            
        Returns:
            Formatted prompt for MCP
        """
        context = self.get_evidence_context(control_id, days)
        
        prompt = f"""
Analyze the following PR review control evidence and provide recommendations:

Evidence Summary:
- Period: {context['evidence_summary']['date_range']['start']} to {context['evidence_summary']['date_range']['end']}
- Total Records: {context['evidence_summary']['total_records']}
- Current Status: {context['evidence_summary']['latest_status']}
- Compliance Trend: {context['evidence_summary']['compliance_trend']['direction']}
  (Change: {context['evidence_summary']['compliance_trend'].get('change', 'N/A')}%)

Review Pattern Concerns:
{chr(10).join([f"- {c['description']} (Severity: {c['severity']})" for c in context['review_patterns']['concerns']])}

Risk Concerns:
{chr(10).join([f"- {c['description']} (Severity: {c['severity']})" for c in context['risk_analysis']['concerns']])}

Suggested Improvements:
{chr(10).join([f"- [{i['priority']}] {i['suggestion']}" for i in context['improvement_opportunities']])}

Based on this evidence:
1. What are the most critical issues that need immediate attention?
2. What patterns or trends suggest potential process improvements?
3. How can we improve the review process to reduce high-risk PRs?
4. What automated checks or guidelines could help prevent these issues?

Please provide specific, actionable recommendations that could be implemented in the next sprint.
        """.strip()
        
        return prompt 