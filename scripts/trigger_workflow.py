#!/usr/bin/env python3
"""
GitHub Actions Workflow Trigger Script

This script provides a convenient way to trigger the GitHub API scraper workflow
programmatically, ideal for Poke integration or other automation systems.

Usage:
    python trigger_workflow.py --mode repository --target microsoft/vscode
    python trigger_workflow.py --mode batch_repos --target "repo1,repo2,repo3" --email notify@example.com
    python trigger_workflow.py --config config.json

Author: Stephen Thompson
"""

import argparse
import json
import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path
import requests
from datetime import datetime


class WorkflowTrigger:
    """Class for triggering GitHub Actions workflows via repository dispatch."""
    
    def __init__(self, token: Optional[str] = None, 
                 owner: str = "CrazyDubya", 
                 repo: str = "research-scrapers"):
        """
        Initialize the workflow trigger.
        
        Args:
            token: GitHub personal access token
            owner: Repository owner
            repo: Repository name
        """
        self.token = token or os.environ.get('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token required. Set GITHUB_TOKEN environment variable or pass token parameter.")
        
        self.owner = owner
        self.repo = repo
        self.api_base = "https://api.github.com"
    
    def trigger_workflow(self, 
                        scraper_mode: str,
                        target: str,
                        output_format: str = "json",
                        include_commits: bool = False,
                        include_issues: bool = False,
                        include_pull_requests: bool = False,
                        max_items: int = 100,
                        parallel_execution: bool = True,
                        notification_email: Optional[str] = None,
                        slack_webhook: Optional[str] = None,
                        artifact_retention_days: int = 30,
                        debug_mode: bool = False,
                        event_type: str = "scrape-github-api") -> Dict[str, Any]:
        """
        Trigger the GitHub Actions workflow.
        
        Args:
            scraper_mode: Type of scraping (repository, user, issues, etc.)
            target: Target to scrape (owner/repo, username, etc.)
            output_format: Output format (json, csv, both)
            include_commits: Include commit history
            include_issues: Include issues data
            include_pull_requests: Include pull requests data
            max_items: Maximum items to fetch
            parallel_execution: Enable parallel execution
            notification_email: Email for notifications
            slack_webhook: Slack webhook URL
            artifact_retention_days: Artifact retention period
            debug_mode: Enable debug logging
            event_type: Event type (scrape-github-api or poke-trigger)
        
        Returns:
            Response from GitHub API
        """
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/dispatches"
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "event_type": event_type,
            "client_payload": {
                "scraper_mode": scraper_mode,
                "target": target,
                "output_format": output_format,
                "include_commits": include_commits,
                "include_issues": include_issues,
                "include_pull_requests": include_pull_requests,
                "max_items": max_items,
                "parallel_execution": parallel_execution,
                "artifact_retention_days": artifact_retention_days,
                "debug_mode": debug_mode,
                "triggered_at": datetime.utcnow().isoformat() + "Z",
                "triggered_by": "trigger_workflow.py"
            }
        }
        
        # Add optional parameters
        if notification_email:
            payload["client_payload"]["notification_email"] = notification_email
        
        if slack_webhook:
            payload["client_payload"]["slack_webhook"] = slack_webhook
        
        print(f"Triggering workflow: {scraper_mode} for {target}")
        print(f"Event type: {event_type}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 204:
            print("✅ Workflow triggered successfully!")
            return {
                "success": True,
                "status_code": response.status_code,
                "message": "Workflow dispatched successfully"
            }
        else:
            print(f"❌ Failed to trigger workflow: {response.status_code}")
            print(f"Response: {response.text}")
            return {
                "success": False,
                "status_code": response.status_code,
                "message": response.text
            }
    
    def trigger_from_config(self, config_file: str) -> Dict[str, Any]:
        """
        Trigger workflow from a JSON configuration file.
        
        Args:
            config_file: Path to JSON configuration file
        
        Returns:
            Response from GitHub API
        """
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return self.trigger_workflow(**config)
    
    def check_workflow_status(self) -> Dict[str, Any]:
        """
        Check the status of recent workflow runs.
        
        Returns:
            Dictionary with workflow run information
        """
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/actions/runs"
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self.token}"
        }
        
        params = {
            "per_page": 5,
            "event": "repository_dispatch"
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            runs = data.get('workflow_runs', [])
            
            print(f"\n📊 Recent workflow runs ({len(runs)}):\n")
            
            for run in runs:
                status_emoji = {
                    'completed': '✅',
                    'in_progress': '🔄',
                    'queued': '⏳',
                    'failure': '❌'
                }.get(run.get('status'), '❓')
                
                print(f"{status_emoji} Run #{run.get('run_number')}")
                print(f"   Status: {run.get('status')} / {run.get('conclusion')}")
                print(f"   Created: {run.get('created_at')}")
                print(f"   URL: {run.get('html_url')}")
                print()
            
            return {"success": True, "runs": runs}
        else:
            print(f"❌ Failed to fetch workflow status: {response.status_code}")
            return {"success": False, "status_code": response.status_code}


def create_sample_config(output_file: str = "workflow_config.json"):
    """Create a sample configuration file."""
    sample_config = {
        "scraper_mode": "repository",
        "target": "microsoft/vscode",
        "output_format": "json",
        "include_commits": False,
        "include_issues": True,
        "include_pull_requests": True,
        "max_items": 100,
        "parallel_execution": True,
        "notification_email": "your-email@example.com",
        "artifact_retention_days": 30,
        "debug_mode": False,
        "event_type": "scrape-github-api"
    }
    
    with open(output_file, 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print(f"✅ Sample configuration created: {output_file}")
    print(f"Edit this file and use: python trigger_workflow.py --config {output_file}")


def main():
    """Command-line interface for workflow trigger."""
    parser = argparse.ArgumentParser(
        description='Trigger GitHub Actions workflow for API scraping',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic repository scraping
  python trigger_workflow.py --mode repository --target microsoft/vscode
  
  # Comprehensive scraping with notifications
  python trigger_workflow.py --mode comprehensive --target facebook/react \\
    --include-commits --include-issues --include-prs \\
    --email notifications@example.com
  
  # Batch processing multiple repositories
  python trigger_workflow.py --mode batch_repos \\
    --target "microsoft/vscode,facebook/react,google/tensorflow" \\
    --parallel
  
  # User profile scraping
  python trigger_workflow.py --mode user --target torvalds
  
  # Using a configuration file
  python trigger_workflow.py --config my_config.json
  
  # Check workflow status
  python trigger_workflow.py --check-status
  
  # Create sample configuration file
  python trigger_workflow.py --create-config
        """
    )
    
    # Action group
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument('--check-status', action='store_true',
                             help='Check recent workflow run status')
    action_group.add_argument('--create-config', action='store_true',
                             help='Create a sample configuration file')
    
    # Configuration
    parser.add_argument('--config', help='JSON configuration file path')
    parser.add_argument('--token', help='GitHub personal access token (or set GITHUB_TOKEN env var)')
    parser.add_argument('--owner', default='CrazyDubya', help='Repository owner')
    parser.add_argument('--repo', default='research-scrapers', help='Repository name')
    
    # Scraping parameters
    parser.add_argument('--mode', choices=[
        'repository', 'user', 'issues', 'pull_requests', 'organization',
        'search_repos', 'search_users', 'search_code', 'batch_repos', 'comprehensive'
    ], help='Scraping mode')
    parser.add_argument('--target', help='Target (owner/repo, username, org, or search query)')
    
    # Output options
    parser.add_argument('--format', choices=['json', 'csv', 'both'], default='json',
                       help='Output format (default: json)')
    
    # Data inclusion options
    parser.add_argument('--include-commits', action='store_true',
                       help='Include commit history (large datasets)')
    parser.add_argument('--include-issues', action='store_true',
                       help='Include issues data')
    parser.add_argument('--include-prs', action='store_true',
                       help='Include pull requests data')
    
    # Execution options
    parser.add_argument('--max-items', type=int, default=100,
                       help='Maximum items to fetch (default: 100)')
    parser.add_argument('--parallel', action='store_true', default=True,
                       help='Enable parallel execution (default: True)')
    parser.add_argument('--no-parallel', action='store_false', dest='parallel',
                       help='Disable parallel execution')
    
    # Notification options
    parser.add_argument('--email', help='Email address for notifications')
    parser.add_argument('--slack-webhook', help='Slack webhook URL for notifications')
    
    # Other options
    parser.add_argument('--retention-days', type=int, default=30,
                       help='Artifact retention period in days (default: 30)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    parser.add_argument('--event-type', default='scrape-github-api',
                       choices=['scrape-github-api', 'poke-trigger'],
                       help='Event type for trigger (default: scrape-github-api)')
    
    args = parser.parse_args()
    
    try:
        # Handle utility actions
        if args.create_config:
            create_sample_config()
            return 0
        
        # Initialize trigger
        trigger = WorkflowTrigger(
            token=args.token,
            owner=args.owner,
            repo=args.repo
        )
        
        if args.check_status:
            trigger.check_workflow_status()
            return 0
        
        # Trigger workflow
        if args.config:
            result = trigger.trigger_from_config(args.config)
        elif args.mode and args.target:
            result = trigger.trigger_workflow(
                scraper_mode=args.mode,
                target=args.target,
                output_format=args.format,
                include_commits=args.include_commits,
                include_issues=args.include_issues,
                include_pull_requests=args.include_prs,
                max_items=args.max_items,
                parallel_execution=args.parallel,
                notification_email=args.email,
                slack_webhook=args.slack_webhook,
                artifact_retention_days=args.retention_days,
                debug_mode=args.debug,
                event_type=args.event_type
            )
        else:
            parser.error("Either --config or both --mode and --target are required")
        
        return 0 if result.get('success') else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Cancelled by user")
        return 130
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
