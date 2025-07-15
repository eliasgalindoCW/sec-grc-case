# check_github_control.py
import requests
import json
from typing import List, Dict, Set
from requests.exceptions import RequestException
from config import GITHUB_TOKEN, GITHUB_REPO

# Setup headers with token
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'}


def get_merged_prs(repo: str, per_page: int = 30) -> List[Dict]:
    """Busca os PRs que foram merged no repositório."""
    try:
        url = f"https://api.github.com/repos/{repo}/pulls"
        params = {'state': 'closed', 'per_page': per_page}
        
        print(f"\nFetching PRs from: {url}")
        print(f"Using params: {params}")
        print(f"Headers: {json.dumps({'Authorization': 'token ****'})}")  # Hide actual token
        
        resp = requests.get(url, headers=HEADERS, params=params)
        
        print(f"Response status code: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Error response: {resp.text}")
            
        resp.raise_for_status()
        prs = resp.json()
        
        merged_prs = [pr for pr in prs if pr.get('merged_at')]
        print(f"Found {len(prs)} total PRs, {len(merged_prs)} were merged")
        
        return merged_prs
    except RequestException as e:
        print(f"\nDetailed error information:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response headers: {json.dumps(dict(e.response.headers))}")
            print(f"Response body: {e.response.text}")
        raise Exception(f"Error fetching merged PRs: {str(e)}")


def check_approval(pr: Dict, repo: str) -> bool:
    """Verifica se o PR foi aprovado por alguém diferente do autor."""
    try:
        pr_number = pr['number']
        author = pr['user']['login']

        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
        print(f"\nChecking reviews for PR #{pr_number}")
        
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            print(f"Error getting reviews for PR #{pr_number}: {resp.text}")
            
        resp.raise_for_status()
        reviews = resp.json()

        approvers: Set[str] = {r['user']['login'] for r in reviews if r['state'] == 'APPROVED'}
        approved = any(a != author for a in approvers)
        
        print(f"PR #{pr_number} by {author}")
        print(f"Approvers: {approvers}")
        print(f"Approved by different user: {approved}")
        
        return approved
    except RequestException as e:
        print(f"\nError checking PR #{pr_number} approval:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        raise Exception(f"Error checking PR approval: {str(e)}")


def check_github_controls() -> Dict[str, any]:
    """
    Main function to check GitHub controls.
    Returns a dictionary with the control check results.
    """
    try:
        print(f"\nStarting GitHub controls check for repository: {GITHUB_REPO}")
        
        results = {
            'total_prs_checked': 0,
            'properly_reviewed_prs': 0,
            'non_compliant_prs': []
        }

        merged_prs = get_merged_prs(GITHUB_REPO)
        results['total_prs_checked'] = len(merged_prs)

        for pr in merged_prs:
            if check_approval(pr, GITHUB_REPO):
                results['properly_reviewed_prs'] += 1
            else:
                results['non_compliant_prs'].append({
                    'number': pr['number'],
                    'title': pr['title'],
                    'url': pr['html_url']
                })

        print("\nControl check completed successfully")
        print(f"Total PRs checked: {results['total_prs_checked']}")
        print(f"Properly reviewed PRs: {results['properly_reviewed_prs']}")
        print(f"Non-compliant PRs: {len(results['non_compliant_prs'])}")
        
        return results

    except Exception as e:
        print(f"\nFatal error in GitHub controls check:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        raise Exception(f"Error in GitHub controls check: {str(e)}")