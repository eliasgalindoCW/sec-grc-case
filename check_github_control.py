# check_github_control.py
import os
import requests
from typing import List, Dict, Set
from requests.exceptions import RequestException

# Get configuration from environment variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO = os.getenv('GITHUB_REPO')
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'}


def get_merged_prs(repo: str, per_page: int = 30) -> List[Dict]:
    """Busca os PRs que foram merged no repositório."""
    try:
        url = f"https://api.github.com/repos/{repo}/pulls"
        params = {'state': 'closed', 'per_page': per_page}
        resp = requests.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        prs = resp.json()
        return [pr for pr in prs if pr.get('merged_at')]
    except RequestException as e:
        raise Exception(f"Error fetching merged PRs: {str(e)}")


def check_approval(pr: Dict, repo: str) -> bool:
    """Verifica se o PR foi aprovado por alguém diferente do autor."""
    try:
        pr_number = pr['number']
        author = pr['user']['login']

        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        reviews = resp.json()

        approvers: Set[str] = {r['user']['login'] for r in reviews if r['state'] == 'APPROVED'}
        return any(a != author for a in approvers)
    except RequestException as e:
        raise Exception(f"Error checking PR approval: {str(e)}")


def check_github_controls() -> Dict[str, any]:
    """
    Main function to check GitHub controls.
    Returns a dictionary with the control check results.
    """
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN environment variable is not set")
    if not REPO:
        raise ValueError("GITHUB_REPO environment variable is not set")

    try:
        results = {
            'total_prs_checked': 0,
            'properly_reviewed_prs': 0,
            'non_compliant_prs': []
        }

        merged_prs = get_merged_prs(REPO)
        results['total_prs_checked'] = len(merged_prs)

        for pr in merged_prs:
            if check_approval(pr, REPO):
                results['properly_reviewed_prs'] += 1
            else:
                results['non_compliant_prs'].append({
                    'number': pr['number'],
                    'title': pr['title'],
                    'url': pr['html_url']
                })

        return results

    except Exception as e:
        raise Exception(f"Error in GitHub controls check: {str(e)}")