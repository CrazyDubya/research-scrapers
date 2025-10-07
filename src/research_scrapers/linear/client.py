"""
Production-Ready Linear API Client

A comprehensive Linear API client designed for the research-scrapers package.
This client provides robust GraphQL operations, error handling, rate limiting,
and integration with all existing scrapers (GitHub, ArXiv, Stack Overflow, Patent).

Features:
- GraphQL query execution with retry logic
- Issue creation and management
- Comment creation and updates
- Workflow state management
- Comprehensive error handling
- Rate limiting with exponential backoff
- Authentication management
- Result formatting for all scraper types
- Automatic task creation from scraper results

Author: Stephen Thompson
"""

import os
import json
import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import urllib.request
import urllib.error
import urllib.parse
from functools import wraps

# Import from the root utils and config
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from utils import (
    RateLimiter,
    APIResponseProcessor,
    DataFormatter,
    DataValidator,
    FileManager,
    setup_logging,
    handle_api_errors,
    exponential_backoff,
    APIError,
    RateLimitError,
    ValidationError,
    get_timestamp
)

logger = logging.getLogger(__name__)


class LinearError(APIError):
    """Base exception for Linear API errors."""
    pass


class LinearRateLimitError(LinearError, RateLimitError):
    """Exception raised when Linear API rate limit is exceeded."""
    pass


class LinearAuthError(LinearError):
    """Exception raised for Linear authentication errors."""
    pass


class LinearValidationError(LinearError, ValidationError):
    """Exception raised for Linear data validation errors."""
    pass


class IssueState(Enum):
    """Linear issue states."""
    BACKLOG = "Backlog"
    TODO = "Todo"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    DONE = "Done"
    CANCELED = "Canceled"


class IssuePriority(Enum):
    """Linear issue priorities."""
    NO_PRIORITY = 0
    URGENT = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class LinearTeam:
    """Linear team information."""
    id: str
    name: str
    key: str


@dataclass
class LinearWorkflowState:
    """Linear workflow state information."""
    id: str
    name: str
    type: str
    position: float


@dataclass
class LinearIssue:
    """Linear issue information."""
    id: str
    identifier: str
    title: str
    description: Optional[str]
    state: LinearWorkflowState
    team: LinearTeam
    priority: int
    created_at: datetime
    updated_at: datetime
    url: str


class ScraperType(Enum):
    """Supported scraper types."""
    GITHUB_REPO = "github_repo"
    GITHUB_ISSUE = "github_issue"
    GITHUB_USER = "github_user"
    ARXIV = "arxiv"
    STACKOVERFLOW = "stackoverflow"
    PATENT = "patent"


def retry_on_rate_limit(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator to retry Linear API calls on rate limit errors.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries (exponential backoff)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except LinearRateLimitError as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                    else:
                        logger.error(f"Max retries ({max_retries}) exceeded for rate limit")
                        raise
                except Exception as e:
                    # Don't retry on non-rate-limit errors
                    raise
            
            raise last_exception
        return wrapper
    return decorator


class LinearClient:
    """
    Production-ready Linear API client with comprehensive error handling and rate limiting.
    
    This client provides a robust interface to Linear's GraphQL API, designed specifically
    for integration with the research-scrapers package. It handles authentication,
    rate limiting, error recovery, and automatic task creation from scraper results.
    
    Examples:
        >>> client = LinearClient(api_key="lin_api_xxx")
        >>> issue = client.create_issue_from_scraper_results(
        ...     team_key="RES",
        ...     scraper_results={"github_repo": {...}},
        ...     run_id="12345"
        ... )
        >>> client.add_comment(issue.id, "Additional findings...")
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.linear.app/graphql",
        rate_limit: float = 50.0,  # Linear allows 50 requests per second
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize Linear API client.
        
        Args:
            api_key: Linear API key (if not provided, uses LINEAR_API_KEY env var)
            base_url: Linear GraphQL API base URL
            rate_limit: Rate limit in requests per second
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            
        Raises:
            LinearAuthError: If API key is not provided or invalid
        """
        self.api_key = api_key or os.environ.get('LINEAR_API_KEY')
        if not self.api_key:
            raise LinearAuthError("Linear API key is required. Set LINEAR_API_KEY environment variable or pass api_key parameter.")
        
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Setup headers
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": self.api_key,
            "User-Agent": "research-scrapers/1.0"
        }
        
        # Rate limiting
        self.rate_limiter = RateLimiter(rate_limit)
        
        # Response processor
        self.response_processor = APIResponseProcessor()
        
        # Data validator
        self.validator = DataValidator()
        
        # Cache for teams and workflow states
        self._teams_cache: Dict[str, LinearTeam] = {}
        self._states_cache: Dict[str, List[LinearWorkflowState]] = {}
        
        logger.info(f"LinearClient initialized with rate limit: {rate_limit} req/s")
        
        # Validate connection
        self._validate_connection()
    
    def _validate_connection(self) -> None:
        """
        Validate the API connection and authentication.
        
        Raises:
            LinearAuthError: If authentication fails
            LinearError: If connection fails
        """
        try:
            query = """
            query {
              viewer {
                id
                name
                email
              }
            }
            """
            result = self.execute_query(query)
            viewer = result.get('viewer')
            if not viewer:
                raise LinearAuthError("Failed to authenticate with Linear API")
            
            logger.info(f"Connected to Linear as: {viewer.get('name', 'Unknown')} ({viewer.get('email', 'No email')})")
            
        except Exception as e:
            if isinstance(e, LinearAuthError):
                raise
            raise LinearError(f"Failed to validate Linear connection: {e}")
    
    @retry_on_rate_limit(max_retries=3, base_delay=1.0)
    def execute_query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query against Linear API with rate limiting and error handling.
        
        Args:
            query: GraphQL query string
            variables: Optional query variables
            operation_name: Optional operation name for debugging
            
        Returns:
            API response data
            
        Raises:
            LinearError: If query execution fails
            LinearRateLimitError: If rate limit is exceeded
            LinearAuthError: If authentication fails
        """
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        if operation_name:
            payload["operationName"] = operation_name
        
        data = json.dumps(payload).encode('utf-8')
        
        @self.rate_limiter
        def _execute():
            req = urllib.request.Request(
                self.base_url,
                data=data,
                headers=self.headers
            )
            
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    
                    # Check for GraphQL errors
                    if 'errors' in result:
                        errors = result['errors']
                        error_messages = [error.get('message', 'Unknown error') for error in errors]
                        
                        # Check for specific error types
                        for error in errors:
                            extensions = error.get('extensions', {})
                            error_code = extensions.get('code')
                            
                            if error_code == 'RATE_LIMITED':
                                raise LinearRateLimitError(f"Rate limit exceeded: {error.get('message')}")
                            elif error_code == 'UNAUTHENTICATED':
                                raise LinearAuthError(f"Authentication failed: {error.get('message')}")
                        
                        raise LinearError(f"GraphQL errors: {'; '.join(error_messages)}")
                    
                    return result.get('data', {})
            
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                
                if e.code == 401:
                    raise LinearAuthError(f"Authentication failed: {error_body}")
                elif e.code == 429:
                    raise LinearRateLimitError(f"Rate limit exceeded: {error_body}")
                else:
                    raise LinearError(f"HTTP {e.code}: {error_body}")
            
            except urllib.error.URLError as e:
                raise LinearError(f"URL error: {e.reason}")
            except json.JSONDecodeError as e:
                raise LinearError(f"Invalid JSON response: {e}")
        
        return _execute()
    
    def get_teams(self, refresh_cache: bool = False) -> List[LinearTeam]:
        """
        Get all teams accessible to the authenticated user.
        
        Args:
            refresh_cache: Whether to refresh the cached teams
            
        Returns:
            List of LinearTeam objects
            
        Raises:
            LinearError: If request fails
        """
        if not refresh_cache and self._teams_cache:
            return list(self._teams_cache.values())
        
        query = """
        query GetTeams {
          teams {
            nodes {
              id
              name
              key
            }
          }
        }
        """
        
        result = self.execute_query(query)
        teams_data = result.get('teams', {}).get('nodes', [])
        
        teams = []
        for team_data in teams_data:
            team = LinearTeam(
                id=team_data['id'],
                name=team_data['name'],
                key=team_data['key']
            )
            teams.append(team)
            self._teams_cache[team.key] = team
        
        logger.info(f"Retrieved {len(teams)} teams")
        return teams
    
    def get_team_by_key(self, team_key: str) -> Optional[LinearTeam]:
        """
        Get a team by its key.
        
        Args:
            team_key: Team key (e.g., "RES", "ENG")
            
        Returns:
            LinearTeam object or None if not found
        """
        if team_key in self._teams_cache:
            return self._teams_cache[team_key]
        
        # Refresh cache and try again
        teams = self.get_teams(refresh_cache=True)
        return self._teams_cache.get(team_key)
    
    def get_workflow_states(self, team_id: str, refresh_cache: bool = False) -> List[LinearWorkflowState]:
        """
        Get workflow states for a team.
        
        Args:
            team_id: Linear team ID
            refresh_cache: Whether to refresh the cached states
            
        Returns:
            List of LinearWorkflowState objects
            
        Raises:
            LinearError: If request fails
        """
        if not refresh_cache and team_id in self._states_cache:
            return self._states_cache[team_id]
        
        query = """
        query GetWorkflowStates($teamId: String!) {
          team(id: $teamId) {
            states {
              nodes {
                id
                name
                type
                position
              }
            }
          }
        }
        """
        
        variables = {"teamId": team_id}
        result = self.execute_query(query, variables)
        
        team_data = result.get('team')
        if not team_data:
            raise LinearError(f"Team with ID {team_id} not found")
        
        states_data = team_data.get('states', {}).get('nodes', [])
        
        states = []
        for state_data in states_data:
            state = LinearWorkflowState(
                id=state_data['id'],
                name=state_data['name'],
                type=state_data['type'],
                position=state_data['position']
            )
            states.append(state)
        
        self._states_cache[team_id] = states
        logger.info(f"Retrieved {len(states)} workflow states for team {team_id}")
        return states
    
    def get_state_by_name(self, team_id: str, state_name: str) -> Optional[LinearWorkflowState]:
        """
        Get a workflow state by name for a specific team.
        
        Args:
            team_id: Linear team ID
            state_name: State name (case-insensitive)
            
        Returns:
            LinearWorkflowState object or None if not found
        """
        states = self.get_workflow_states(team_id)
        
        for state in states:
            if state.name.lower() == state_name.lower():
                return state
        
        return None
    
    def get_issue(self, issue_id: str) -> LinearIssue:
        """
        Get issue details by ID.
        
        Args:
            issue_id: Linear issue ID
            
        Returns:
            LinearIssue object
            
        Raises:
            LinearError: If issue not found or request fails
        """
        query = """
        query GetIssue($id: String!) {
          issue(id: $id) {
            id
            identifier
            title
            description
            priority
            createdAt
            updatedAt
            url
            state {
              id
              name
              type
              position
            }
            team {
              id
              name
              key
            }
          }
        }
        """
        
        variables = {"id": issue_id}
        result = self.execute_query(query, variables)
        
        issue_data = result.get('issue')
        if not issue_data:
            raise LinearError(f"Issue with ID {issue_id} not found")
        
        return self._parse_issue_data(issue_data)
    
    def _parse_issue_data(self, issue_data: Dict[str, Any]) -> LinearIssue:
        """Parse issue data from API response into LinearIssue object."""
        state_data = issue_data['state']
        team_data = issue_data['team']
        
        state = LinearWorkflowState(
            id=state_data['id'],
            name=state_data['name'],
            type=state_data['type'],
            position=state_data['position']
        )
        
        team = LinearTeam(
            id=team_data['id'],
            name=team_data['name'],
            key=team_data['key']
        )
        
        return LinearIssue(
            id=issue_data['id'],
            identifier=issue_data['identifier'],
            title=issue_data['title'],
            description=issue_data.get('description'),
            state=state,
            team=team,
            priority=issue_data['priority'],
            created_at=datetime.fromisoformat(issue_data['createdAt'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(issue_data['updatedAt'].replace('Z', '+00:00')),
            url=issue_data['url']
        )
    
    def create_issue(
        self,
        team_id: str,
        title: str,
        description: Optional[str] = None,
        priority: int = IssuePriority.MEDIUM.value,
        state_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> LinearIssue:
        """
        Create a new issue in Linear.
        
        Args:
            team_id: Linear team ID
            title: Issue title
            description: Issue description (supports markdown)
            priority: Issue priority (0=No Priority, 1=Urgent, 2=High, 3=Medium, 4=Low)
            state_id: Optional workflow state ID
            assignee_id: Optional assignee user ID
            labels: Optional list of label names
            
        Returns:
            Created LinearIssue object
            
        Raises:
            LinearError: If issue creation fails
        """
        input_data = {
            "teamId": team_id,
            "title": title,
            "priority": priority
        }
        
        if description:
            input_data["description"] = description
        
        if state_id:
            input_data["stateId"] = state_id
        
        if assignee_id:
            input_data["assigneeId"] = assignee_id
        
        if labels:
            input_data["labelIds"] = labels  # Note: This expects label IDs, not names
        
        query = """
        mutation CreateIssue($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            success
            issue {
              id
              identifier
              title
              description
              priority
              createdAt
              updatedAt
              url
              state {
                id
                name
                type
                position
              }
              team {
                id
                name
                key
              }
            }
          }
        }
        """
        
        variables = {"input": input_data}
        result = self.execute_query(query, variables)
        
        create_result = result.get('issueCreate', {})
        if not create_result.get('success'):
            raise LinearError("Failed to create issue")
        
        issue_data = create_result.get('issue')
        if not issue_data:
            raise LinearError("Issue created but no data returned")
        
        issue = self._parse_issue_data(issue_data)
        logger.info(f"Created issue: {issue.identifier} - {issue.title}")
        return issue
    
    def update_issue(
        self,
        issue_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        state_id: Optional[str] = None,
        priority: Optional[int] = None,
        assignee_id: Optional[str] = None
    ) -> LinearIssue:
        """
        Update an existing issue.
        
        Args:
            issue_id: Linear issue ID
            title: New title
            description: New description
            state_id: New workflow state ID
            priority: New priority
            assignee_id: New assignee user ID
            
        Returns:
            Updated LinearIssue object
            
        Raises:
            LinearError: If update fails
        """
        input_data = {}
        
        if title is not None:
            input_data["title"] = title
        
        if description is not None:
            input_data["description"] = description
        
        if state_id is not None:
            input_data["stateId"] = state_id
        
        if priority is not None:
            input_data["priority"] = priority
        
        if assignee_id is not None:
            input_data["assigneeId"] = assignee_id
        
        if not input_data:
            # Nothing to update, return current issue
            return self.get_issue(issue_id)
        
        query = """
        mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
          issueUpdate(id: $id, input: $input) {
            success
            issue {
              id
              identifier
              title
              description
              priority
              createdAt
              updatedAt
              url
              state {
                id
                name
                type
                position
              }
              team {
                id
                name
                key
              }
            }
          }
        }
        """
        
        variables = {
            "id": issue_id,
            "input": input_data
        }
        
        result = self.execute_query(query, variables)
        
        update_result = result.get('issueUpdate', {})
        if not update_result.get('success'):
            raise LinearError(f"Failed to update issue {issue_id}")
        
        issue_data = update_result.get('issue')
        if not issue_data:
            raise LinearError("Issue updated but no data returned")
        
        issue = self._parse_issue_data(issue_data)
        logger.info(f"Updated issue: {issue.identifier}")
        return issue
    
    def add_comment(self, issue_id: str, body: str) -> str:
        """
        Add a comment to a Linear issue.
        
        Args:
            issue_id: Linear issue ID
            body: Comment body (supports markdown)
            
        Returns:
            Comment ID
            
        Raises:
            LinearError: If comment creation fails
        """
        query = """
        mutation CreateComment($input: CommentCreateInput!) {
          commentCreate(input: $input) {
            success
            comment {
              id
              body
              createdAt
            }
          }
        }
        """
        
        variables = {
            "input": {
                "issueId": issue_id,
                "body": body
            }
        }
        
        result = self.execute_query(query, variables)
        
        create_result = result.get('commentCreate', {})
        if not create_result.get('success'):
            raise LinearError(f"Failed to create comment for issue {issue_id}")
        
        comment_data = create_result.get('comment')
        if not comment_data:
            raise LinearError("Comment created but no data returned")
        
        comment_id = comment_data['id']
        logger.info(f"Added comment to issue {issue_id}: {comment_id}")
        return comment_id
    
    def format_scraper_results_for_linear(
        self,
        scraper_results: Dict[str, Any],
        run_id: str,
        workflow_url: Optional[str] = None
    ) -> str:
        """
        Format scraper results as markdown for Linear comments.
        
        Args:
            scraper_results: Dictionary of scraper results by type
            run_id: Unique run identifier
            workflow_url: Optional URL to GitHub Actions workflow run
            
        Returns:
            Formatted markdown string
        """
        markdown = f"# 🔬 Research Scraper Results\n\n"
        markdown += f"**Run ID**: `{run_id}`\n"
        markdown += f"**Timestamp**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        
        if workflow_url:
            markdown += f"**Workflow**: [View in GitHub Actions]({workflow_url})\n"
        
        markdown += "\n---\n\n"
        
        if not scraper_results:
            markdown += "⚠️ No results to display. Check workflow logs for details.\n"
            return markdown
        
        for scraper_type, data in scraper_results.items():
            markdown += f"## {scraper_type.replace('_', ' ').title()}\n\n"
            
            # Format based on scraper type
            try:
                scraper_enum = ScraperType(scraper_type)
                if scraper_enum == ScraperType.GITHUB_REPO:
                    markdown += self._format_github_repo_results(data)
                elif scraper_enum == ScraperType.GITHUB_ISSUE:
                    markdown += self._format_github_issue_results(data)
                elif scraper_enum == ScraperType.GITHUB_USER:
                    markdown += self._format_github_user_results(data)
                elif scraper_enum == ScraperType.ARXIV:
                    markdown += self._format_arxiv_results(data)
                elif scraper_enum == ScraperType.STACKOVERFLOW:
                    markdown += self._format_stackoverflow_results(data)
                elif scraper_enum == ScraperType.PATENT:
                    markdown += self._format_patent_results(data)
                else:
                    markdown += self._format_generic_results(data)
            except ValueError:
                # Unknown scraper type, use generic formatting
                markdown += self._format_generic_results(data)
            
            markdown += "\n"
        
        return markdown
    
    def _format_github_repo_results(self, data: Dict[str, Any]) -> str:
        """Format GitHub repository scraper results."""
        if not isinstance(data, dict):
            return self._format_generic_results(data)
        
        md = ""
        
        if 'full_name' in data:
            md += f"**Repository**: [`{data['full_name']}`]({data.get('html_url', '#')})\n"
        elif 'name' in data:
            owner = data.get('owner', {}).get('login', data.get('owner', 'N/A'))
            md += f"**Repository**: `{owner}/{data['name']}`\n"
        
        if 'description' in data and data['description']:
            md += f"**Description**: {data['description']}\n"
        
        if 'stargazers_count' in data:
            md += f"**Stars**: ⭐ {data['stargazers_count']:,}\n"
        
        if 'forks_count' in data:
            md += f"**Forks**: 🍴 {data['forks_count']:,}\n"
        
        if 'language' in data and data['language']:
            md += f"**Language**: {data['language']}\n"
        
        if 'topics' in data and data['topics']:
            topics = ', '.join(f'`{t}`' for t in data['topics'][:10])  # Limit to 10 topics
            md += f"**Topics**: {topics}\n"
        
        if 'license' in data and data['license']:
            license_name = data['license'].get('name', 'Unknown') if isinstance(data['license'], dict) else str(data['license'])
            md += f"**License**: {license_name}\n"
        
        if 'open_issues_count' in data:
            md += f"**Open Issues**: {data['open_issues_count']:,}\n"
        
        return md
    
    def _format_github_issue_results(self, data: Union[List, Dict]) -> str:
        """Format GitHub issue scraper results."""
        if isinstance(data, list):
            md = f"**Total Issues**: {len(data)}\n\n"
            
            # Show top 10 issues
            for i, issue in enumerate(data[:10], 1):
                if isinstance(issue, dict):
                    title = issue.get('title', 'N/A')
                    number = issue.get('number', 'N/A')
                    state = issue.get('state', 'N/A')
                    
                    md += f"{i}. **{title}** (#{number})\n"
                    md += f"   - State: `{state}`\n"
                    
                    if 'labels' in issue and issue['labels']:
                        labels = ', '.join(f"`{l['name']}`" if isinstance(l, dict) else f"`{l}`" for l in issue['labels'][:5])
                        md += f"   - Labels: {labels}\n"
                    
                    if 'user' in issue and isinstance(issue['user'], dict):
                        md += f"   - Author: {issue['user'].get('login', 'N/A')}\n"
            
            if len(data) > 10:
                md += f"\n... and {len(data) - 10} more issues\n"
        
        else:
            md = self._format_generic_results(data)
        
        return md
    
    def _format_github_user_results(self, data: Dict[str, Any]) -> str:
        """Format GitHub user scraper results."""
        if not isinstance(data, dict):
            return self._format_generic_results(data)
        
        md = ""
        
        if 'login' in data:
            md += f"**Username**: [`{data['login']}`]({data.get('html_url', '#')})\n"
        
        if 'name' in data and data['name']:
            md += f"**Name**: {data['name']}\n"
        
        if 'bio' in data and data['bio']:
            md += f"**Bio**: {data['bio']}\n"
        
        if 'company' in data and data['company']:
            md += f"**Company**: {data['company']}\n"
        
        if 'location' in data and data['location']:
            md += f"**Location**: {data['location']}\n"
        
        if 'public_repos' in data:
            md += f"**Public Repos**: {data['public_repos']:,}\n"
        
        if 'followers' in data:
            md += f"**Followers**: {data['followers']:,}\n"
        
        if 'following' in data:
            md += f"**Following**: {data['following']:,}\n"
        
        return md
    
    def _format_arxiv_results(self, data: Union[List, Dict]) -> str:
        """Format ArXiv scraper results."""
        if isinstance(data, list):
            md = f"**Total Papers**: {len(data)}\n\n"
            
            # Show top 10 papers
            for i, paper in enumerate(data[:10], 1):
                if isinstance(paper, dict):
                    title = paper.get('title', 'N/A')
                    authors = paper.get('authors', [])
                    
                    md += f"{i}. **{title}**\n"
                    
                    if authors:
                        author_list = ', '.join(authors[:3])  # Show first 3 authors
                        if len(authors) > 3:
                            author_list += f" et al. ({len(authors)} total)"
                        md += f"   - Authors: {author_list}\n"
                    
                    if 'published' in paper:
                        md += f"   - Published: {paper['published']}\n"
                    
                    if 'categories' in paper and paper['categories']:
                        categories = ', '.join(f"`{c}`" for c in paper['categories'][:3])
                        md += f"   - Categories: {categories}\n"
            
            if len(data) > 10:
                md += f"\n... and {len(data) - 10} more papers\n"
        
        else:
            md = self._format_generic_results(data)
        
        return md
    
    def _format_stackoverflow_results(self, data: Union[List, Dict]) -> str:
        """Format Stack Overflow scraper results."""
        if isinstance(data, list):
            md = f"**Total Questions**: {len(data)}\n\n"
            
            # Show top 10 questions
            for i, question in enumerate(data[:10], 1):
                if isinstance(question, dict):
                    title = question.get('title', 'N/A')
                    score = question.get('score', 0)
                    
                    md += f"{i}. **{title}**\n"
                    md += f"   - Score: {score}\n"
                    
                    if 'tags' in question and question['tags']:
                        tags = ', '.join(f"`{t}`" for t in question['tags'][:5])
                        md += f"   - Tags: {tags}\n"
                    
                    if 'answer_count' in question:
                        md += f"   - Answers: {question['answer_count']}\n"
                    
                    if 'view_count' in question:
                        md += f"   - Views: {question['view_count']:,}\n"
            
            if len(data) > 10:
                md += f"\n... and {len(data) - 10} more questions\n"
        
        else:
            md = self._format_generic_results(data)
        
        return md
    
    def _format_patent_results(self, data: Union[List, Dict]) -> str:
        """Format patent scraper results."""
        if isinstance(data, list):
            md = f"**Total Patents**: {len(data)}\n\n"
            
            # Show top 10 patents
            for i, patent in enumerate(data[:10], 1):
                if isinstance(patent, dict):
                    title = patent.get('title', 'N/A')
                    patent_number = patent.get('patent_number', 'N/A')
                    
                    md += f"{i}. **{title}** ({patent_number})\n"
                    
                    if 'inventors' in patent and patent['inventors']:
                        inventors = ', '.join(patent['inventors'][:3])
                        if len(patent['inventors']) > 3:
                            inventors += f" et al. ({len(patent['inventors'])} total)"
                        md += f"   - Inventors: {inventors}\n"
                    
                    if 'assignee' in patent and patent['assignee']:
                        md += f"   - Assignee: {patent['assignee']}\n"
                    
                    if 'filing_date' in patent:
                        md += f"   - Filed: {patent['filing_date']}\n"
                    
                    if 'grant_date' in patent:
                        md += f"   - Granted: {patent['grant_date']}\n"
            
            if len(data) > 10:
                md += f"\n... and {len(data) - 10} more patents\n"
        
        else:
            md = self._format_generic_results(data)
        
        return md
    
    def _format_generic_results(self, data: Any) -> str:
        """Format generic scraper results as JSON."""
        try:
            json_str = json.dumps(data, indent=2, default=str)
            # Truncate if too long
            if len(json_str) > 1000:
                json_str = json_str[:1000] + "..."
            return f"```json\n{json_str}\n```\n"
        except Exception:
            return f"```\n{str(data)[:1000]}...\n```\n"
    
    def create_issue_from_scraper_results(
        self,
        team_key: str,
        scraper_results: Dict[str, Any],
        run_id: str,
        workflow_url: Optional[str] = None,
        title_prefix: str = "Research Results",
        priority: int = IssuePriority.MEDIUM.value,
        assignee_id: Optional[str] = None
    ) -> LinearIssue:
        """
        Create a Linear issue from scraper results.
        
        Args:
            team_key: Linear team key (e.g., "RES", "ENG")
            scraper_results: Dictionary of scraper results by type
            run_id: Unique run identifier
            workflow_url: Optional URL to GitHub Actions workflow run
            title_prefix: Prefix for the issue title
            priority: Issue priority
            assignee_id: Optional assignee user ID
            
        Returns:
            Created LinearIssue object
            
        Raises:
            LinearError: If team not found or issue creation fails
        """
        # Get team
        team = self.get_team_by_key(team_key)
        if not team:
            raise LinearError(f"Team with key '{team_key}' not found")
        
        # Generate title
        scraper_types = list(scraper_results.keys())
        if scraper_types:
            scrapers_str = ', '.join(scraper_types)
            title = f"{title_prefix}: {scrapers_str} ({run_id})"
        else:
            title = f"{title_prefix}: No Results ({run_id})"
        
        # Format description
        description = self.format_scraper_results_for_linear(
            scraper_results,
            run_id,
            workflow_url
        )
        
        # Create issue
        issue = self.create_issue(
            team_id=team.id,
            title=title,
            description=description,
            priority=priority,
            assignee_id=assignee_id
        )
        
        logger.info(f"Created Linear issue from scraper results: {issue.identifier}")
        return issue
    
    def update_issue_with_results(
        self,
        issue_id: str,
        scraper_results: Dict[str, Any],
        run_id: str,
        workflow_url: Optional[str] = None,
        append_to_description: bool = True
    ) -> LinearIssue:
        """
        Update an existing Linear issue with new scraper results.
        
        Args:
            issue_id: Linear issue ID
            scraper_results: Dictionary of scraper results by type
            run_id: Unique run identifier
            workflow_url: Optional URL to GitHub Actions workflow run
            append_to_description: Whether to append to existing description
            
        Returns:
            Updated LinearIssue object
            
        Raises:
            LinearError: If issue not found or update fails
        """
        # Format new results
        new_content = self.format_scraper_results_for_linear(
            scraper_results,
            run_id,
            workflow_url
        )
        
        if append_to_description:
            # Get current issue to append to description
            current_issue = self.get_issue(issue_id)
            current_description = current_issue.description or ""
            
            description = f"{current_description}\n\n---\n\n{new_content}"
        else:
            description = new_content
        
        # Update issue
        issue = self.update_issue(
            issue_id=issue_id,
            description=description
        )
        
        logger.info(f"Updated Linear issue with scraper results: {issue.identifier}")
        return issue
    
    def close(self) -> None:
        """
        Close the client and cleanup resources.
        """
        # Clear caches
        self._teams_cache.clear()
        self._states_cache.clear()
        
        logger.info("LinearClient closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


# Convenience functions for common operations

def create_linear_client(api_key: Optional[str] = None) -> LinearClient:
    """
    Create a Linear client with default settings.
    
    Args:
        api_key: Optional API key (uses environment variable if not provided)
        
    Returns:
        Configured LinearClient instance
    """
    return LinearClient(api_key=api_key)


def create_issue_from_artifacts(
    artifacts_dir: Path,
    team_key: str,
    run_id: str,
    workflow_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> Optional[LinearIssue]:
    """
    Create a Linear issue from scraper artifacts directory.
    
    Args:
        artifacts_dir: Directory containing scraper artifacts
        team_key: Linear team key
        run_id: Unique run identifier
        workflow_url: Optional workflow URL
        api_key: Optional Linear API key
        
    Returns:
        Created LinearIssue object or None if no artifacts found
        
    Raises:
        LinearError: If issue creation fails
    """
    if not artifacts_dir.exists():
        logger.warning(f"Artifacts directory {artifacts_dir} not found")
        return None
    
    # Load all JSON artifacts
    scraper_results = {}
    for json_file in artifacts_dir.rglob("*.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                scraper_type = json_file.stem.split('_')[0]
                scraper_results[scraper_type] = data
                logger.info(f"Loaded {json_file.name}")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading {json_file.name}: {e}")
    
    if not scraper_results:
        logger.warning("No valid scraper results found")
        return None
    
    # Create Linear issue
    with create_linear_client(api_key) as client:
        issue = client.create_issue_from_scraper_results(
            team_key=team_key,
            scraper_results=scraper_results,
            run_id=run_id,
            workflow_url=workflow_url
        )
    
    return issue