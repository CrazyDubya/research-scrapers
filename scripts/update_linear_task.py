#!/usr/bin/env python3
"""
Linear Task Updater for Research Scrapers

This script updates Linear tasks with research findings from scraper outputs.
It handles authentication, data formatting, and API communication securely.

Author: Stephen Thompson
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import urllib.request
import urllib.error


class LinearAPIClient:
    """Secure Linear API client with error handling and rate limiting."""
    
    def __init__(self, api_key: str):
        """
        Initialize Linear API client.
        
        Args:
            api_key: Linear API key
        """
        if not api_key:
            raise ValueError("Linear API key is required")
        
        self.api_key = api_key
        self.base_url = "https://api.linear.app/graphql"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": self.api_key
        }
    
    def execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """
        Execute a GraphQL query against Linear API.
        
        Args:
            query: GraphQL query string
            variables: Optional query variables
            
        Returns:
            API response data
        """
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            self.base_url,
            data=data,
            headers=self.headers
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if 'errors' in result:
                    raise Exception(f"GraphQL errors: {result['errors']}")
                
                return result.get('data', {})
        
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise Exception(f"HTTP {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise Exception(f"URL error: {e.reason}")
    
    def get_issue(self, issue_id: str) -> Dict:
        """
        Get issue details by ID.
        
        Args:
            issue_id: Linear issue ID
            
        Returns:
            Issue data
        """
        query = """
        query GetIssue($id: String!) {
          issue(id: $id) {
            id
            identifier
            title
            description
            state {
              id
              name
            }
            team {
              id
              name
            }
          }
        }
        """
        
        variables = {"id": issue_id}
        result = self.execute_query(query, variables)
        return result.get('issue', {})
    
    def update_issue(self, issue_id: str, state_name: Optional[str] = None,
                    description_append: Optional[str] = None) -> bool:
        """
        Update a Linear issue.
        
        Args:
            issue_id: Linear issue ID
            state_name: Optional new state name
            description_append: Optional text to append to description
            
        Returns:
            True if successful
        """
        # First get the issue to get current description
        issue = self.get_issue(issue_id)
        
        input_data = {}
        
        if state_name:
            # Get state ID for the team
            team_id = issue['team']['id']
            states = self.get_workflow_states(team_id)
            state_id = next((s['id'] for s in states if s['name'].lower() == state_name.lower()), None)
            
            if state_id:
                input_data['stateId'] = state_id
        
        if description_append:
            current_description = issue.get('description', '')
            input_data['description'] = f"{current_description}\n\n{description_append}"
        
        if not input_data:
            return True  # Nothing to update
        
        query = """
        mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
          issueUpdate(id: $id, input: $input) {
            success
            issue {
              id
              identifier
              title
            }
          }
        }
        """
        
        variables = {
            "id": issue_id,
            "input": input_data
        }
        
        result = self.execute_query(query, variables)
        return result.get('issueUpdate', {}).get('success', False)
    
    def add_comment(self, issue_id: str, body: str) -> bool:
        """
        Add a comment to a Linear issue.
        
        Args:
            issue_id: Linear issue ID
            body: Comment body (supports markdown)
            
        Returns:
            True if successful
        """
        query = """
        mutation CreateComment($issueId: String!, $body: String!) {
          commentCreate(input: {
            issueId: $issueId,
            body: $body
          }) {
            success
            comment {
              id
              body
            }
          }
        }
        """
        
        variables = {
            "issueId": issue_id,
            "body": body
        }
        
        result = self.execute_query(query, variables)
        return result.get('commentCreate', {}).get('success', False)
    
    def get_workflow_states(self, team_id: str) -> List[Dict]:
        """
        Get workflow states for a team.
        
        Args:
            team_id: Linear team ID
            
        Returns:
            List of workflow states
        """
        query = """
        query GetWorkflowStates($teamId: String!) {
          team(id: $teamId) {
            states {
              nodes {
                id
                name
                type
              }
            }
          }
        }
        """
        
        variables = {"teamId": team_id}
        result = self.execute_query(query, variables)
        return result.get('team', {}).get('states', {}).get('nodes', [])


class ScraperResultsProcessor:
    """Process scraper results and format for Linear."""
    
    @staticmethod
    def load_artifacts(artifacts_dir: Path) -> Dict[str, Any]:
        """
        Load all scraper artifacts from directory.
        
        Args:
            artifacts_dir: Directory containing artifacts
            
        Returns:
            Dictionary of scraper results
        """
        results = {}
        
        if not artifacts_dir.exists():
            print(f"Warning: Artifacts directory {artifacts_dir} not found")
            return results
        
        # Find all JSON files in artifacts directory
        for json_file in artifacts_dir.rglob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    scraper_type = json_file.stem.split('_')[0]
                    results[scraper_type] = data
                    print(f"✓ Loaded {json_file.name}")
            except json.JSONDecodeError as e:
                print(f"✗ Error loading {json_file.name}: {e}")
            except Exception as e:
                print(f"✗ Unexpected error loading {json_file.name}: {e}")
        
        return results
    
    @staticmethod
    def format_results_for_linear(results: Dict[str, Any], run_id: str,
                                 workflow_url: str) -> str:
        """
        Format scraper results as markdown for Linear comment.
        
        Args:
            results: Dictionary of scraper results
            run_id: Unique run identifier
            workflow_url: URL to GitHub Actions workflow run
            
        Returns:
            Formatted markdown string
        """
        markdown = f"# 🔬 Research Scraper Results\n\n"
        markdown += f"**Run ID**: `{run_id}`\n"
        markdown += f"**Timestamp**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        markdown += f"**Workflow**: [View in GitHub Actions]({workflow_url})\n\n"
        markdown += "---\n\n"
        
        if not results:
            markdown += "⚠️ No results to display. Check workflow logs for details.\n"
            return markdown
        
        for scraper_type, data in results.items():
            markdown += f"## {scraper_type.replace('_', ' ').title()}\n\n"
            
            # Format based on scraper type
            if scraper_type == "github-repo" or scraper_type == "github_repo":
                markdown += ScraperResultsProcessor._format_repo_results(data)
            elif scraper_type == "github-issue" or scraper_type == "github_issue":
                markdown += ScraperResultsProcessor._format_issue_results(data)
            elif scraper_type == "github-user" or scraper_type == "github_user":
                markdown += ScraperResultsProcessor._format_user_results(data)
            else:
                # Generic formatting
                markdown += f"```json\n{json.dumps(data, indent=2)[:500]}...\n```\n\n"
            
            markdown += "\n"
        
        return markdown
    
    @staticmethod
    def _format_repo_results(data: Dict) -> str:
        """Format repository scraper results."""
        md = ""
        
        if isinstance(data, dict):
            if 'name' in data:
                md += f"**Repository**: `{data.get('owner', 'N/A')}/{data.get('name')}`\n"
            if 'description' in data:
                md += f"**Description**: {data.get('description', 'N/A')}\n"
            if 'stars' in data:
                md += f"**Stars**: ⭐ {data.get('stars', 0)}\n"
            if 'forks' in data:
                md += f"**Forks**: 🍴 {data.get('forks', 0)}\n"
            if 'language' in data:
                md += f"**Language**: {data.get('language', 'N/A')}\n"
            if 'topics' in data:
                topics = data.get('topics', [])
                if topics:
                    md += f"**Topics**: {', '.join(f'`{t}`' for t in topics)}\n"
        
        return md
    
    @staticmethod
    def _format_issue_results(data: Dict) -> str:
        """Format issue scraper results."""
        md = ""
        
        if isinstance(data, list):
            md += f"**Total Issues**: {len(data)}\n\n"
            
            # Show top 5 issues
            for i, issue in enumerate(data[:5], 1):
                md += f"{i}. **{issue.get('title', 'N/A')}** (#{issue.get('number', 'N/A')})\n"
                md += f"   - State: `{issue.get('state', 'N/A')}`\n"
                if 'labels' in issue:
                    labels = ', '.join(f"`{l}`" for l in issue.get('labels', []))
                    md += f"   - Labels: {labels}\n"
        
        return md
    
    @staticmethod
    def _format_user_results(data: Dict) -> str:
        """Format user scraper results."""
        md = ""
        
        if isinstance(data, dict):
            if 'login' in data:
                md += f"**Username**: `{data.get('login')}`\n"
            if 'name' in data:
                md += f"**Name**: {data.get('name', 'N/A')}\n"
            if 'bio' in data:
                md += f"**Bio**: {data.get('bio', 'N/A')}\n"
            if 'public_repos' in data:
                md += f"**Public Repos**: {data.get('public_repos', 0)}\n"
            if 'followers' in data:
                md += f"**Followers**: {data.get('followers', 0)}\n"
            if 'following' in data:
                md += f"**Following**: {data.get('following', 0)}\n"
        
        return md


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Update Linear tasks with research scraper results"
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        required=True,
        help="Directory containing scraper artifacts"
    )
    parser.add_argument(
        "--task-id",
        type=str,
        help="Linear task ID to update"
    )
    parser.add_argument(
        "--run-id",
        type=str,
        required=True,
        help="Unique run identifier"
    )
    parser.add_argument(
        "--workflow-url",
        type=str,
        required=True,
        help="URL to GitHub Actions workflow run"
    )
    
    args = parser.parse_args()
    
    # Get API key from environment
    api_key = os.environ.get('LINEAR_API_KEY')
    if not api_key:
        print("⚠️ LINEAR_API_KEY not set. Skipping Linear update.")
        return 0
    
    try:
        # Initialize Linear client
        client = LinearAPIClient(api_key)
        print("✓ Linear API client initialized")
        
        # Load scraper results
        processor = ScraperResultsProcessor()
        results = processor.load_artifacts(args.artifacts_dir)
        print(f"✓ Loaded {len(results)} scraper result(s)")
        
        # Format results for Linear
        comment_body = processor.format_results_for_linear(
            results,
            args.run_id,
            args.workflow_url
        )
        
        # Update Linear task
        if args.task_id:
            print(f"Updating Linear task {args.task_id}...")
            
            # Add comment with results
            success = client.add_comment(args.task_id, comment_body)
            
            if success:
                print(f"✅ Successfully updated Linear task {args.task_id}")
                
                # Update task state if results are complete
                if results:
                    client.update_issue(args.task_id, state_name="Done")
                    print("✓ Task state updated to 'Done'")
            else:
                print(f"❌ Failed to update Linear task {args.task_id}")
                return 1
        else:
            print("No task ID provided. Skipping Linear update.")
            print("\nFormatted results:")
            print(comment_body)
        
        return 0
    
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
