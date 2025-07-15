# check_github_control.py
import requests
import json
from typing import List, Dict, Set
from requests.exceptions import RequestException
from config import GITHUB_TOKEN, GITHUB_REPO
from datetime import datetime, timedelta

# Setup headers with token
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'}

def get_date_range() -> tuple:
    """Get date range for PR analysis (last 30 days by default)."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    return start_date.isoformat(), end_date.isoformat()

def get_merged_prs(repo: str, per_page: int = 100) -> List[Dict]:
    """
    Fetch merged PRs from the repository.
    Uses pagination to get a larger sample size and date filtering for relevance.
    """
    try:
        start_date, end_date = get_date_range()
        url = f"https://api.github.com/repos/{repo}/pulls"
        params = {
            'state': 'closed',
            'per_page': per_page,
            'sort': 'updated',
            'direction': 'desc'
        }
        
        print(f"\nFetching PRs from: {url}")
        print(f"Using params: {params}")
        print(f"Date range: {start_date} to {end_date}")
        
        all_prs = []
        page = 1
        
        while True:
            params['page'] = page
            resp = requests.get(url, headers=HEADERS, params=params)
            resp.raise_for_status()
            prs = resp.json()
            
            if not prs:
                break
                
            # Filter PRs by merge date and date range
            merged_prs = [
                pr for pr in prs 
                if pr.get('merged_at') 
                and start_date <= pr['merged_at'] <= end_date
            ]
            
            all_prs.extend(merged_prs)
            
            # Stop if we've gone past our date range
            if prs and prs[-1]['updated_at'] < start_date:
                break
                
            page += 1
        
        print(f"Found {len(all_prs)} merged PRs in the last 30 days")
        return all_prs
        
    except RequestException as e:
        print(f"\nDetailed error information:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response headers: {json.dumps(dict(e.response.headers))}")
            print(f"Response body: {e.response.text}")
        raise Exception(f"Error fetching merged PRs: {str(e)}")


def check_approval(pr: Dict, repo: str) -> Dict:
    """
    Check if PR was properly reviewed and approved.
    Returns detailed approval information.
    """
    try:
        pr_number = pr['number']
        author = pr['user']['login']
        created_at = pr['created_at']
        merged_at = pr['merged_at']

        url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
        print(f"\nChecking reviews for PR #{pr_number}")
        
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            print(f"Error getting reviews for PR #{pr_number}: {resp.text}")
            
        resp.raise_for_status()
        reviews = resp.json()

        # Get all approvers and their timestamps
        approvers = {
            r['user']['login']: r['submitted_at'] 
            for r in reviews 
            if r['state'] == 'APPROVED'
        }
        
        # Calculate review metrics
        time_to_first_review = None
        if approvers:
            first_approval = min(approvers.values())
            time_to_first_review = (
                datetime.fromisoformat(first_approval.replace('Z', '+00:00')) -
                datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            ).total_seconds() / 3600  # Convert to hours
        
        approved = any(a != author for a in approvers)
        
        print(f"PR #{pr_number} by {author}")
        print(f"Approvers: {list(approvers.keys())}")
        print(f"Approved by different user: {approved}")
        
        return {
            'approved': approved,
            'approvers': list(approvers.keys()),
            'author': author,
            'time_to_review': time_to_first_review,
            'created_at': created_at,
            'merged_at': merged_at
        }
        
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
    Returns comprehensive metrics about PR reviews.
    """
    try:
        print(f"\nStarting GitHub controls check for repository: {GITHUB_REPO}")
        
        results = {
            'total_prs_checked': 0,
            'properly_reviewed_prs': 0,
            'non_compliant_prs': [],
            'metrics': {
                'avg_time_to_review': 0,
                'max_time_to_review': 0,
                'min_time_to_review': float('inf'),
                'total_unique_reviewers': set(),
                'review_distribution': {}  # Reviewer -> number of reviews
            }
        }

        merged_prs = get_merged_prs(GITHUB_REPO)
        results['total_prs_checked'] = len(merged_prs)
        
        review_times = []

        for pr in merged_prs:
            approval_info = check_approval(pr, GITHUB_REPO)
            
            # Update metrics
            if approval_info['time_to_review'] is not None:
                review_times.append(approval_info['time_to_review'])
                results['metrics']['max_time_to_review'] = max(
                    results['metrics']['max_time_to_review'],
                    approval_info['time_to_review']
                )
                results['metrics']['min_time_to_review'] = min(
                    results['metrics']['min_time_to_review'],
                    approval_info['time_to_review']
                )
            
            # Update reviewer statistics
            for reviewer in approval_info['approvers']:
                results['metrics']['total_unique_reviewers'].add(reviewer)
                results['metrics']['review_distribution'][reviewer] = \
                    results['metrics']['review_distribution'].get(reviewer, 0) + 1
            
            if approval_info['approved']:
                results['properly_reviewed_prs'] += 1
            else:
                results['non_compliant_prs'].append({
                    'number': pr['number'],
                    'title': pr['title'],
                    'url': pr['html_url'],
                    'author': approval_info['author'],
                    'created_at': approval_info['created_at'],
                    'merged_at': approval_info['merged_at'],
                    'approvers': approval_info['approvers']
                })

        # Calculate average review time
        if review_times:
            results['metrics']['avg_time_to_review'] = sum(review_times) / len(review_times)
            
        # Convert set to list for JSON serialization
        results['metrics']['total_unique_reviewers'] = \
            list(results['metrics']['total_unique_reviewers'])

        print("\nControl check completed successfully")
        print(f"Total PRs checked: {results['total_prs_checked']}")
        print(f"Properly reviewed PRs: {results['properly_reviewed_prs']}")
        print(f"Non-compliant PRs: {len(results['non_compliant_prs'])}")
        print("\nMetrics:")
        print(f"Average time to review: {results['metrics']['avg_time_to_review']:.2f} hours")
        print(f"Unique reviewers: {len(results['metrics']['total_unique_reviewers'])}")
        
        return results

    except Exception as e:
        print(f"\nFatal error in GitHub controls check:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        raise Exception(f"Error in GitHub controls check: {str(e)}")