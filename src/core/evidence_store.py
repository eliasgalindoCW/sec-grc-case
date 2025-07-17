"""
Evidence Store Module

This module provides a local storage system for control evidence and metrics.
It handles:
- Storing control evidence in JSON format
- Managing metrics data
- Generating reports
- Maintaining evidence history
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging
from pathlib import Path

from src.utils.logging_config import setup_logging
from src.utils.config import load_config

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

class EvidenceStore:
    """
    Stores control evidence locally in a structured format.
    """
    
    def __init__(self, storage_dir: str = None):
        """
        Initialize evidence store.
        
        Args:
            storage_dir: Directory to store evidence files (defaults to config path)
        """
        config = load_config()
        self.storage_dir = Path(storage_dir or str(config.evidence_dir))
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.storage_dir / "controls").mkdir(exist_ok=True)
        (self.storage_dir / "metrics").mkdir(exist_ok=True)
        (self.storage_dir / "reports").mkdir(exist_ok=True)
        
        logger.info(f"Initialized evidence store in {self.storage_dir}")
    
    def store_evidence(
        self,
        control_id: int,
        description: str,
        metrics: Dict,
        status: Optional[str] = None
    ) -> Dict:
        """
        Store control evidence.
        
        Args:
            control_id: Control identifier
            description: Evidence description
            metrics: Evidence metrics
            status: Optional status override (defaults to metrics['summary']['status'])
            
        Returns:
            Dictionary with file paths
        """
        timestamp = datetime.now(datetime.UTC)
        date_str = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        
        # Use provided status or get from metrics
        if status is None:
            status = metrics.get('summary', {}).get('status', 'unknown')
        
        # Prepare evidence data
        evidence = {
            'control_id': control_id,
            'timestamp': timestamp.isoformat(),
            'status': status,
            'description': description
        }
        
        # Save evidence
        evidence_file = self.storage_dir / "controls" / f"control_{control_id}_{date_str}.json"
        with open(evidence_file, 'w') as f:
            json.dump(evidence, f, indent=2)
            
        logger.info(f"Stored evidence for control {control_id}")
        logger.info(f"Evidence file: {evidence_file}")
        
        # Save metrics
        metrics_file = self.storage_dir / "metrics" / f"metrics_{control_id}_{date_str}.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
            
        logger.info(f"Metrics file: {metrics_file}")
        
        return {
            'evidence_file': str(evidence_file),
            'metrics_file': str(metrics_file)
        }
    
    def get_evidence_history(
        self,
        control_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get evidence history for a control.
        
        Args:
            control_id: Optional control ID to filter
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            List of evidence records
        """
        evidence_list = []
        
        # Get all evidence files
        evidence_dir = self.storage_dir / "controls"
        metrics_dir = self.storage_dir / "metrics"
        
        for evidence_file in sorted(evidence_dir.glob("control_*.json")):
            # Check control ID
            if control_id is not None:
                file_control_id = int(evidence_file.name.split('_')[1])
                if file_control_id != control_id:
                    continue
            
            # Load evidence
            with open(evidence_file) as f:
                evidence = json.load(f)
                
            # Check date range
            timestamp = datetime.fromisoformat(evidence['timestamp'])
            if start_date and timestamp < start_date:
                continue
            if end_date and timestamp > end_date:
                continue
                
            # Load corresponding metrics
            metrics_file = metrics_dir / f"metrics_{evidence_file.name.split('_', 1)[1]}"
            if metrics_file.exists():
                with open(metrics_file) as f:
                    evidence['metrics'] = json.load(f)
                    
            evidence_list.append(evidence)
            
        return evidence_list
    
    def generate_report(self, evidence_list: Optional[List[Dict]] = None) -> str:
        """
        Generate evidence report.
        
        Args:
            evidence_list: Optional list of evidence records (if not provided, gets latest)
            
        Returns:
            Path to generated report
        """
        if evidence_list is None:
            evidence_list = self.get_evidence_history()
            
        if not evidence_list:
            return ""
            
        # Get latest evidence
        latest = evidence_list[-1]
        timestamp = datetime.fromisoformat(latest['timestamp'])
        date_str = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        
        # Generate report
        report_file = self.storage_dir / "reports" / f"report_{date_str}.md"
        
        with open(report_file, 'w') as f:
            f.write(f"# Control Evidence Report\n\n")
            f.write(f"Generated: {timestamp.isoformat()}\n\n")
            
            f.write("## Latest Evidence\n\n")
            f.write(f"Control ID: {latest.get('control_id', 'N/A')}\n")
            f.write(f"Status: {latest.get('status', 'unknown')}\n")
            f.write(f"Timestamp: {latest.get('timestamp', 'N/A')}\n\n")
            
            f.write("### Description\n\n")
            f.write(latest.get('description', 'No description available'))
            f.write("\n\n")
            
            if 'metrics' in latest:
                f.write("### Metrics\n\n")
                metrics = latest['metrics']
                
                if 'summary' in metrics:
                    summary = metrics['summary']
                    f.write("Summary:\n")
                    f.write(f"- Total PRs: {summary.get('total_prs', 0)}\n")
                    f.write(f"- Compliance Rate: {summary.get('compliance_rate', 0):.2f}%\n")
                    f.write(f"- High Risk PRs: {summary.get('high_risk_prs', 0)}\n\n")
                    
                    if 'risk_distribution' in summary:
                        f.write("Risk Distribution:\n")
                        for risk, count in summary['risk_distribution'].items():
                            f.write(f"- {risk}: {count}\n")
                        f.write("\n")
                    
                if 'review_patterns' in metrics:
                    f.write("Review Patterns:\n")
                    for reviewer, count in metrics['review_patterns'].items():
                        f.write(f"- {reviewer}: {count} reviews\n")
                    f.write("\n")
                    
                if 'statistical_metrics' in metrics:
                    f.write("Statistical Metrics:\n")
                    stats = metrics['statistical_metrics']
                    if stats.get('median_review_time') is not None:
                        f.write(f"- Median Review Time: {stats['median_review_time']:.2f} hours\n")
                    if stats.get('avg_review_time') is not None:
                        f.write(f"- Average Review Time: {stats['avg_review_time']:.2f} hours\n")
                    f.write("\n")
            
        logger.info(f"Generated report: {report_file}")
        return str(report_file) 