"""
Main Application Module

This module provides the entry point for the PR review control analyzer.
"""

import sys
from typing import Optional, Dict
import logging
from pathlib import Path

from src.analyzers.pr_analyzer import PullRequestAnalyzer
from src.analyzers.analyze_with_llm import LLMAnalyzer
from src.core.evidence_store import EvidenceStore
from src.utils.config import load_config
from src.utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Load configuration
config = load_config()

def analyze_github_controls(days: int = 30) -> Dict:
    """
    Analyze GitHub PR controls using the new analyzer.
    """
    analyzer = PullRequestAnalyzer(
        config.github_token,
        config.github_repo
    )
    return analyzer.analyze_compliance(days)

def store_evidence(analysis_result: Dict) -> Dict:
    """
    Store analysis results as evidence locally.
    """
    # Initialize evidence store
    store = EvidenceStore()
    
    # Format evidence description
    description = f"""
GitHub Pull Request Review Control Analysis
Analysis Date: {analysis_result['analysis_metadata']['analysis_date']}
Period Analyzed: Last {analysis_result['analysis_metadata']['days_analyzed']} days

Summary:
- Total PRs analyzed: {analysis_result['summary']['total_prs']}
- Compliance rate: {analysis_result['summary']['compliance_rate']:.2f}%
- High risk PRs: {analysis_result['summary']['high_risk_prs']}

Risk Distribution:
{chr(10).join([f"- {risk}: {count}" for risk, count in analysis_result['summary']['risk_distribution'].items()])}

Review Patterns:
{chr(10).join([f"- {reviewer}: {count} reviews" for reviewer, count in analysis_result['review_patterns'].items()])}

Non-compliant Pull Requests:
{chr(10).join([
    f"- PR #{pr['number']}: {pr['title']}"
    f"\n  Author: {pr['author']}"
    f"\n  Created: {pr['created_at']}"
    f"\n  Risk Level: {pr['risk_level']}"
    f"\n  URL: {pr['url']}"
    for pr in analysis_result['non_compliant_details']
])}
    """.strip()
    
    # Store evidence
    return store.store_evidence(
        control_id=config.eramba_control_id,
        description=description,
        metrics=analysis_result
    )

def analyze_with_llm():
    """
    Analyze evidence with LLM.
    """
    analyzer = LLMAnalyzer()
    analyzer.analyze_evidence()

def main(action: Optional[str] = None) -> None:
    """
    Main function to orchestrate the execution of GitHub control checks
    and evidence storage.
    
    Args:
        action: Optional string specifying which action to run:
               'check' for GitHub controls check
               'submit' for evidence storage
               'report' for generating evidence report
               'analyze' for LLM analysis
               None to run all actions
    """
    try:
        analysis_result = None
        store = EvidenceStore()
        
        if action is None or action.lower() == 'check':
            logger.info("\nAnalyzing GitHub PR controls...")
            analysis_result = analyze_github_controls()
            
        if action is None or action.lower() == 'submit':
            if analysis_result is None:
                analysis_result = analyze_github_controls()
                
            logger.info("\nStoring evidence locally...")
            store_result = store_evidence(analysis_result)
            
            logger.info("\nEvidence stored successfully!")
            logger.info(f"Evidence file: {store_result['evidence_file']}")
            logger.info(f"Metrics file: {store_result['metrics_file']}")
            
        if action is None or action.lower() == 'report':
            logger.info("\nGenerating evidence report...")
            report_path = store.generate_report()
            logger.info(f"Report generated: {report_path}")

        if action is None or action.lower() == 'analyze':
            logger.info("\nAnalyzing evidence with LLM...")
            analyze_with_llm()
            
    except Exception as e:
        logger.error(f"\nError during execution: {str(e)}")
        if "Requires authentication" in str(e):
            logger.error("\nAuthentication failed. Please check your GitHub token in config.py")
            logger.error("1. Ensure GITHUB_TOKEN is set correctly")
            logger.error("2. Verify the token has not expired")
            logger.error("3. Confirm the token has the necessary permissions (repo scope)")
        sys.exit(1)

if __name__ == "__main__":
    # Parse command line arguments
    action = sys.argv[1] if len(sys.argv) > 1 else None
    
    valid_actions = ['check', 'submit', 'report', 'analyze']
    if action and action.lower() not in valid_actions:
        logger.error(f"Invalid action. Use one of: {', '.join(valid_actions)}")
        sys.exit(1)
        
    main(action)
