"""
Comprehensive GitHub Scraper

A production-ready GitHub scraper that provides unified access to GitHub's REST API
for repositories, users, organizations, issues, pull requests, and search operations.

This module builds on the existing utility functions (RateLimiter, APIResponseProcessor, 
DataFormatter, FileManager) and follows the architecture patterns of the research-scrapers package.

Features:
- Repository metadata and statistics
- User profile and activity information
- Organization data and repositories
- Issues and pull requests
- Advanced search capabilities (repos, users, code)
- Automatic pagination handling
- Rate limiting with exponential backoff
- Comprehensive error handling
- Optional caching support

Author: Stephen Thompson
"""

import os
import logging
import time
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

import requests

# Import from the root utils and config (not src/)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import (
    RateLimiter,
    APIResponseProcessor,
    DataFormatter,
    DataValidator,
    FileManager,
    setup_logging,
    handle_api_errors,
    exponential_backoff,
    create_session,
    APIError,
    RateLimitError,
    ValidationError,
    get_timestamp
)

from config import (
    GITHUB_API_BASE_URL,
    DEFAULT_RATE_LIMIT,
    AUTHENTICATED_RATE_LIMIT,
    DEFAULT_TIMEOUT,
    DEFAULT_PER_PAGE,
    MAX_PER_PAGE,
    get_github_token,
    get_rate_limit
)


logger = logging.getLogger(__name__)


class GitHubScraper:
    """
    Comprehensive GitHub scraper using the GitHub REST API.
    
    This class provides methods to scrape various GitHub resources including
    repositories, users, organizations, issues, pull requests, and search results.
    It handles authentication, rate limiting, pagination, and error handling automatically.
    
    Examples:
        >>> scraper = GitHubScraper(token="ghp_xxx")
        >>> repo_data = scraper.scrape_repository("facebook", "react")
        >>> user_data = scraper.scrape_user("torvalds")
        >>> results = scraper.search_repositories("machine learning", limit=50)
    """
    
    def __init__(self, token: Optional[str] = None, enable_caching: bool = False):
        """
        Initialize the GitHub scraper.
        
        Args:
            token: GitHub personal access token. If not provided, uses GITHUB_TOKEN env var.
            enable_caching: Whether to enable response caching (default: False)
            
        Raises:
            APIError: If session setup fails
        """
        self.token = token or get_github_token()
        self.base_url = GITHUB_API_BASE_URL
        self.enable_caching = enable_caching
        
        # Create session with retry logic
        self.session = create_session()
        
        # Setup authentication and headers
        if self.token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'research-scrapers/1.0'
            })
            rate_limit = AUTHENTICATED_RATE_LIMIT
        else:
            self.session.headers.update({
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'research-scrapers/1.0'
            })
            rate_limit = DEFAULT_RATE_LIMIT
        
        # Rate limiting
        self.rate_limiter = RateLimiter(rate_limit)
        
        # Response processor
        self.response_processor = APIResponseProcessor()
        
        # Data validator
        self.validator = DataValidator()
        
        # Cache directory
        if self.enable_caching:
            self.cache_dir = Path('.cache/github')
            FileManager.ensure_directory(self.cache_dir)
        
        logger.info(
            f"GitHubScraper initialized with "
            f"{'authenticated' if self.token else 'unauthenticated'} access "
            f"(rate limit: {rate_limit} req/s)"
        )
    
    @exponential_backoff(max_retries=3, base_delay=1.0)
    @handle_api_errors
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = 'GET'
    ) -> requests.Response:
        """
        Make a rate-limited API request to GitHub.
        
        Args:
            endpoint: API endpoint (e.g., '/repos/owner/repo')
            params: Query parameters
            method: HTTP method (default: GET)
            
        Returns:
            Response object
            
        Raises:
            APIError: If request fails
            RateLimitError: If rate limit is exceeded
        """
        url = f"{self.base_url}{endpoint}" if not endpoint.startswith('http') else endpoint
        
        # Apply rate limiting
        @self.rate_limiter
        def _request():
            logger.debug(f"Making {method} request to: {url}")
            response = self.session.request(method, url, params=params, timeout=DEFAULT_TIMEOUT)
            
            # Check rate limit
            rate_info = self.response_processor.get_rate_limit_info(response)
            if rate_info['remaining'] < 10:
                logger.warning(
                    f"Rate limit low: {rate_info['remaining']}/{rate_info['limit']} remaining, "
                    f"resets at {rate_info['reset']}"
                )
            
            if rate_info['remaining'] == 0:
                reset_time = rate_info['reset']
                wait_time = max(0, reset_time - time.time())
                raise RateLimitError(
                    f"Rate limit exceeded. Resets in {wait_time:.0f} seconds"
                )
            
            return response
        
        return _request()
    
    def _paginate(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        max_pages: Optional[int] = None,
        per_page: int = DEFAULT_PER_PAGE
    ) -> List[Dict[str, Any]]:
        """
        Handle pagination for list endpoints using Link headers.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            max_pages: Maximum number of pages to fetch (None = all)
            per_page: Results per page (max 100)
            
        Returns:
            List of all collected items
            
        Raises:
            APIError: If pagination fails
        """
        all_items = []
        page = 1
        
        if params is None:
            params = {}
        
        params['per_page'] = min(per_page, MAX_PER_PAGE)
        
        while True:
            if max_pages and page > max_pages:
                break
            
            params['page'] = page
            response = self._make_request(endpoint, params)
            data = self.response_processor.validate_response(response)
            
            if not data:
                break
            
            # Handle both list and dict responses
            if isinstance(data, list):
                all_items.extend(data)
                if len(data) < params['per_page']:
                    break
            elif isinstance(data, dict):
                # For search endpoints
                items = data.get('items', [])
                all_items.extend(items)
                if len(items) < params['per_page']:
                    break
            else:
                break
            
            # Check for Link header pagination
            pagination = self.response_processor.extract_pagination_info(response)
            if not pagination.get('next'):
                break
            
            page += 1
            logger.debug(f"Fetching page {page}")
        
        logger.info(f"Collected {len(all_items)} items from {page} pages")
        return all_items
    
    def scrape_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Scrape comprehensive repository metadata and statistics.
        
        Args:
            owner: Repository owner (username or organization)
            repo: Repository name
            
        Returns:
            Dictionary containing repository data including:
            - Basic metadata (name, description, owner)
            - Statistics (stars, forks, watchers, issues)
            - Timestamps (created, updated, pushed)
            - Additional info (language, topics, license)
            
        Raises:
            APIError: If repository not found or request fails
            ValidationError: If response data is invalid
            
        Examples:
            >>> scraper = GitHubScraper()
            >>> repo = scraper.scrape_repository("facebook", "react")
            >>> print(f"Stars: {repo['stargazers_count']}")
        """
        endpoint = f"/repos/{owner}/{repo}"
        response = self._make_request(endpoint)
        data = self.response_processor.validate_response(response)
        
        # Validate repository data
        if not self.validator.validate_github_repo(data):
            raise ValidationError(f"Invalid repository data for {owner}/{repo}")
        
        logger.info(f"Scraped repository: {owner}/{repo}")
        return data
    
    def scrape_user(self, username: str) -> Dict[str, Any]:
        """
        Scrape user profile and activity information.
        
        Args:
            username: GitHub username
            
        Returns:
            Dictionary containing user data including:
            - Profile information (name, bio, location, email)
            - Statistics (followers, following, public repos)
            - Account info (created date, type, company)
            - URLs (blog, avatar, profile)
            
        Raises:
            APIError: If user not found or request fails
            
        Examples:
            >>> scraper = GitHubScraper()
            >>> user = scraper.scrape_user("torvalds")
            >>> print(f"Followers: {user['followers']}")
        """
        endpoint = f"/users/{username}"
        response = self._make_request(endpoint)
        data = self.response_processor.validate_response(response)
        
        logger.info(f"Scraped user: {username}")
        return data
    
    def scrape_organization(self, org_name: str) -> Dict[str, Any]:
        """
        Scrape organization information and repository list.
        
        Args:
            org_name: GitHub organization name
            
        Returns:
            Dictionary containing organization data including:
            - Basic info (name, description, location)
            - Statistics (public repos, followers)
            - Account details (created date, type, email)
            - Repositories list
            
        Raises:
            APIError: If organization not found or request fails
            
        Examples:
            >>> scraper = GitHubScraper()
            >>> org = scraper.scrape_organization("microsoft")
            >>> print(f"Public repos: {org['public_repos']}")
        """
        # Get organization details
        endpoint = f"/orgs/{org_name}"
        response = self._make_request(endpoint)
        org_data = self.response_processor.validate_response(response)
        
        # Get organization repositories
        repos_endpoint = f"/orgs/{org_name}/repos"
        org_data['repositories'] = self._paginate(repos_endpoint, params={'type': 'public'})
        
        logger.info(f"Scraped organization: {org_name} ({len(org_data['repositories'])} repos)")
        return org_data
    
    def scrape_issues(
        self,
        owner: str,
        repo: str,
        state: str = 'all',
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Scrape issues from a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state filter - 'open', 'closed', or 'all' (default: 'all')
            limit: Maximum number of issues to retrieve (default: 100)
            
        Returns:
            List of issue dictionaries containing:
            - Issue details (number, title, body, state)
            - Author information
            - Labels, assignees, milestone
            - Comments count and timestamps
            
        Raises:
            APIError: If request fails
            ValidationError: If state parameter is invalid
            
        Examples:
            >>> scraper = GitHubScraper()
            >>> issues = scraper.scrape_issues("facebook", "react", state="open", limit=50)
            >>> print(f"Found {len(issues)} open issues")
        """
        if state not in ['open', 'closed', 'all']:
            raise ValidationError(f"Invalid state '{state}'. Must be 'open', 'closed', or 'all'")
        
        endpoint = f"/repos/{owner}/{repo}/issues"
        params = {'state': state, 'sort': 'created', 'direction': 'desc'}
        
        max_pages = (limit + DEFAULT_PER_PAGE - 1) // DEFAULT_PER_PAGE
        issues = self._paginate(endpoint, params=params, max_pages=max_pages)
        
        # Limit to requested number
        issues = issues[:limit]
        
        logger.info(f"Scraped {len(issues)} issues from {owner}/{repo}")
        return issues
    
    def scrape_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = 'all',
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Scrape pull requests from a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state filter - 'open', 'closed', or 'all' (default: 'all')
            limit: Maximum number of PRs to retrieve (default: 100)
            
        Returns:
            List of pull request dictionaries containing:
            - PR details (number, title, body, state)
            - Author and reviewers
            - Labels, assignees, milestone
            - Merge status and timestamps
            
        Raises:
            APIError: If request fails
            ValidationError: If state parameter is invalid
            
        Examples:
            >>> scraper = GitHubScraper()
            >>> prs = scraper.scrape_pull_requests("microsoft", "vscode", state="open")
            >>> print(f"Found {len(prs)} open pull requests")
        """
        if state not in ['open', 'closed', 'all']:
            raise ValidationError(f"Invalid state '{state}'. Must be 'open', 'closed', or 'all'")
        
        endpoint = f"/repos/{owner}/{repo}/pulls"
        params = {'state': state, 'sort': 'created', 'direction': 'desc'}
        
        max_pages = (limit + DEFAULT_PER_PAGE - 1) // DEFAULT_PER_PAGE
        prs = self._paginate(endpoint, params=params, max_pages=max_pages)
        
        # Limit to requested number
        prs = prs[:limit]
        
        logger.info(f"Scraped {len(prs)} pull requests from {owner}/{repo}")
        return prs
    
    def search_repositories(
        self,
        query: str,
        sort: str = 'stars',
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for repositories using GitHub's search API.
        
        Args:
            query: Search query (supports GitHub search syntax)
            sort: Sort field - 'stars', 'forks', 'updated', or 'help-wanted-issues'
            limit: Maximum number of results (default: 100)
            
        Returns:
            List of repository dictionaries matching the search query
            
        Raises:
            APIError: If search fails
            ValidationError: If sort parameter is invalid
            
        Examples:
            >>> scraper = GitHubScraper()
            >>> repos = scraper.search_repositories(
            ...     "machine learning language:python", 
            ...     sort="stars", 
            ...     limit=50
            ... )
            >>> for repo in repos[:5]:
            ...     print(f"{repo['full_name']}: {repo['stargazers_count']} stars")
        """
        valid_sorts = ['stars', 'forks', 'updated', 'help-wanted-issues']
        if sort not in valid_sorts:
            raise ValidationError(f"Invalid sort '{sort}'. Must be one of {valid_sorts}")
        
        endpoint = "/search/repositories"
        params = {'q': query, 'sort': sort, 'order': 'desc'}
        
        max_pages = (limit + DEFAULT_PER_PAGE - 1) // DEFAULT_PER_PAGE
        results = self._paginate(endpoint, params=params, max_pages=max_pages)
        
        # Limit to requested number
        results = results[:limit]
        
        logger.info(f"Search found {len(results)} repositories for query: {query}")
        return results
    
    def search_users(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search for users using GitHub's search API.
        
        Args:
            query: Search query (supports GitHub search syntax)
            limit: Maximum number of results (default: 100)
            
        Returns:
            List of user dictionaries matching the search query
            
        Raises:
            APIError: If search fails
            
        Examples:
            >>> scraper = GitHubScraper()
            >>> users = scraper.search_users("location:seattle followers:>100", limit=30)
            >>> for user in users[:5]:
            ...     print(f"{user['login']}: {user.get('score', 0)} score")
        """
        endpoint = "/search/users"
        params = {'q': query, 'order': 'desc'}
        
        max_pages = (limit + DEFAULT_PER_PAGE - 1) // DEFAULT_PER_PAGE
        results = self._paginate(endpoint, params=params, max_pages=max_pages)
        
        # Limit to requested number
        results = results[:limit]
        
        logger.info(f"Search found {len(results)} users for query: {query}")
        return results
    
    def search_code(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search for code using GitHub's search API.
        
        Args:
            query: Search query (supports GitHub search syntax)
            limit: Maximum number of results (default: 100)
            
        Returns:
            List of code match dictionaries containing:
            - File path and repository info
            - Code snippet and match details
            - Repository metadata
            
        Raises:
            APIError: If search fails
            
        Examples:
            >>> scraper = GitHubScraper()
            >>> results = scraper.search_code(
            ...     "def scrape language:python", 
            ...     limit=30
            ... )
            >>> for item in results[:5]:
            ...     print(f"{item['repository']['full_name']}: {item['path']}")
        """
        endpoint = "/search/code"
        params = {'q': query, 'order': 'desc'}
        
        max_pages = (limit + DEFAULT_PER_PAGE - 1) // DEFAULT_PER_PAGE
        results = self._paginate(endpoint, params=params, max_pages=max_pages)
        
        # Limit to requested number
        results = results[:limit]
        
        logger.info(f"Search found {len(results)} code matches for query: {query}")
        return results
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status for the authenticated user.
        
        Returns:
            Dictionary containing rate limit information:
            - core: API rate limit info
            - search: Search API rate limit info
            - graphql: GraphQL API rate limit info
            
        Examples:
            >>> scraper = GitHubScraper()
            >>> status = scraper.get_rate_limit_status()
            >>> print(f"Remaining: {status['core']['remaining']}/{status['core']['limit']}")
        """
        endpoint = "/rate_limit"
        response = self._make_request(endpoint)
        data = self.response_processor.validate_response(response)
        
        logger.info("Retrieved rate limit status")
        return data
    
    def save_data(
        self,
        data: Any,
        filename: str,
        output_dir: Optional[Union[str, Path]] = None
    ) -> Path:
        """
        Save scraped data to a JSON file.
        
        Args:
            data: Data to save
            filename: Output filename
            output_dir: Output directory (default: './output')
            
        Returns:
            Path to saved file
            
        Examples:
            >>> scraper = GitHubScraper()
            >>> repo = scraper.scrape_repository("facebook", "react")
            >>> path = scraper.save_data(repo, "react_data.json")
            >>> print(f"Saved to {path}")
        """
        if output_dir is None:
            output_dir = Path('./output')
        else:
            output_dir = Path(output_dir)
        
        filepath = output_dir / filename
        FileManager.save_json(data, filepath)
        
        logger.info(f"Saved data to {filepath}")
        return filepath
    
    def close(self) -> None:
        """
        Close the session and cleanup resources.
        
        Examples:
            >>> scraper = GitHubScraper()
            >>> try:
            ...     data = scraper.scrape_repository("owner", "repo")
            ... finally:
            ...     scraper.close()
        """
        if self.session:
            self.session.close()
            logger.info("GitHubScraper session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
