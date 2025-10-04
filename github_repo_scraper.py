#!/usr/bin/env python3
"""
GitHub Repository Scraper

Scrapes comprehensive repository metadata including:
- Basic repository information (name, description, stars, forks)
- Repository statistics (commits, contributors, languages)
- Recent commits with details
- Contributors with contribution counts
- Release information
- Topics and metadata

Usage:
    python github_repo_scraper.py owner/repo [--output file.json] [--include-commits] [--max-commits 100]
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    from utils import GitHubAPIClient, RateLimiter, save_json, setup_logging
    from config import GITHUB_TOKEN
except ImportError:
    print("Error: Missing required modules. Please ensure utils.py and config.py are present.")
    sys.exit(1)

import logging
logger = setup_logging(__name__)


class GitHubRepoScraper:
    """Scraper for GitHub repository data."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the repository scraper.
        
        Args:
            token: GitHub personal access token (optional)
        """
        self.client = GitHubAPIClient(token)
        self.rate_limiter = RateLimiter()
    
    def scrape_repository(self, owner: str, repo: str, 
                         include_commits: bool = False,
                         max_commits: int = 100) -> Dict[str, Any]:
        """
        Scrape comprehensive repository information.
        
        Args:
            owner: Repository owner
            repo: Repository name
            include_commits: Whether to include commit history
            max_commits: Maximum number of commits to fetch
            
        Returns:
            Dictionary containing all repository data
        """
        logger.info(f"Scraping repository: {owner}/{repo}")
        
        data = {
            'scraped_at': datetime.utcnow().isoformat(),
            'repository': f"{owner}/{repo}",
            'metadata': {},
            'statistics': {},
            'contributors': [],
            'languages': {},
            'topics': [],
            'recent_releases': [],
        }
        
        # Get basic repository information
        try:
            repo_data = self._get_repo_info(owner, repo)
            data['metadata'] = repo_data
            logger.info(f"Retrieved repository metadata: {repo_data.get('full_name')}")
        except Exception as e:
            logger.error(f"Failed to get repository info: {e}")
            raise
        
        # Get repository statistics
        try:
            data['statistics'] = self._get_repo_stats(owner, repo)
            logger.info("Retrieved repository statistics")
        except Exception as e:
            logger.warning(f"Failed to get repository stats: {e}")
        
        # Get contributors
        try:
            data['contributors'] = self._get_contributors(owner, repo)
            logger.info(f"Retrieved {len(data['contributors'])} contributors")
        except Exception as e:
            logger.warning(f"Failed to get contributors: {e}")
        
        # Get languages
        try:
            data['languages'] = self._get_languages(owner, repo)
            logger.info(f"Retrieved {len(data['languages'])} languages")
        except Exception as e:
            logger.warning(f"Failed to get languages: {e}")
        
        # Get topics
        try:
            data['topics'] = self._get_topics(owner, repo)
            logger.info(f"Retrieved {len(data['topics'])} topics")
        except Exception as e:
            logger.warning(f"Failed to get topics: {e}")
        
        # Get recent releases
        try:
            data['recent_releases'] = self._get_releases(owner, repo, limit=10)
            logger.info(f"Retrieved {len(data['recent_releases'])} releases")
        except Exception as e:
            logger.warning(f"Failed to get releases: {e}")
        
        # Get commits if requested
        if include_commits:
            try:
                data['commits'] = self._get_commits(owner, repo, max_commits)
                logger.info(f"Retrieved {len(data['commits'])} commits")
            except Exception as e:
                logger.warning(f"Failed to get commits: {e}")
        
        return data
    
    def _get_repo_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get basic repository information."""
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.client.base_url}/repos/{owner}/{repo}"
        response = self.client.get(url)
        
        repo_data = response.json()
        
        return {
            'name': repo_data.get('name'),
            'full_name': repo_data.get('full_name'),
            'description': repo_data.get('description'),
            'url': repo_data.get('html_url'),
            'created_at': repo_data.get('created_at'),
            'updated_at': repo_data.get('updated_at'),
            'pushed_at': repo_data.get('pushed_at'),
            'size': repo_data.get('size'),
            'stars': repo_data.get('stargazers_count'),
            'watchers': repo_data.get('watchers_count'),
            'forks': repo_data.get('forks_count'),
            'open_issues': repo_data.get('open_issues_count'),
            'default_branch': repo_data.get('default_branch'),
            'language': repo_data.get('language'),
            'license': repo_data.get('license', {}).get('name') if repo_data.get('license') else None,
            'archived': repo_data.get('archived'),
            'disabled': repo_data.get('disabled'),
            'private': repo_data.get('private'),
            'fork': repo_data.get('fork'),
            'homepage': repo_data.get('homepage'),
        }
    
    def _get_repo_stats(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository statistics."""
        stats = {}
        
        # Get commit count (approximate from recent commits)
        self.rate_limiter.wait_if_needed()
        url = f"{self.client.base_url}/repos/{owner}/{repo}/commits"
        response = self.client.get(url, params={'per_page': 1})
        
        # Try to extract total count from Link header
        if 'Link' in response.headers:
            link_header = response.headers['Link']
            if 'last' in link_header:
                try:
                    last_page = int(link_header.split('page=')[-1].split('>')[0])
                    stats['approximate_commits'] = last_page * 100  # Rough estimate
                except:
                    pass
        
        return stats
    
    def _get_contributors(self, owner: str, repo: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get repository contributors."""
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.client.base_url}/repos/{owner}/{repo}/contributors"
        response = self.client.get(url, params={'per_page': limit})
        
        contributors_data = response.json()
        
        contributors = []
        for contributor in contributors_data:
            contributors.append({
                'username': contributor.get('login'),
                'contributions': contributor.get('contributions'),
                'profile_url': contributor.get('html_url'),
                'avatar_url': contributor.get('avatar_url'),
            })
        
        return contributors
    
    def _get_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """Get repository languages."""
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.client.base_url}/repos/{owner}/{repo}/languages"
        response = self.client.get(url)
        
        return response.json()
    
    def _get_topics(self, owner: str, repo: str) -> List[str]:
        """Get repository topics."""
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.client.base_url}/repos/{owner}/{repo}/topics"
        headers = {'Accept': 'application/vnd.github.mercy-preview+json'}
        response = self.client.get(url, headers=headers)
        
        data = response.json()
        return data.get('names', [])
    
    def _get_releases(self, owner: str, repo: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent releases."""
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.client.base_url}/repos/{owner}/{repo}/releases"
        response = self.client.get(url, params={'per_page': limit})
        
        releases_data = response.json()
        
        releases = []
        for release in releases_data:
            releases.append({
                'name': release.get('name'),
                'tag_name': release.get('tag_name'),
                'published_at': release.get('published_at'),
                'url': release.get('html_url'),
                'draft': release.get('draft'),
                'prerelease': release.get('prerelease'),
                'author': release.get('author', {}).get('login'),
            })
        
        return releases
    
    def _get_commits(self, owner: str, repo: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent commits."""
        commits = []
        per_page = min(limit, 100)
        pages = (limit + per_page - 1) // per_page
        
        for page in range(1, pages + 1):
            self.rate_limiter.wait_if_needed()
            
            url = f"{self.client.base_url}/repos/{owner}/{repo}/commits"
            response = self.client.get(url, params={'per_page': per_page, 'page': page})
            
            commits_data = response.json()
            if not commits_data:
                break
            
            for commit in commits_data:
                commits.append({
                    'sha': commit.get('sha'),
                    'message': commit.get('commit', {}).get('message'),
                    'author': commit.get('commit', {}).get('author', {}).get('name'),
                    'author_email': commit.get('commit', {}).get('author', {}).get('email'),
                    'date': commit.get('commit', {}).get('author', {}).get('date'),
                    'url': commit.get('html_url'),
                })
            
            if len(commits) >= limit:
                break
        
        return commits[:limit]


def main():
    """Command-line interface for the repository scraper."""
    parser = argparse.ArgumentParser(
        description='Scrape GitHub repository data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python github_repo_scraper.py microsoft/vscode
  python github_repo_scraper.py torvalds/linux --include-commits --max-commits 50
  python github_repo_scraper.py facebook/react --output react_data.json
        """
    )
    
    parser.add_argument('repository', help='Repository in format owner/repo')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    parser.add_argument('--include-commits', action='store_true', 
                       help='Include commit history')
    parser.add_argument('--max-commits', type=int, default=100,
                       help='Maximum number of commits to fetch (default: 100)')
    parser.add_argument('--token', help='GitHub personal access token')
    
    args = parser.parse_args()
    
    # Parse repository
    if '/' not in args.repository:
        parser.error('Repository must be in format owner/repo')
    
    owner, repo = args.repository.split('/', 1)
    
    # Use token from args or config
    token = args.token or GITHUB_TOKEN
    
    # Create scraper and fetch data
    scraper = GitHubRepoScraper(token)
    
    try:
        data = scraper.scrape_repository(
            owner, repo,
            include_commits=args.include_commits,
            max_commits=args.max_commits
        )
        
        # Save or print data
        if args.output:
            save_json(data, args.output)
            print(f"Data saved to {args.output}")
        else:
            print(json.dumps(data, indent=2))
        
        # Print summary
        logger.info("\n=== Scraping Summary ===")
        logger.info(f"Repository: {data['metadata']['full_name']}")
        logger.info(f"Stars: {data['metadata']['stars']}")
        logger.info(f"Forks: {data['metadata']['forks']}")
        logger.info(f"Contributors: {len(data['contributors'])}")
        logger.info(f"Languages: {len(data['languages'])}")
        if args.include_commits:
            logger.info(f"Commits fetched: {len(data.get('commits', []))}")
        
    except Exception as e:
        logger.error(f"Error scraping repository: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
