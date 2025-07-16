"""
Code Analysis Module

This module provides code analysis functionality for assessing PR risk levels.
"""

import re
from typing import Dict, List, Set
from pathlib import Path
import logging

from src.utils.logging_config import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

class CodeAnalyzer:
    """
    Analyzes code complexity and risk factors.
    """
    
    # High-risk file patterns
    HIGH_RISK_PATTERNS = {
        'security': r'(auth|crypt|password|secret|token|key|cert)',
        'critical': r'(payment|transaction|transfer|withdraw)',
        'sensitive': r'(user|account|profile|personal)',
        'infrastructure': r'(deploy|terraform|k8s|kubernetes|docker)',
    }
    
    # High-risk file types
    HIGH_RISK_EXTENSIONS = {
        '.env', 'Dockerfile', 'docker-compose.yml',
        '.tf', '.yaml', '.yml', '.key', '.pem'
    }
    
    def __init__(self):
        """Initialize code analyzer."""
        self.risk_patterns = {
            name: re.compile(pattern, re.I)
            for name, pattern in self.HIGH_RISK_PATTERNS.items()
        }
        
    def analyze_diff(self, diff: str) -> Dict:
        """
        Analyze a PR diff for risk factors.
        
        Args:
            diff: PR diff content
            
        Returns:
            Dictionary with analysis results
        """
        results = {
            'complexity_score': self._calculate_complexity(diff),
            'risk_factors': self._identify_risk_factors(diff),
            'sensitive_patterns': self._check_sensitive_patterns(diff),
            'stats': self._calculate_stats(diff)
        }
        
        # Calculate overall risk level
        results['risk_level'] = self._determine_risk_level(results)
        
        return results
        
    def _calculate_complexity(self, diff: str) -> float:
        """Calculate code complexity score."""
        score = 0.0
        
        # Check line count
        lines = diff.count('\n')
        if lines > 500:
            score += 0.4
        elif lines > 200:
            score += 0.2
        
        # Check function complexity
        functions = len(re.findall(r'(def|function|class)\s+\w+', diff))
        if functions > 10:
            score += 0.3
        elif functions > 5:
            score += 0.2
            
        # Check nested complexity
        nesting = len(re.findall(r'^\s{8,}', diff, re.M))
        if nesting > 20:
            score += 0.3
        elif nesting > 10:
            score += 0.2
            
        return min(score, 1.0)
        
    def _identify_risk_factors(self, diff: str) -> List[str]:
        """Identify risk factors in code."""
        factors = []
        
        # Check for risky patterns
        for name, pattern in self.risk_patterns.items():
            if pattern.search(diff):
                factors.append(f"Contains {name}-related code")
                
        # Check file types
        for ext in self.HIGH_RISK_EXTENSIONS:
            if f"diff --git a/*{ext}" in diff or f"diff --git b/*{ext}" in diff:
                factors.append(f"Modifies {ext} file")
                
        # Check for specific patterns
        if re.search(r'TODO|FIXME|XXX|HACK', diff):
            factors.append("Contains temporary solutions/hacks")
            
        if re.search(r'console\.(log|debug|error)|print[\s]*\(', diff):
            factors.append("Contains debug statements")
            
        return factors
        
    def _check_sensitive_patterns(self, diff: str) -> Set[str]:
        """Check for sensitive patterns in code."""
        patterns = set()
        
        # Check for potential secrets
        secret_pattern = re.compile(
            r'(api[_-]?key|token|secret|password|credential)',
            re.I
        )
        if secret_pattern.search(diff):
            patterns.add("potential_secrets")
            
        # Check for SQL queries
        if re.search(r'SELECT|INSERT|UPDATE|DELETE\s+FROM', diff):
            patterns.add("sql_queries")
            
        # Check for security configurations
        if re.search(r'security|permission|role|access', diff, re.I):
            patterns.add("security_config")
            
        return patterns
        
    def _calculate_stats(self, diff: str) -> Dict:
        """Calculate diff statistics."""
        return {
            'total_lines': diff.count('\n'),
            'added_lines': len(re.findall(r'^\+[^+]', diff, re.M)),
            'removed_lines': len(re.findall(r'^-[^-]', diff, re.M)),
            'files_changed': len(re.findall(r'diff --git', diff)),
            'functions_changed': len(re.findall(r'(def|function|class)\s+\w+', diff))
        }
        
    def _determine_risk_level(self, results: Dict) -> str:
        """Determine overall risk level."""
        risk_score = 0.0
        
        # Factor in complexity
        risk_score += results['complexity_score']
        
        # Factor in risk factors
        risk_score += len(results['risk_factors']) * 0.1
        
        # Factor in sensitive patterns
        risk_score += len(results['sensitive_patterns']) * 0.2
        
        # Factor in stats
        stats = results['stats']
        if stats['total_lines'] > 500:
            risk_score += 0.2
        if stats['files_changed'] > 10:
            risk_score += 0.2
            
        # Determine level
        if risk_score >= 0.8:
            return "critical"
        elif risk_score >= 0.6:
            return "high"
        elif risk_score >= 0.3:
            return "medium"
        else:
            return "low" 