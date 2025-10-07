#!/usr/bin/env python3
"""
Comprehensive GitHub Repository Scraper

This scraper extracts extensive repository metadata, statistics, commit history,
contributors, languages, file structure, and more. It leverages the utils.py
and config.py modules for robust operation.

Features:
- Repository metadata and statistics
- Commit history with detailed information
- Contributor analysis and statistics
- Language breakdown and file analysis
- File tree structure mapping
- Issue and pull request data
- Release information
- Topic and tag analysis
- README and documentation extraction
- License information
- Comprehensive CLI interface

Author: Stephen Thompson
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import concurrent.futures
from dataclasses import dataclass, asdict

# Import our utility modules
try:
    from utils import (
        RateLimiter, APIResponseProcessor, DataFormatter, FileManager,
        setup_logging, handle_api_errors, exponential_backoff, 
        create_session, DataValidator, ScrapingError, APIError,
        parse_github_url, safe_get, get_timestamp
    )
    from config import (
        get_github_token, get_rate_limit, GITHUB_API_BASE_URL,
        DEFAULT_MAX_COMMITS, DEFAULT_MAX_CONTRIBUTORS, DEFAULT_MAX_RELEASES,
        DEFAULT_PER_PAGE, get_output_path, get_log_path,
        SCRAPE_METADATA, SCRAPE_STATISTICS, SCRAPE_COMMITS, SCRAPE_CONTRIBUTORS,
        SCRAPE_LANGUAGES, SCRAPE_TOPICS, SCRAPE_RELEASES, SCRAPE_FILE_TREE,
        SCRAPE_README, SCRAPE_LICENSE, DEFAULT_FILE_TREE_DEPTH
    )
except ImportError as e:
    print(f"Error: Missing required modules: {e}")
    print("Please ensure utils.py and config.py are present in the same directory.")
    sys.exit(1)

import requests
import logging

# Setup logging
logger = setup_logging(level='INFO', log_file=str(get_log_path('repo_scraper')))


@dataclass
class ScrapingOptions:
    """Configuration options for repository scraping."""
    include_metadata: bool = True
    include_statistics: bool = True
    include_commits: bool = False
    include_contributors: bool = True
    include_languages: bool = True
    include_topics: bool = True
    include_releases: bool = True
    include_issues: bool = False
    include_pull_requests: bool = False
    include_file_tree: bool = True
    include_readme: bool = True
    include_license: bool = True
    
    max_commits: int = DEFAULT_MAX_COMMITS
    max_contributors: int = DEFAULT_MAX_CONTRIBUTORS
    max_releases: int = DEFAULT_MAX_RELEASES
    max_issues: int = 100
    max_pull_requests: int = 100
    file_tree_depth: int = DEFAULT_FILE_TREE_DEPTH
    
    output_format: str = 'json'
    output_file: Optional[str] = None
    verbose: bool = False


class GitHubRepoScraper:
    """Comprehensive GitHub repository scraper."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the repository scraper.
        
        Args:
            token: GitHub personal access token
        """
        self.token = token or get_github_token()
        self.base_url = GITHUB_API_BASE_URL
        self.session = create_session()
        
        # Setup authentication
        if self.token:
            self.session.headers.update({
                'Authorization': f'token {self.token}',
                'Accept': 'application/vnd.github.v3+json'
            })
        
        # Rate limiting
        self.rate_limiter = RateLimiter(get_rate_limit())
        
        # Response processor
        self.response_processor = APIResponseProcessor()
        
        logger.info(f"Initialized scraper with {'authenticated' if self.token else 'unauthenticated'} access")
    
    def close(self):
        """Close the session and cleanup resources."""
        if hasattr(self, 'session'):
            self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.close()
    
    @exponential_backoff(max_retries=3)
    @handle_api_errors
    def _make_request(self, url: str, params: Optional[Dict] = None, 
                     headers: Optional[Dict] = None) -> requests.Response:
        """Make a rate-limited API request."""
        # Apply rate limiting
        self.rate_limiter.wait()
        
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)
        
        logger.debug(f"Making request to: {url}")
        response = self.session.get(url, params=params, headers=request_headers)
        
        # Log rate limit info
        rate_info = self.response_processor.get_rate_limit_info(response)
        if rate_info['remaining'] < 10:
            logger.warning(f"Rate limit low: {rate_info['remaining']} requests remaining")
        
        return response
    
    def scrape_repository(self, owner: str, repo: str, 
                         options: Optional[ScrapingOptions] = None) -> Dict[str, Any]:
        """
        Scrape comprehensive repository information.
        
        Args:
            owner: Repository owner
            repo: Repository name
            options: Scraping configuration options
            
        Returns:
            Dictionary containing all repository data
        """
        if options is None:
            options = ScrapingOptions()
        
        logger.info(f"Starting comprehensive scrape of {owner}/{repo}")
        start_time = time.time()
        
        # Initialize result structure
        result = {
            'scraping_info': {
                'scraped_at': get_timestamp(),
                'scraper_version': '2.0.0',
                'repository': f"{owner}/{repo}",
                'options': asdict(options)
            },
            'repository': {
                'owner': owner,
                'name': repo,
                'full_name': f"{owner}/{repo}"
            }
        }
        
        # Track what was successfully scraped
        scraped_sections = []
        
        try:
            # Repository metadata (always included)
            if options.include_metadata:
                logger.info("Scraping repository metadata...")
                result['metadata'] = self._scrape_metadata(owner, repo)
                scraped_sections.append('metadata')
            
            # Repository statistics
            if options.include_statistics:
                logger.info("Scraping repository statistics...")
                result['statistics'] = self._scrape_statistics(owner, repo)
                scraped_sections.append('statistics')
            
            # Contributors
            if options.include_contributors:
                logger.info("Scraping contributors...")
                result['contributors'] = self._scrape_contributors(
                    owner, repo, options.max_contributors
                )
                scraped_sections.append('contributors')
            
            # Languages
            if options.include_languages:
                logger.info("Scraping languages...")
                result['languages'] = self._scrape_languages(owner, repo)
                scraped_sections.append('languages')
            
            # Topics
            if options.include_topics:
                logger.info("Scraping topics...")
                result['topics'] = self._scrape_topics(owner, repo)
                scraped_sections.append('topics')
            
            # Releases
            if options.include_releases:
                logger.info("Scraping releases...")
                result['releases'] = self._scrape_releases(
                    owner, repo, options.max_releases
                )
                scraped_sections.append('releases')
            
            # README
            if options.include_readme:
                logger.info("Scraping README...")
                result['readme'] = self._scrape_readme(owner, repo)
                scraped_sections.append('readme')
            
            # License
            if options.include_license:
                logger.info("Scraping license...")
                result['license'] = self._scrape_license(owner, repo)
                scraped_sections.append('license')
            
            # File tree
            if options.include_file_tree:
                logger.info("Scraping file tree...")
                result['file_tree'] = self._scrape_file_tree(
                    owner, repo, options.file_tree_depth
                )
                scraped_sections.append('file_tree')
            
            # Commits (can be large)
            if options.include_commits:
                logger.info("Scraping commits...")
                result['commits'] = self._scrape_commits(
                    owner, repo, options.max_commits
                )
                scraped_sections.append('commits')
            
            # Issues (can be large)
            if options.include_issues:
                logger.info("Scraping issues...")
                result['issues'] = self._scrape_issues(
                    owner, repo, options.max_issues
                )
                scraped_sections.append('issues')
            
            # Pull requests (can be large)
            if options.include_pull_requests:
                logger.info("Scraping pull requests...")
                result['pull_requests'] = self._scrape_pull_requests(
                    owner, repo, options.max_pull_requests
                )
                scraped_sections.append('pull_requests')
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            result['scraping_info']['error'] = str(e)
            result['scraping_info']['partial_success'] = True
        
        # Add scraping summary
        end_time = time.time()
        result['scraping_info'].update({
            'duration_seconds': round(end_time - start_time, 2),
            'sections_scraped': scraped_sections,
            'success': 'error' not in result['scraping_info']
        })
        
        logger.info(f"Scraping completed in {result['scraping_info']['duration_seconds']}s")
        logger.info(f"Sections scraped: {', '.join(scraped_sections)}")
        
        return result
    
    def _scrape_metadata(self, owner: str, repo: str) -> Dict[str, Any]:
        """Scrape basic repository metadata."""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        response = self._make_request(url)
        data = self.response_processor.validate_response(response)
        
        return DataFormatter.normalize_github_data(data)
    
    def _scrape_statistics(self, owner: str, repo: str) -> Dict[str, Any]:
        """Scrape repository statistics."""
        stats = {}
        
        # Get commit activity (weekly)
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/stats/commit_activity"
            response = self._make_request(url)
            if response.status_code == 200:
                commit_activity = response.json()
                if commit_activity:
                    total_commits = sum(week.get('total', 0) for week in commit_activity)
                    stats['total_commits_52_weeks'] = total_commits
                    stats['commit_activity_weekly'] = commit_activity[-4:]  # Last 4 weeks
        except Exception as e:
            logger.warning(f"Failed to get commit activity: {e}")
        
        # Get code frequency
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/stats/code_frequency"
            response = self._make_request(url)
            if response.status_code == 200:
                code_frequency = response.json()
                if code_frequency:
                    stats['code_frequency'] = code_frequency[-4:]  # Last 4 weeks
        except Exception as e:
            logger.warning(f"Failed to get code frequency: {e}")
        
        # Get participation stats
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/stats/participation"
            response = self._make_request(url)
            if response.status_code == 200:
                participation = response.json()
                stats['participation'] = participation
        except Exception as e:
            logger.warning(f"Failed to get participation stats: {e}")
        
        return stats
    
    def _scrape_contributors(self, owner: str, repo: str, limit: int) -> List[Dict[str, Any]]:
        """Scrape repository contributors."""
        contributors = []
        page = 1
        per_page = min(limit, DEFAULT_PER_PAGE)
        
        while len(contributors) < limit:
            url = f"{self.base_url}/repos/{owner}/{repo}/contributors"
            params = {'page': page, 'per_page': per_page}
            
            response = self._make_request(url, params=params)
            data = self.response_processor.validate_response(response)
            
            if not data:
                break
            
            for contributor in data:
                if len(contributors) >= limit:
                    break
                
                contributor_data = {
                    'username': contributor.get('login'),
                    'contributions': contributor.get('contributions'),
                    'profile_url': contributor.get('html_url'),
                    'avatar_url': contributor.get('avatar_url'),
                    'type': contributor.get('type'),
                    'site_admin': contributor.get('site_admin', False)
                }
                contributors.append(contributor_data)
            
            page += 1
            if len(data) < per_page:
                break
        
        return contributors
    
    def _scrape_languages(self, owner: str, repo: str) -> Dict[str, Any]:
        """Scrape repository languages."""
        url = f"{self.base_url}/repos/{owner}/{repo}/languages"
        response = self._make_request(url)
        languages_data = self.response_processor.validate_response(response)
        
        # Calculate percentages
        total_bytes = sum(languages_data.values())
        languages_with_percentages = {}
        
        for language, bytes_count in languages_data.items():
            percentage = (bytes_count / total_bytes * 100) if total_bytes > 0 else 0
            languages_with_percentages[language] = {
                'bytes': bytes_count,
                'percentage': round(percentage, 2)
            }
        
        return {
            'languages': languages_with_percentages,
            'total_bytes': total_bytes,
            'primary_language': max(languages_data.keys(), key=languages_data.get) if languages_data else None
        }
    
    def _scrape_topics(self, owner: str, repo: str) -> List[str]:
        """Scrape repository topics."""
        url = f"{self.base_url}/repos/{owner}/{repo}/topics"
        headers = {'Accept': 'application/vnd.github.mercy-preview+json'}
        
        response = self._make_request(url, headers=headers)
        data = self.response_processor.validate_response(response)
        
        return data.get('names', [])
    
    def _scrape_releases(self, owner: str, repo: str, limit: int) -> List[Dict[str, Any]]:
        """Scrape repository releases."""
        releases = []
        page = 1
        per_page = min(limit, DEFAULT_PER_PAGE)
        
        while len(releases) < limit:
            url = f"{self.base_url}/repos/{owner}/{repo}/releases"
            params = {'page': page, 'per_page': per_page}
            
            response = self._make_request(url, params=params)
            data = self.response_processor.validate_response(response)
            
            if not data:
                break
            
            for release in data:
                if len(releases) >= limit:
                    break
                
                release_data = {
                    'id': release.get('id'),
                    'name': release.get('name'),
                    'tag_name': release.get('tag_name'),
                    'target_commitish': release.get('target_commitish'),
                    'draft': release.get('draft'),
                    'prerelease': release.get('prerelease'),
                    'created_at': release.get('created_at'),
                    'published_at': release.get('published_at'),
                    'author': {
                        'login': safe_get(release, 'author.login'),
                        'avatar_url': safe_get(release, 'author.avatar_url')
                    },
                    'body': DataValidator.clean_text(release.get('body', '')),
                    'html_url': release.get('html_url'),
                    'assets_count': len(release.get('assets', [])),
                    'download_count': sum(asset.get('download_count', 0) for asset in release.get('assets', []))
                }
                releases.append(release_data)
            
            page += 1
            if len(data) < per_page:
                break
        
        return releases
    
    def _scrape_readme(self, owner: str, repo: str) -> Dict[str, Any]:
        """Scrape repository README."""
        url = f"{self.base_url}/repos/{owner}/{repo}/readme"
        
        try:
            response = self._make_request(url)
            data = self.response_processor.validate_response(response)
            
            return {
                'name': data.get('name'),
                'path': data.get('path'),
                'size': data.get('size'),
                'content': data.get('content'),  # Base64 encoded
                'encoding': data.get('encoding'),
                'html_url': data.get('html_url'),
                'download_url': data.get('download_url')
            }
        except APIError as e:
            if "404" in str(e):
                return {'error': 'README not found'}
            raise
    
    def _scrape_license(self, owner: str, repo: str) -> Dict[str, Any]:
        """Scrape repository license information."""
        url = f"{self.base_url}/repos/{owner}/{repo}/license"
        
        try:
            response = self._make_request(url)
            data = self.response_processor.validate_response(response)
            
            return {
                'name': safe_get(data, 'license.name'),
                'key': safe_get(data, 'license.key'),
                'spdx_id': safe_get(data, 'license.spdx_id'),
                'url': safe_get(data, 'license.url'),
                'content': data.get('content'),  # Base64 encoded
                'encoding': data.get('encoding'),
                'html_url': data.get('html_url'),
                'download_url': data.get('download_url')
            }
        except APIError as e:
            if "404" in str(e):
                return {'error': 'License not found'}
            raise
    
    def _scrape_file_tree(self, owner: str, repo: str, max_depth: int) -> Dict[str, Any]:
        """Scrape repository file tree structure."""
        def get_tree_recursive(sha: str, path: str = "", depth: int = 0) -> List[Dict[str, Any]]:
            if depth >= max_depth:
                return []
            
            url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{sha}"
            params = {'recursive': '1' if depth == 0 else '0'}
            
            response = self._make_request(url, params=params)
            data = self.response_processor.validate_response(response)
            
            tree_items = []
            for item in data.get('tree', []):
                item_data = {
                    'path': item.get('path'),
                    'mode': item.get('mode'),
                    'type': item.get('type'),
                    'size': item.get('size'),
                    'sha': item.get('sha'),
                    'url': item.get('url')
                }
                tree_items.append(item_data)
            
            return tree_items
        
        try:
            # Get default branch first
            repo_url = f"{self.base_url}/repos/{owner}/{repo}"
            repo_response = self._make_request(repo_url)
            repo_data = self.response_processor.validate_response(repo_response)
            default_branch = repo_data.get('default_branch', 'main')
            
            # Get the tree
            tree_items = get_tree_recursive(default_branch)
            
            # Analyze file structure
            file_types = {}
            total_files = 0
            total_size = 0
            
            for item in tree_items:
                if item['type'] == 'blob':  # It's a file
                    total_files += 1
                    if item.get('size'):
                        total_size += item['size']
                    
                    # Get file extension
                    path = item['path']
                    if '.' in path:
                        ext = path.split('.')[-1].lower()
                        file_types[ext] = file_types.get(ext, 0) + 1
            
            return {
                'tree': tree_items[:1000],  # Limit to prevent huge responses
                'total_items': len(tree_items),
                'total_files': total_files,
                'total_size_bytes': total_size,
                'file_types': file_types,
                'analyzed_at_depth': max_depth
            }
            
        except Exception as e:
            logger.warning(f"Failed to scrape file tree: {e}")
            return {'error': str(e)}
    
    def _scrape_commits(self, owner: str, repo: str, limit: int) -> List[Dict[str, Any]]:
        """Scrape repository commits."""
        commits = []
        page = 1
        per_page = min(limit, DEFAULT_PER_PAGE)
        
        while len(commits) < limit:
            url = f"{self.base_url}/repos/{owner}/{repo}/commits"
            params = {'page': page, 'per_page': per_page}
            
            response = self._make_request(url, params=params)
            data = self.response_processor.validate_response(response)
            
            if not data:
                break
            
            for commit in data:
                if len(commits) >= limit:
                    break
                
                commit_data = {
                    'sha': commit.get('sha'),
                    'message': DataValidator.clean_text(safe_get(commit, 'commit.message', '')),
                    'author': {
                        'name': safe_get(commit, 'commit.author.name'),
                        'email': safe_get(commit, 'commit.author.email'),
                        'date': safe_get(commit, 'commit.author.date'),
                        'login': safe_get(commit, 'author.login') if commit.get('author') else None
                    },
                    'committer': {
                        'name': safe_get(commit, 'commit.committer.name'),
                        'email': safe_get(commit, 'commit.committer.email'),
                        'date': safe_get(commit, 'commit.committer.date'),
                        'login': safe_get(commit, 'committer.login') if commit.get('committer') else None
                    },
                    'html_url': commit.get('html_url'),
                    'parents': [p.get('sha') for p in commit.get('parents', [])],
                    'stats': commit.get('stats')  # May not be available in list view
                }
                commits.append(commit_data)
            
            page += 1
            if len(data) < per_page:
                break
        
        return commits
    
    def _scrape_issues(self, owner: str, repo: str, limit: int) -> List[Dict[str, Any]]:
        """Scrape repository issues."""
        issues = []
        page = 1
        per_page = min(limit, DEFAULT_PER_PAGE)
        
        while len(issues) < limit:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues"
            params = {
                'page': page, 
                'per_page': per_page,
                'state': 'all'  # Get both open and closed
            }
            
            response = self._make_request(url, params=params)
            data = self.response_processor.validate_response(response)
            
            if not data:
                break
            
            for issue in data:
                # Skip pull requests (they appear in issues API)
                if 'pull_request' in issue:
                    continue
                
                if len(issues) >= limit:
                    break
                
                issue_data = {
                    'id': issue.get('id'),
                    'number': issue.get('number'),
                    'title': DataValidator.clean_text(issue.get('title', '')),
                    'body': DataValidator.clean_text(issue.get('body', '')),
                    'state': issue.get('state'),
                    'created_at': issue.get('created_at'),
                    'updated_at': issue.get('updated_at'),
                    'closed_at': issue.get('closed_at'),
                    'author': {
                        'login': safe_get(issue, 'user.login'),
                        'avatar_url': safe_get(issue, 'user.avatar_url')
                    },
                    'assignees': [a.get('login') for a in issue.get('assignees', [])],
                    'labels': [l.get('name') for l in issue.get('labels', [])],
                    'comments': issue.get('comments'),
                    'html_url': issue.get('html_url')
                }
                issues.append(issue_data)
            
            page += 1
            if len(data) < per_page:
                break
        
        return issues
    
    def _scrape_pull_requests(self, owner: str, repo: str, limit: int) -> List[Dict[str, Any]]:
        """Scrape repository pull requests."""
        pull_requests = []
        page = 1
        per_page = min(limit, DEFAULT_PER_PAGE)
        
        while len(pull_requests) < limit:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
            params = {
                'page': page, 
                'per_page': per_page,
                'state': 'all'  # Get both open and closed
            }
            
            response = self._make_request(url, params=params)
            data = self.response_processor.validate_response(response)
            
            if not data:
                break
            
            for pr in data:
                if len(pull_requests) >= limit:
                    break
                
                pr_data = {
                    'id': pr.get('id'),
                    'number': pr.get('number'),
                    'title': DataValidator.clean_text(pr.get('title', '')),
                    'body': DataValidator.clean_text(pr.get('body', '')),
                    'state': pr.get('state'),
                    'created_at': pr.get('created_at'),
                    'updated_at': pr.get('updated_at'),
                    'closed_at': pr.get('closed_at'),
                    'merged_at': pr.get('merged_at'),
                    'author': {
                        'login': safe_get(pr, 'user.login'),
                        'avatar_url': safe_get(pr, 'user.avatar_url')
                    },
                    'head': {
                        'ref': safe_get(pr, 'head.ref'),
                        'sha': safe_get(pr, 'head.sha'),
                        'repo': safe_get(pr, 'head.repo.full_name')
                    },
                    'base': {
                        'ref': safe_get(pr, 'base.ref'),
                        'sha': safe_get(pr, 'base.sha')
                    },
                    'assignees': [a.get('login') for a in pr.get('assignees', [])],
                    'labels': [l.get('name') for l in pr.get('labels', [])],
                    'comments': pr.get('comments'),
                    'commits': pr.get('commits'),
                    'additions': pr.get('additions'),
                    'deletions': pr.get('deletions'),
                    'changed_files': pr.get('changed_files'),
                    'html_url': pr.get('html_url')
                }
                pull_requests.append(pr_data)
            
            page += 1
            if len(data) < per_page:
                break
        
        return pull_requests


def create_scraping_options_from_args(args) -> ScrapingOptions:
    """Create ScrapingOptions from command line arguments."""
    return ScrapingOptions(
        include_metadata=not args.no_metadata,
        include_statistics=not args.no_statistics,
        include_commits=args.include_commits,
        include_contributors=not args.no_contributors,
        include_languages=not args.no_languages,
        include_topics=not args.no_topics,
        include_releases=not args.no_releases,
        include_issues=args.include_issues,
        include_pull_requests=args.include_pull_requests,
        include_file_tree=not args.no_file_tree,
        include_readme=not args.no_readme,
        include_license=not args.no_license,
        
        max_commits=args.max_commits,
        max_contributors=args.max_contributors,
        max_releases=args.max_releases,
        max_issues=args.max_issues,
        max_pull_requests=args.max_pull_requests,
        file_tree_depth=args.file_tree_depth,
        
        output_format=args.format,
        output_file=args.output,
        verbose=args.verbose
    )


def print_scraping_summary(data: Dict[str, Any]) -> None:
    """Print a summary of scraped data."""
    info = data.get('scraping_info', {})
    repo_name = info.get('repository', 'Unknown')
    
    print(f"\n{'='*60}")
    print(f"SCRAPING SUMMARY: {repo_name}")
    print(f"{'='*60}")
    
    print(f"Duration: {info.get('duration_seconds', 0)}s")
    print(f"Success: {'✓' if info.get('success') else '✗'}")
    
    if 'error' in info:
        print(f"Error: {info['error']}")
    
    sections = info.get('sections_scraped', [])
    print(f"Sections scraped ({len(sections)}): {', '.join(sections)}")
    
    # Print key metrics if available
    if 'metadata' in data:
        meta = data['metadata']
        print(f"\nRepository Metrics:")
        print(f"  Stars: {meta.get('stars', 0):,}")
        print(f"  Forks: {meta.get('forks', 0):,}")
        print(f"  Size: {meta.get('size', 0):,} KB")
        print(f"  Language: {meta.get('language', 'Unknown')}")
    
    if 'contributors' in data:
        print(f"  Contributors: {len(data['contributors'])}")
    
    if 'languages' in data:
        langs = data['languages'].get('languages', {})
        print(f"  Languages: {len(langs)}")
    
    if 'commits' in data:
        print(f"  Commits scraped: {len(data['commits'])}")
    
    if 'issues' in data:
        print(f"  Issues scraped: {len(data['issues'])}")
    
    if 'pull_requests' in data:
        print(f"  Pull requests scraped: {len(data['pull_requests'])}")
    
    print(f"{'='*60}")


def main():
    """Command-line interface for the repository scraper."""
    parser = argparse.ArgumentParser(
        description='Comprehensive GitHub Repository Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic scraping
  python github_repo_scraper.py microsoft/vscode
  
  # Include commits and issues
  python github_repo_scraper.py torvalds/linux --include-commits --include-issues
  
  # Comprehensive scraping with custom limits
  python github_repo_scraper.py facebook/react --include-commits --include-issues \\
    --include-pull-requests --max-commits 200 --max-issues 100
  
  # Save to specific file
  python github_repo_scraper.py google/tensorflow --output tensorflow_data.json
  
  # Minimal scraping (metadata only)
  python github_repo_scraper.py owner/repo --no-contributors --no-languages \\
    --no-topics --no-releases --no-file-tree
        """
    )
    
    # Repository argument
    parser.add_argument('repository', 
                       help='Repository in format owner/repo or GitHub URL')
    
    # Output options
    parser.add_argument('--output', '-o', 
                       help='Output file path (default: auto-generated)')
    parser.add_argument('--format', choices=['json', 'csv'], default='json',
                       help='Output format (default: json)')
    
    # What to include (large datasets)
    parser.add_argument('--include-commits', action='store_true',
                       help='Include commit history (can be large)')
    parser.add_argument('--include-issues', action='store_true',
                       help='Include issues (can be large)')
    parser.add_argument('--include-pull-requests', action='store_true',
                       help='Include pull requests (can be large)')
    
    # What to exclude (normally included)
    parser.add_argument('--no-metadata', action='store_true',
                       help='Skip repository metadata')
    parser.add_argument('--no-statistics', action='store_true',
                       help='Skip repository statistics')
    parser.add_argument('--no-contributors', action='store_true',
                       help='Skip contributors')
    parser.add_argument('--no-languages', action='store_true',
                       help='Skip language breakdown')
    parser.add_argument('--no-topics', action='store_true',
                       help='Skip topics')
    parser.add_argument('--no-releases', action='store_true',
                       help='Skip releases')
    parser.add_argument('--no-file-tree', action='store_true',
                       help='Skip file tree structure')
    parser.add_argument('--no-readme', action='store_true',
                       help='Skip README')
    parser.add_argument('--no-license', action='store_true',
                       help='Skip license information')
    
    # Limits
    parser.add_argument('--max-commits', type=int, default=DEFAULT_MAX_COMMITS,
                       help=f'Maximum commits to fetch (default: {DEFAULT_MAX_COMMITS})')
    parser.add_argument('--max-contributors', type=int, default=DEFAULT_MAX_CONTRIBUTORS,
                       help=f'Maximum contributors to fetch (default: {DEFAULT_MAX_CONTRIBUTORS})')
    parser.add_argument('--max-releases', type=int, default=DEFAULT_MAX_RELEASES,
                       help=f'Maximum releases to fetch (default: {DEFAULT_MAX_RELEASES})')
    parser.add_argument('--max-issues', type=int, default=100,
                       help='Maximum issues to fetch (default: 100)')
    parser.add_argument('--max-pull-requests', type=int, default=100,
                       help='Maximum pull requests to fetch (default: 100)')
    parser.add_argument('--file-tree-depth', type=int, default=DEFAULT_FILE_TREE_DEPTH,
                       help=f'File tree depth (default: {DEFAULT_FILE_TREE_DEPTH})')
    
    # Other options
    parser.add_argument('--token', help='GitHub personal access token')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Parse repository
    try:
        if args.repository.startswith('http'):
            parsed = parse_github_url(args.repository)
            owner, repo = parsed['owner'], parsed['repo']
        else:
            if '/' not in args.repository:
                parser.error('Repository must be in format owner/repo or a GitHub URL')
            owner, repo = args.repository.split('/', 1)
    except ValueError as e:
        parser.error(f"Invalid repository format: {e}")
    
    # Create scraping options
    options = create_scraping_options_from_args(args)
    
    # Use token from args or config
    token = args.token or get_github_token()
    if not token:
        logger.warning("No GitHub token provided. Rate limits will be lower.")
        logger.info("Set GITHUB_TOKEN environment variable for better rate limits.")
    
    # Create scraper and fetch data
    scraper = GitHubRepoScraper(token)
    
    try:
        logger.info(f"Starting scrape of {owner}/{repo}")
        data = scraper.scrape_repository(owner, repo, options)
        
        # Determine output file
        if args.output:
            output_file = Path(args.output)
        else:
            safe_repo_name = DataValidator.sanitize_filename(f"{owner}_{repo}")
            output_file = get_output_path(f"{safe_repo_name}_repo_data", args.format)
        
        # Save data
        if args.format == 'json':
            FileManager.save_json(data, output_file)
        elif args.format == 'csv':
            # Flatten data for CSV
            flattened = DataFormatter.flatten_dict(data)
            FileManager.save_csv([flattened], output_file)
        
        print(f"✓ Data saved to {output_file}")
        
        # Print summary
        print_scraping_summary(data)
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error scraping repository: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()