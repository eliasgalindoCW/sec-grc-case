#!/usr/bin/env python3

import sys
from typing import Optional

# Import functions from other modules
try:
    from check_github_control import check_github_controls
    from submit_eramba_evidence import submit_evidence
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

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
            print("Checking GitHub controls...")
            check_github_controls()
            
        if action is None or action.lower() == 'submit':
            print("Submitting evidence to Eramba...")
            submit_evidence()
            
    except Exception as e:
        print(f"Error during execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Parse command line arguments
    action = sys.argv[1] if len(sys.argv) > 1 else None
    
    if action and action.lower() not in ['check', 'submit']:
        print("Invalid action. Use 'check' for GitHub controls or 'submit' for Eramba evidence.")
        sys.exit(1)
        
    main(action)
