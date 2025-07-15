#!/usr/bin/env python3

import sys
from typing import Optional, Dict

try:
    from check_github_control import check_github_controls
    from submit_eramba_evidence import submit_evidence
    import config
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def print_results(results: Dict):
    """Print results in a formatted way."""
    if isinstance(results, dict):
        print("\nResults:")
        for key, value in results.items():
            if isinstance(value, (list, dict)):
                print(f"\n{key}:")
                if isinstance(value, list):
                    for item in value:
                        print(f"  - {item}")
                else:
                    for k, v in value.items():
                        print(f"  {k}: {v}")
            else:
                print(f"{key}: {value}")

def main(action: Optional[str] = None) -> None:
    """
    Main function to orchestrate the execution of GitHub control checks
    and Eramba evidence submission.
    
    Args:
        action: Optional string specifying which action to run:
               'check' for GitHub controls check
               'submit' for Eramba evidence submission
               None to run both
    """
    try:
        if action is None or action.lower() == 'check':
            print("\nChecking GitHub controls...")
            results = check_github_controls()
            print_results(results)
            
        if action is None or action.lower() == 'submit':
            print("\nSubmitting evidence to Eramba...")
            results = submit_evidence()
            print_results(results)
            
    except Exception as e:
        print(f"\nError during execution: {str(e)}")
        if "Requires authentication" in str(e):
            print("\nAuthentication failed. Please check your GitHub token in config.py")
            print("1. Ensure GITHUB_TOKEN is set correctly")
            print("2. Verify the token has not expired")
            print("3. Confirm the token has the necessary permissions (repo scope)")
        sys.exit(1)

if __name__ == "__main__":
    # Parse command line arguments
    action = sys.argv[1] if len(sys.argv) > 1 else None
    
    if action and action.lower() not in ['check', 'submit']:
        print("Invalid action. Use 'check' for GitHub controls or 'submit' for Eramba evidence.")
        sys.exit(1)
        
    main(action)
