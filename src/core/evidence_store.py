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
    
    def _get_evidence_path(self, control_id: int, timestamp: datetime) -> Path:
        """Get path for evidence file."""
        date_str = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        return self.storage_dir / "controls" / f"control_{control_id}_{date_str}.json"
    
    def _get_metrics_path(self, control_id: int, timestamp: datetime) -> Path:
        """Get path for metrics file."""
        date_str = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        return self.storage_dir / "metrics" / f"metrics_{control_id}_{date_str}.json"
    
    def store_evidence(
        self,
        control_id: int,
        status: str,
        description: str,
        metrics: Dict,
        attachments: Optional[List[str]] = None
    ) -> Dict:
        """
        Store control evidence locally.
        
        Args:
            control_id: Control identifier
            status: Control status (pass/fail)
            description: Evidence description
            metrics: Additional metrics
            attachments: Optional list of attachment paths
            
        Returns:
            Dictionary with storage information
        """
        timestamp = datetime.utcnow()
        
        # Prepare evidence data
        evidence_data = {
            'control_id': control_id,
            'timestamp': timestamp.isoformat(),
            'status': status,
            'description': description,
            'metrics': metrics,
            'attachments': attachments or []
        }
        
        # Save evidence
        evidence_path = self._get_evidence_path(control_id, timestamp)
        with open(evidence_path, 'w') as f:
            json.dump(evidence_data, f, indent=2)
        
        # Save metrics separately for analysis
        metrics_path = self._get_metrics_path(control_id, timestamp)
        with open(metrics_path, 'w') as f:
            json.dump({
                'control_id': control_id,
                'timestamp': timestamp.isoformat(),
                'metrics': metrics
            }, f, indent=2)
        
        logger.info(f"Stored evidence for control {control_id}")
        logger.info(f"Evidence file: {evidence_path}")
        logger.info(f"Metrics file: {metrics_path}")
        
        return {
            'success': True,
            'evidence_file': str(evidence_path),
            'metrics_file': str(metrics_path),
            'timestamp': timestamp.isoformat()
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
        evidence_files = list(self.storage_dir.glob("controls/control_*.json"))
        
        results = []
        for file_path in evidence_files:
            with open(file_path) as f:
                evidence = json.load(f)
                
            # Apply filters
            if control_id and evidence['control_id'] != control_id:
                continue
                
            evidence_date = datetime.fromisoformat(evidence['timestamp'])
            if start_date and evidence_date < start_date:
                continue
            if end_date and evidence_date > end_date:
                continue
                
            results.append(evidence)
        
        return sorted(results, key=lambda x: x['timestamp'], reverse=True)
    
    def generate_report(
        self,
        control_ids: Optional[List[int]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Generate a report of evidence history.
        
        Args:
            control_ids: Optional list of control IDs to include
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Path to generated report file
        """
        timestamp = datetime.utcnow()
        report_path = self.storage_dir / "reports" / f"report_{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.md"
        
        # Get evidence history
        evidence_list = self.get_evidence_history(start_date=start_date, end_date=end_date)
        if control_ids:
            evidence_list = [e for e in evidence_list if e['control_id'] in control_ids]
        
        # Generate report
        with open(report_path, 'w') as f:
            f.write("# Control Evidence Report\n\n")
            f.write(f"Generated: {timestamp.isoformat()}\n\n")
            
            if not evidence_list:
                f.write("No evidence found for the specified criteria.\n")
                return str(report_path)
            
            # Group by control
            controls = {}
            for evidence in evidence_list:
                control_id = evidence['control_id']
                if control_id not in controls:
                    controls[control_id] = []
                controls[control_id].append(evidence)
            
            # Write each control's evidence
            for control_id, control_evidence in controls.items():
                f.write(f"\n## Control {control_id}\n\n")
                
                for evidence in control_evidence:
                    f.write(f"### Evidence from {evidence['timestamp']}\n\n")
                    f.write(f"Status: {evidence['status']}\n\n")
                    f.write(f"Description:\n{evidence['description']}\n\n")
                    f.write("Metrics:\n")
                    for key, value in evidence['metrics'].items():
                        f.write(f"- {key}: {value}\n")
                    f.write("\n---\n")
        
        logger.info(f"Generated report: {report_path}")
        return str(report_path) 