# submit_eramba_evidence.py
import requests
from datetime import datetime
import datetime as dt
from typing import Dict, Tuple
from requests.exceptions import RequestException
from src.utils.config import ERAMBA_API_URL, ERAMBA_TOKEN, ERAMBA_CONTROL_ID
import os
import json
import urllib3

# Disable SSL warnings when verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# SSL verification configuration
VERIFY_SSL = os.getenv('VERIFY_SSL', 'true').lower() == 'true'

def get_eramba_session() -> requests.Session:
    """
    Initialize a session with Eramba and handle authentication.
    """
    try:
        session = requests.Session()
        
        # Configure session
        session.verify = VERIFY_SSL
        session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Token {ERAMBA_TOKEN}'
        })
        
        print(f"\nTesting connection to Eramba at: {ERAMBA_API_URL}")
        
        # Test connection
        response = session.get(
            f"{ERAMBA_API_URL}/api/users/me",
            verify=VERIFY_SSL
        )
        
        if response.status_code == 200:
            print("Successfully connected to Eramba")
            return session
        else:
            print(f"Connection test failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            raise Exception("Failed to connect to Eramba")
            
    except Exception as e:
        raise Exception(f"Error connecting to Eramba: {str(e)}")

def send_evidence(control_id: int, result: str, description: str) -> Tuple[int, str]:
    """
    Send evidence to Eramba API.
    
    Args:
        control_id: The ID of the control in Eramba
        result: The result of the control check
        description: Detailed description of the evidence
        
    Returns:
        Tuple of (status_code, response_text)
    """
    try:
        # Get authenticated session
        session = get_eramba_session()
        
        # Prepare payload
        payload = {
            'control_id': control_id,
            'date': datetime.now(dt.UTC).isoformat(),
            'result': result,
            'description': description
        }
        
        print(f"\nSending evidence to Eramba:")
        print(f"URL: {ERAMBA_API_URL}/api/evidences")
        print(f"Control ID: {control_id}")
        print(f"SSL Verification: {'Enabled' if VERIFY_SSL else 'Disabled'}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Send request using the session
        resp = session.post(
            f"{ERAMBA_API_URL}/api/evidences",
            json=payload
        )
        
        print(f"Response status code: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Error response: {resp.text}")
            
        resp.raise_for_status()
        return resp.status_code, resp.text
        
    except RequestException as e:
        print(f"\nDetailed error information:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        raise Exception(f"Error sending evidence to Eramba: {str(e)}")


def submit_evidence() -> Dict[str, any]:
    """
    Main function to submit evidence to Eramba.
    Returns a dictionary with the submission results.
    """
    try:
        # Get GitHub control results
        from src.core.check_github_control import check_github_controls
        github_results = check_github_controls()
        
        # Prepare evidence description
        description = f"""
GitHub PR Review Control Check Results:
- Total PRs checked: {github_results['total_prs_checked']}
- Properly reviewed PRs: {github_results['properly_reviewed_prs']}
- Non-compliant PRs: {len(github_results['non_compliant_prs'])}

Non-compliant PRs:
{chr(10).join([f"- PR #{pr['number']}: {pr['title']} ({pr['url']})" for pr in github_results['non_compliant_prs']])}
        """.strip()
        
        # Submit evidence to Eramba
        status_code, response = send_evidence(
            control_id=ERAMBA_CONTROL_ID,
            result='pass' if len(github_results['non_compliant_prs']) == 0 else 'fail',
            description=description
        )
        
        return {
            'success': 200 <= status_code < 300,
            'status_code': status_code,
            'response': response,
            'github_results': github_results
        }
        
    except Exception as e:
        raise Exception(f"Error submitting evidence: {str(e)}")
