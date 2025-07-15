# submit_eramba_evidence.py
import os
import requests
from datetime import datetime
from typing import Dict, Tuple
from requests.exceptions import RequestException

# Get configuration from environment variables
ERAMBA_API_URL = os.getenv('ERAMBA_API_URL')
ERAMBA_TOKEN = os.getenv('ERAMBA_TOKEN')


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
        if not ERAMBA_TOKEN:
            raise ValueError("ERAMBA_TOKEN environment variable is not set")
        if not ERAMBA_API_URL:
            raise ValueError("ERAMBA_API_URL environment variable is not set")

        headers = {'Authorization': f'Token {ERAMBA_TOKEN}'}
        payload = {
            'control_id': control_id,
            'date': datetime.utcnow().isoformat(),
            'result': result,
            'description': description
        }
        
        resp = requests.post(ERAMBA_API_URL, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.status_code, resp.text
        
    except RequestException as e:
        raise Exception(f"Error sending evidence to Eramba: {str(e)}")


def submit_evidence() -> Dict[str, any]:
    """
    Main function to submit evidence to Eramba.
    Returns a dictionary with the submission results.
    """
    try:
        # Get GitHub control results
        from check_github_control import check_github_controls
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
        # Note: Replace 123 with your actual control ID in Eramba
        status_code, response = send_evidence(
            control_id=123,  # Replace with actual control ID
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
