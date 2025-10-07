"""Integration between Linear and GitHub scrapers for automatic task creation.

This module implements the core functionality for RUB-50: automatically creating
Linear tasks from GitHub scraper results.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..scrapers.github_scraper import GitHubScraper
from ..scrapers.linear_scraper import LinearScraper


logger = logging.getLogger(__name__)


class LinearGitHubIntegration:
    """Integration class for creating Linear tasks from GitHub scraper results."""
    
    def __init__(self, github_scraper: GitHubScraper, linear_scraper: LinearScraper):
        """Initialize the integration.
        
        Args:
            github_scraper: Configured GitHub scraper instance
            linear_scraper: Configured Linear scraper instance
        """
        self.github_scraper = github_scraper
        self.linear_scraper = linear_scraper
        
    def create_tasks_from_issues(self, 
                                repo_owner: str, 
                                repo_name: str, 
                                team_id: str,
                                filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Create Linear tasks from GitHub issues.
        
        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            team_id: Linear team ID to create tasks in
            filters: Optional filters for GitHub issues (labels, state, etc.)
            
        Returns:
            List of created Linear task data
        """
        logger.info(f"Creating Linear tasks from GitHub issues in {repo_owner}/{repo_name}")
        
        # Fetch GitHub issues
        issues = self.github_scraper.get_repository_issues(
            owner=repo_owner,
            repo=repo_name,
            filters=filters or {}
        )
        
        created_tasks = []
        
        for issue in issues:
            try:
                task_data = self._convert_issue_to_task(issue, team_id)
                created_task = self.linear_scraper.create_issue(task_data)
                created_tasks.append(created_task)
                
                logger.info(f"Created Linear task {created_task.get('id')} from GitHub issue #{issue['number']}")
                
            except Exception as e:
                logger.error(f"Failed to create Linear task from GitHub issue #{issue['number']}: {e}")
                continue
                
        return created_tasks
    
    def create_tasks_from_pull_requests(self,
                                       repo_owner: str,
                                       repo_name: str,
                                       team_id: str,
                                       filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Create Linear tasks from GitHub pull requests.
        
        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            team_id: Linear team ID to create tasks in
            filters: Optional filters for GitHub PRs (state, labels, etc.)
            
        Returns:
            List of created Linear task data
        """
        logger.info(f"Creating Linear tasks from GitHub PRs in {repo_owner}/{repo_name}")
        
        # Fetch GitHub pull requests
        pull_requests = self.github_scraper.get_repository_pull_requests(
            owner=repo_owner,
            repo=repo_name,
            filters=filters or {}
        )
        
        created_tasks = []
        
        for pr in pull_requests:
            try:
                task_data = self._convert_pr_to_task(pr, team_id)
                created_task = self.linear_scraper.create_issue(task_data)
                created_tasks.append(created_task)
                
                logger.info(f"Created Linear task {created_task.get('id')} from GitHub PR #{pr['number']}")
                
            except Exception as e:
                logger.error(f"Failed to create Linear task from GitHub PR #{pr['number']}: {e}")
                continue
                
        return created_tasks
    
    def sync_repository_activity(self,
                                repo_owner: str,
                                repo_name: str,
                                team_id: str,
                                sync_config: Optional[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Sync all repository activity to Linear tasks.
        
        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            team_id: Linear team ID to create tasks in
            sync_config: Configuration for what to sync (issues, PRs, etc.)
            
        Returns:
            Dictionary with 'issues' and 'pull_requests' keys containing created tasks
        """
        config = sync_config or {
            'sync_issues': True,
            'sync_pull_requests': True,
            'issue_filters': {'state': 'open'},
            'pr_filters': {'state': 'open'}
        }
        
        results = {
            'issues': [],
            'pull_requests': []
        }
        
        if config.get('sync_issues', True):
            results['issues'] = self.create_tasks_from_issues(
                repo_owner=repo_owner,
                repo_name=repo_name,
                team_id=team_id,
                filters=config.get('issue_filters')
            )
            
        if config.get('sync_pull_requests', True):
            results['pull_requests'] = self.create_tasks_from_pull_requests(
                repo_owner=repo_owner,
                repo_name=repo_name,
                team_id=team_id,
                filters=config.get('pr_filters')
            )
            
        return results
    
    def _convert_issue_to_task(self, issue: Dict[str, Any], team_id: str) -> Dict[str, Any]:
        """Convert a GitHub issue to Linear task format.
        
        Args:
            issue: GitHub issue data
            team_id: Linear team ID
            
        Returns:
            Linear task data dictionary
        """
        # Extract labels and convert to Linear format
        labels = [label['name'] for label in issue.get('labels', [])]
        
        # Determine priority based on labels
        priority = self._determine_priority_from_labels(labels)
        
        # Create task description with GitHub context
        description = f"""**GitHub Issue**: {issue['html_url']}
**Repository**: {issue['repository_url'].split('/')[-2:]}
**Author**: {issue['user']['login']}
**Created**: {issue['created_at']}

---

{issue.get('body', '')}
"""
        
        return {
            'title': f"[GitHub] {issue['title']}",
            'description': description,
            'teamId': team_id,
            'priority': priority,
            'labels': labels,
            'externalId': f"github-issue-{issue['id']}",
            'url': issue['html_url']
        }
    
    def _convert_pr_to_task(self, pr: Dict[str, Any], team_id: str) -> Dict[str, Any]:
        """Convert a GitHub pull request to Linear task format.
        
        Args:
            pr: GitHub pull request data
            team_id: Linear team ID
            
        Returns:
            Linear task data dictionary
        """
        # Extract labels and convert to Linear format
        labels = [label['name'] for label in pr.get('labels', [])]
        labels.append('pull-request')  # Add PR-specific label
        
        # Determine priority based on labels
        priority = self._determine_priority_from_labels(labels)
        
        # Create task description with GitHub context
        description = f"""**GitHub Pull Request**: {pr['html_url']}
**Repository**: {pr['base']['repo']['full_name']}
**Author**: {pr['user']['login']}
**Branch**: {pr['head']['ref']} → {pr['base']['ref']}
**Created**: {pr['created_at']}
**Status**: {pr['state']}

---

{pr.get('body', '')}
"""
        
        return {
            'title': f"[GitHub PR] {pr['title']}",
            'description': description,
            'teamId': team_id,
            'priority': priority,
            'labels': labels,
            'externalId': f"github-pr-{pr['id']}",
            'url': pr['html_url']
        }
    
    def _determine_priority_from_labels(self, labels: List[str]) -> int:
        """Determine Linear priority from GitHub labels.
        
        Args:
            labels: List of GitHub label names
            
        Returns:
            Linear priority value (1=Urgent, 2=High, 3=Medium, 4=Low)
        """
        # Priority mapping based on common GitHub labels
        priority_map = {
            'critical': 1,
            'urgent': 1,
            'high': 2,
            'high priority': 2,
            'medium': 3,
            'low': 4,
            'low priority': 4
        }
        
        # Check labels for priority indicators
        for label in labels:
            label_lower = label.lower()
            for priority_label, priority_value in priority_map.items():
                if priority_label in label_lower:
                    return priority_value
        
        # Default to medium priority
        return 3
