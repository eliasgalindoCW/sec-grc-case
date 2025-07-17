"""
MCP Evidence Analyzer

This module provides MCP (Model Context Protocol) integration for analyzing
PR review control evidence and suggesting improvements.
"""

import json
from datetime import datetime, timedelta
import datetime as dt
from typing import Dict, List, Optional
from pathlib import Path
import logging

from src.core.evidence_store import EvidenceStore
from src.utils.logging_config import setup_logging
from src.utils.config import load_config

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

class MCPEvidenceAnalyzer:
    """
    Analyzes control evidence using MCP for intelligent insights.
    """
    
    def __init__(self, evidence_dir: str = None):
        """Initialize analyzer with evidence directory."""
        config = load_config()
        self.store = EvidenceStore(evidence_dir or str(config.evidence_dir))
    
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
        end_date = datetime.now(dt.UTC)
        start_date = end_date - timedelta(days=days)
        
        # Get evidence history
        evidence_list = self.store.get_evidence_history(
            control_id=control_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get latest evidence
        latest_evidence = evidence_list[-1] if evidence_list else None
        
        # Calculate trends
        compliance_trend = self._analyze_compliance_trend(evidence_list)
        review_patterns = self._analyze_review_patterns(evidence_list)
        risk_patterns = self._analyze_risk_patterns(evidence_list)
        
        return {
            'evidence_summary': {
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'total_records': len(evidence_list),
                'latest_status': latest_evidence.get('status', 'unknown') if latest_evidence else 'unknown',
                'compliance_trend': compliance_trend
            },
            'review_patterns': review_patterns,
            'risk_patterns': risk_patterns
        }
    
    def _analyze_compliance_trend(self, evidence_list: List[Dict]) -> Dict:
        """Analyze compliance trend from evidence history."""
        if not evidence_list:
            return {'direction': 'stable', 'rate': 0.0}
            
        # Calculate compliance rates over time
        compliance_rates = [
            1.0 if e.get('status') == 'pass' else 0.0
            for e in evidence_list
        ]
        
        # Calculate trend
        if len(compliance_rates) < 2:
            return {'direction': 'stable', 'rate': compliance_rates[0]}
            
        current_rate = compliance_rates[-1]
        prev_rate = compliance_rates[-2]
        
        if current_rate > prev_rate:
            direction = 'improving'
        elif current_rate < prev_rate:
            direction = 'declining'
        else:
            direction = 'stable'
            
        return {
            'direction': direction,
            'rate': current_rate
        }
    
    def _analyze_review_patterns(self, evidence_list: List[Dict]) -> Dict:
        """Analyze review patterns from evidence history."""
        if not evidence_list:
            return {}
            
        # Use only the latest evidence for review patterns
        latest_evidence = evidence_list[-1]
        return latest_evidence.get('metrics', {}).get('review_patterns', {})
    
    def _analyze_risk_patterns(self, evidence_list: List[Dict]) -> Dict:
        """Analyze risk patterns from evidence history."""
        if not evidence_list:
            return {'high_risk_trend': [], 'risk_distribution': {}}
            
        # Use only the latest evidence for risk distribution
        latest_evidence = evidence_list[-1]
        latest_metrics = latest_evidence.get('metrics', {})
        
        return {
            'high_risk_trend': [
                e.get('metrics', {}).get('high_risk_prs', 0)
                for e in evidence_list
            ],
            'risk_distribution': latest_metrics.get('risk_distribution', {})
        }
    
    def generate_mcp_prompt(self, control_id: Optional[int] = None, days: int = 30) -> str:
        """Generate MCP prompt from evidence context."""
        context = self.get_evidence_context(control_id, days)
        
        # Format prompt
        prompt = f"""
Please analyze the following PR review control evidence and provide recommendations:

Evidence Summary:
- Period: {context['evidence_summary']['date_range']['start']} to {context['evidence_summary']['date_range']['end']}
- Total Records: {context['evidence_summary']['total_records']}
- Current Status: {context['evidence_summary']['latest_status']}
- Compliance Trend: {context['evidence_summary']['compliance_trend']['direction']} ({context['evidence_summary']['compliance_trend']['rate']:.2f})

Review Patterns:
{chr(10).join([f"- {reviewer}: {count} reviews" for reviewer, count in context['review_patterns'].items()])}

Risk Distribution:
{chr(10).join([f"- {risk}: {count} PRs" for risk, count in context['risk_patterns']['risk_distribution'].items()])}

High Risk PR Trend:
{', '.join(map(str, context['risk_patterns']['high_risk_trend']))}

Please provide:
1. Critical issues that need immediate attention
2. Process improvement recommendations
3. Specific metrics and targets to track
4. Actionable next steps
"""
        return prompt.strip() 