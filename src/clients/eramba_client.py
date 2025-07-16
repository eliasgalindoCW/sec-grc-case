"""
Eramba API Client

This module handles the interaction with Eramba's REST API for submitting control evidence.
It implements a structured approach to:
1. Authentication and session management
2. Evidence formatting and submission
3. Control status updates
4. Audit trail maintenance
"""

import requests
from typing import Dict, Optional, Union
from datetime import datetime
import json
from dataclasses import dataclass
from enum import Enum
import urllib3
import logging
import re
import ssl
import certifi
from urllib3.exceptions import InsecureRequestWarning

from src.utils.logging_config import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

# Configure SSL context for self-signed certificates
def create_ssl_context(verify_ssl: bool = True) -> Optional[ssl.SSLContext]:
    """Create SSL context based on verification settings."""
    if verify_ssl:
        return ssl.create_default_context(cafile=certifi.where())
    else:
        # Disable SSL verification warnings when using self-signed certificates
        urllib3.disable_warnings(InsecureRequestWarning)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

class ErambaEnvironment(Enum):
    """Environment types for Eramba deployment."""
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"

class ErambaControlStatus(Enum):
    """Possible control status values."""
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    UNKNOWN = "unknown"

@dataclass
class ErambaEvidence:
    """Structured format for evidence submission."""
    control_id: int
    status: ErambaControlStatus
    description: str
    metrics: Dict
    timestamp: datetime = None
    attachments: list = None
    
    def __post_init__(self):
        self.timestamp = self.timestamp or datetime.utcnow()
        self.attachments = self.attachments or []

class ErambaClient:
    """
    Client for interacting with Eramba's REST API.
    Handles authentication, evidence submission, and status updates.
    """
    
    def __init__(
        self,
        base_url: str,
        api_token: str,
        environment: ErambaEnvironment = ErambaEnvironment.LOCAL,
        verify_ssl: bool = True
    ):
        """
        Initialize Eramba client.
        
        Args:
            base_url: Eramba instance base URL
            api_token: API token for authentication
            environment: Which environment we're connecting to
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.environment = environment
        self.verify_ssl = verify_ssl and environment != ErambaEnvironment.LOCAL
        
        # Create session with proper SSL handling
        self.session = requests.Session()
        if not self.verify_ssl:
            self.session.verify = False
            # Disable SSL verification warnings
            urllib3.disable_warnings(InsecureRequestWarning)
            logger.warning("SSL certificate verification is disabled!")
        
        # Initialize session
        self._initialize_session()
            
        logger.info(f"Initialized Eramba client for {environment.value} environment")
        logger.info(f"Base URL: {base_url}")
        logger.info(f"SSL Verification: {'Enabled' if self.verify_ssl else 'Disabled'}")
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with proper error handling and SSL configuration.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Target URL
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
        """
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL Error: {str(e)}")
            if self.verify_ssl:
                logger.info("Consider using verify_ssl=False for local development with self-signed certificates")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Error: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"Response Status: {e.response.status_code}")
                logger.error(f"Response Body: {e.response.text}")
            raise
    
    def _initialize_session(self):
        """Initialize session with proper authentication."""
        try:
            # First, get the login page to get CSRF token
            response = self._make_request('GET', f"{self.base_url}/auth/login")
            
            # Extract CSRF token from the page
            csrf_token = None
            match = re.search(r'name="_token"\s+value="([^"]+)"', response.text)
            if match:
                csrf_token = match.group(1)
            
            if not csrf_token:
                logger.warning("Could not find CSRF token in login page")
            
            # Setup headers
            self.session.headers.update({
                'X-CSRF-TOKEN': csrf_token if csrf_token else '',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            })
            
            # Attempt login
            login_data = {
                '_token': csrf_token,
                'api_token': self.api_token
            }
            
            response = self._make_request(
                'POST',
                f"{self.base_url}/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                logger.info("Successfully authenticated with Eramba")
            else:
                logger.warning(f"Authentication response: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to initialize session: {str(e)}")
    
    def _get_api_endpoint(self, path: str) -> str:
        """Construct API endpoint URL based on environment."""
        if self.environment == ErambaEnvironment.LOCAL:
            # Local Docker setup uses Laravel API
            return f"{self.base_url}/api/{path.lstrip('/')}"
        else:
            # Production/staging setup
            return f"{self.base_url}/api/{path.lstrip('/')}"
    
    def test_connection(self) -> bool:
        """Test connection and authentication with Eramba."""
        try:
            # Try different endpoints based on environment
            endpoints = [
                '/api/dashboard',  # Common endpoint
                '/api/user/profile',  # User profile endpoint
                '/api/settings'  # Settings endpoint
            ]
            
            for endpoint in endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    logger.info(f"Testing connection to {url}")
                    
                    response = self._make_request('GET', url)
                    if response.status_code == 200:
                        logger.info("Successfully connected to Eramba")
                        return True
                    elif response.status_code == 401:
                        logger.warning("Authentication failed, attempting to re-initialize session")
                        self._initialize_session()
                        # Retry the request
                        response = self._make_request('GET', url)
                        if response.status_code == 200:
                            logger.info("Successfully connected after re-authentication")
                            return True
                            
                except requests.RequestException as e:
                    logger.warning(f"Failed to connect to {endpoint}: {str(e)}")
                    continue
            
            logger.error("Failed to connect to any endpoint")
            return False
            
        except Exception as e:
            logger.error(f"Failed to connect to Eramba: {str(e)}")
            return False
    
    def format_evidence(self, pr_analysis: Dict) -> str:
        """
        Format PR analysis results into structured evidence.
        
        Args:
            pr_analysis: Analysis results from PullRequestAnalyzer
            
        Returns:
            Formatted evidence description
        """
        evidence = []
        
        # Add analysis metadata
        evidence.append("## Pull Request Review Control Analysis")
        evidence.append(f"Analysis Date: {pr_analysis['analysis_metadata']['analysis_date']}")
        evidence.append(f"Repository: {pr_analysis['analysis_metadata']['repository']}")
        evidence.append(f"Period: Last {pr_analysis['analysis_metadata']['days_analyzed']} days")
        evidence.append("")
        
        # Add compliance summary
        evidence.append("### Compliance Summary")
        evidence.append(f"- Total PRs Analyzed: {pr_analysis['summary']['total_prs']}")
        evidence.append(f"- Compliance Rate: {pr_analysis['summary']['compliance_rate']:.2f}%")
        evidence.append(f"- Compliant PRs: {pr_analysis['summary']['compliant_prs']}")
        evidence.append(f"- Non-compliant PRs: {pr_analysis['summary']['non_compliant_prs']}")
        evidence.append(f"- High Risk PRs: {pr_analysis['summary']['high_risk_prs']}")
        evidence.append("")
        
        # Add risk distribution
        evidence.append("### Risk Distribution")
        for risk, count in pr_analysis['summary']['risk_distribution'].items():
            evidence.append(f"- {risk}: {count}")
        evidence.append("")
        
        # Add statistical metrics if available
        if pr_analysis.get('statistical_metrics'):
            evidence.append("### Review Time Statistics (hours)")
            for metric, value in pr_analysis['statistical_metrics'].items():
                evidence.append(f"- {metric}: {value:.2f}")
            evidence.append("")
        
        # Add review patterns
        evidence.append("### Review Patterns")
        for reviewer, count in pr_analysis['review_patterns'].items():
            evidence.append(f"- {reviewer}: {count} reviews")
        evidence.append("")
        
        # Add non-compliant details
        if pr_analysis['non_compliant_details']:
            evidence.append("### Non-compliant and High Risk PRs")
            for pr in pr_analysis['non_compliant_details']:
                evidence.append(f"\nPR #{pr['number']}: {pr['title']}")
                evidence.append(f"- Author: {pr['author']}")
                evidence.append(f"- Created: {pr['created_at']}")
                evidence.append(f"- Risk Level: {pr['risk_level']}")
                if pr.get('risk_factors'):
                    evidence.append(f"- Risk Factors: {', '.join(pr['risk_factors'])}")
                evidence.append(f"- URL: {pr['url']}")
        
        return "\n".join(evidence)
    
    def determine_control_status(self, pr_analysis: Dict) -> ErambaControlStatus:
        """
        Determine control status based on analysis results.
        
        Args:
            pr_analysis: Analysis results from PullRequestAnalyzer
            
        Returns:
            Appropriate control status
        """
        compliance_rate = pr_analysis['summary']['compliance_rate']
        high_risk_count = pr_analysis['summary']['high_risk_prs']
        
        if compliance_rate >= 95 and high_risk_count == 0:
            return ErambaControlStatus.PASS
        elif compliance_rate >= 80:
            return ErambaControlStatus.PARTIAL
        else:
            return ErambaControlStatus.FAIL
    
    def submit_evidence(self, control_id: int, pr_analysis: Dict) -> Dict:
        """
        Submit control evidence to Eramba.
        
        Args:
            control_id: Eramba control ID
            pr_analysis: Analysis results from PullRequestAnalyzer
            
        Returns:
            API response data
        """
        # Format evidence and determine status
        evidence_description = self.format_evidence(pr_analysis)
        status = self.determine_control_status(pr_analysis)
        
        # Prepare evidence object
        evidence = ErambaEvidence(
            control_id=control_id,
            status=status,
            description=evidence_description,
            metrics={
                'compliance_rate': pr_analysis['summary']['compliance_rate'],
                'total_prs': pr_analysis['summary']['total_prs'],
                'high_risk_prs': pr_analysis['summary']['high_risk_prs']
            }
        )
        
        # Prepare request payload
        payload = {
            'control_id': evidence.control_id,
            'status': evidence.status.value,
            'description': evidence.description,
            'evidence_data': {
                'metrics': evidence.metrics,
                'timestamp': evidence.timestamp.isoformat(),
                'type': 'automated_check'
            }
        }
        
        try:
            # First, check if we need to re-authenticate
            if not self.test_connection():
                self._initialize_session()
            
            # Submit evidence
            endpoint = self._get_api_endpoint(f"security-controls/{control_id}/evidence")
            logger.info(f"Submitting evidence to {endpoint}")
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = self._make_request('POST', endpoint, json=payload)
            
            if response.status_code == 401:
                logger.warning("Authentication expired, re-initializing session")
                self._initialize_session()
                response = self._make_request('POST', endpoint, json=payload)
            
            if 200 <= response.status_code < 300:
                logger.info("Successfully submitted evidence")
                return {
                    'success': True,
                    'status': evidence.status.value,
                    'response': response.json() if response.text else {},
                    'evidence': evidence_description
                }
            else:
                logger.error(f"Failed to submit evidence: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code}",
                    'response': response.text,
                    'evidence': evidence_description
                }
            
        except Exception as e:
            logger.error(f"Failed to submit evidence: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"Response: {e.response.text}")
            return {
                'success': False,
                'error': str(e),
                'status': evidence.status.value,
                'evidence': evidence_description
            }
    
    def get_control_info(self, control_id: int) -> Optional[Dict]:
        """Get information about a specific control."""
        try:
            response = self._make_request('GET', f"{self.base_url}/api/controls/{control_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to get control info: {str(e)}")
            return None
    
    def get_evidence_history(self, control_id: int) -> Optional[Dict]:
        """Get evidence history for a specific control."""
        try:
            response = self._make_request(
                'GET',
                f"{self.base_url}/api/controls/{control_id}/evidence"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to get evidence history: {str(e)}")
            return None 