#!/usr/bin/env python3
"""
Linear Status Poster

Posts workflow status updates to Linear for monitoring and tracking.

Author: Stephen Thompson
"""

import argparse
import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime


def post_status(api_key: str, status: str, run_id: str) -> bool:
    """
    Post workflow status to Linear.
    
    Args:
        api_key: Linear API key
        status: Workflow status (success, failure, cancelled)
        run_id: Unique run identifier
        
    Returns:
        True if successful
    """
    if not api_key:
        print("ℹ️  LINEAR_API_KEY not configured - skipping Linear status update")
        print(f"   Status: {status.upper()}, Run ID: {run_id}")
        return True  # Return True to indicate graceful skip
    
    # Create status emoji and message
    status_emoji = {
        'success': '✅',
        'failure': '❌',
        'cancelled': '⚠️',
        'skipped': '⏭️'
    }
    
    emoji = status_emoji.get(status, '📊')
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    # For now, just log the status
    # In production, you could post to a specific Linear issue or webhook
    print(f"{emoji} Workflow Status: {status.upper()}")
    print(f"Run ID: {run_id}")
    print(f"Timestamp: {timestamp}")
    
    return True


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Post workflow status to Linear"
    )
    parser.add_argument(
        "--status",
        type=str,
        required=True,
        choices=['success', 'failure', 'cancelled', 'skipped'],
        help="Workflow status"
    )
    parser.add_argument(
        "--run-id",
        type=str,
        required=True,
        help="Unique run identifier"
    )
    
    args = parser.parse_args()
    
    api_key = os.environ.get('LINEAR_API_KEY', '')
    
    try:
        success = post_status(api_key, args.status, args.run_id)
        # Always return 0 (success) to avoid failing workflows
        # when LINEAR_API_KEY is not configured
        return 0
    except Exception as e:
        print(f"Warning: {e}", file=sys.stderr)
        # Return 0 even on error to avoid failing the workflow
        # Linear integration is optional
        return 0


if __name__ == "__main__":
    sys.exit(main())
