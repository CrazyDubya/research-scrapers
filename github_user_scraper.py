#!/usr/bin/env python3
"""
GitHub User/Organization Scraper

Scrapes comprehensive data from GitHub user and organization profiles including:
- Profile information
- Repositories
- Activity/events
- Followers/Following
- Contribution data
- Organization membership
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

from utils import (
    setup_logging, 
    save_data, 
    load_data, 
    create_session_with_retries,
    rate_limit_handler,
    sanitize_filename
)
from config import (
    GITHUB_TOKEN,
    OUTPUT_DIR,
    REQUEST_DELAY,
    MAX_RETRIES,
    TIMEOUT,
    USER_AGENT
)


class GitHubUserScraper:
    """Scraper for GitHub user and organization data"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or GITHUB_TOKEN
        self.base_url = "https://api.github.com"
        self.session = create_session_with_retries()
        self.logger = setup_logging(__name__)
        
        # Set up authentication headers
        self.headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'application/vnd.github.v3+json'
        }
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
        
        self.session.headers.update(self.headers)
    
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
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated request to GitHub API with rate limiting"""
        try:
            response = self.session.get(url, params=params, timeout=TIMEOUT)
            
            # Handle rate limiting
            if response.status_code == 403 and 'rate limit' in response.text.lower():
                self.logger.warning("Rate limit hit, waiting...")
                rate_limit_handler(response)
                response = self.session.get(url, params=params, timeout=TIMEOUT)
            
            response.raise_for_status()
            time.sleep(REQUEST_DELAY)
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            return None
    
    def _get_paginated_data(self, url: str, params: Optional[Dict] = None, 
                          max_pages: int = 10) -> List[Dict]:
        """Get all pages of data from paginated endpoint"""
        all_data = []
        page = 1
        params = params or {}
        
        while page <= max_pages:
            params['page'] = page
            params['per_page'] = 100
            
            data = self._make_request(url, params)
            if not data:
                break
                
            if isinstance(data, list):
                if not data:  # Empty page
                    break
                all_data.extend(data)
            else:
                # Handle search API format
                if 'items' in data:
                    if not data['items']:
                        break
                    all_data.extend(data['items'])
                else:
                    all_data.append(data)
                    break
            
            page += 1
            
        return all_data
    
    def get_user_profile(self, username: str) -> Optional[Dict]:
        """Get user or organization profile information"""
        url = f"{self.base_url}/users/{username}"
        profile = self._make_request(url)
        
        if profile:
            self.logger.info(f"Retrieved profile for {username}")
            
            # Add additional metadata
            profile['scraped_at'] = datetime.now().isoformat()
            profile['account_type'] = profile.get('type', 'User').lower()
            
        return profile
    
    def get_user_repositories(self, username: str, repo_type: str = 'all') -> List[Dict]:
        """Get user's repositories"""
        if repo_type == 'all':
            # Get both owned and contributed repos
            owned_repos = self._get_paginated_data(
                f"{self.base_url}/users/{username}/repos",
                {'type': 'all', 'sort': 'updated'}
            )
            return owned_repos
        else:
            return self._get_paginated_data(
                f"{self.base_url}/users/{username}/repos",
                {'type': repo_type, 'sort': 'updated'}
            )
    
    def get_user_activity(self, username: str, days_back: int = 30) -> List[Dict]:
        """Get user's recent public activity/events"""
        events = self._get_paginated_data(
            f"{self.base_url}/users/{username}/events/public",
            max_pages=5  # Limit to recent activity
        )
        
        # Filter by date if specified
        if days_back and events:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            filtered_events = []
            
            for event in events:
                event_date = datetime.fromisoformat(
                    event['created_at'].replace('Z', '+00:00')
                )
                if event_date.replace(tzinfo=None) >= cutoff_date:
                    filtered_events.append(event)
            
            events = filtered_events
        
        return events
    
    def get_user_followers(self, username: str) -> List[Dict]:
        """Get user's followers"""
        return self._get_paginated_data(
            f"{self.base_url}/users/{username}/followers"
        )
    
    def get_user_following(self, username: str) -> List[Dict]:
        """Get users that this user follows"""
        return self._get_paginated_data(
            f"{self.base_url}/users/{username}/following"
        )
    
    def get_user_organizations(self, username: str) -> List[Dict]:
        """Get user's public organization memberships"""
        return self._get_paginated_data(
            f"{self.base_url}/users/{username}/orgs"
        )
    
    def get_user_starred_repos(self, username: str) -> List[Dict]:
        """Get repositories starred by user"""
        return self._get_paginated_data(
            f"{self.base_url}/users/{username}/starred"
        )
    
    def get_user_gists(self, username: str) -> List[Dict]:
        """Get user's public gists"""
        return self._get_paginated_data(
            f"{self.base_url}/users/{username}/gists"
        )
    
    def get_organization_members(self, org_name: str) -> List[Dict]:
        """Get organization members (if public)"""
        return self._get_paginated_data(
            f"{self.base_url}/orgs/{org_name}/members"
        )
    
    def get_organization_repos(self, org_name: str) -> List[Dict]:
        """Get organization repositories"""
        return self._get_paginated_data(
            f"{self.base_url}/orgs/{org_name}/repos",
            {'sort': 'updated'}
        )
    
    def get_contribution_stats(self, username: str) -> Dict:
        """Get contribution statistics (limited by API)"""
        # Note: GitHub doesn't provide detailed contribution stats via API
        # This gets basic repository statistics
        repos = self.get_user_repositories(username)
        
        stats = {
            'total_repos': len(repos),
            'total_stars': sum(repo.get('stargazers_count', 0) for repo in repos),
            'total_forks': sum(repo.get('forks_count', 0) for repo in repos),
            'languages': {},
            'repo_types': {'public': 0, 'private': 0, 'fork': 0}
        }
        
        for repo in repos:
            # Count languages
            if repo.get('language'):
                lang = repo['language']
                stats['languages'][lang] = stats['languages'].get(lang, 0) + 1
            
            # Count repo types
            if repo.get('private'):
                stats['repo_types']['private'] += 1
            else:
                stats['repo_types']['public'] += 1
                
            if repo.get('fork'):
                stats['repo_types']['fork'] += 1
        
        return stats
    
    def scrape_user_comprehensive(self, username: str, include_activity: bool = True,
                                activity_days: int = 30) -> Dict[str, Any]:
        """Scrape comprehensive user data"""
        self.logger.info(f"Starting comprehensive scrape for user: {username}")
        
        data = {
            'username': username,
            'scraped_at': datetime.now().isoformat(),
            'profile': None,
            'repositories': [],
            'followers': [],
            'following': [],
            'organizations': [],
            'starred_repos': [],
            'gists': [],
            'activity': [],
            'contribution_stats': {},
            'scrape_metadata': {
                'include_activity': include_activity,
                'activity_days': activity_days if include_activity else 0
            }
        }
        
        # Get profile
        self.logger.info("Fetching profile...")
        data['profile'] = self.get_user_profile(username)
        
        if not data['profile']:
            self.logger.error(f"Could not fetch profile for {username}")
            return data
        
        account_type = data['profile'].get('type', 'User').lower()
        
        # Get repositories
        self.logger.info("Fetching repositories...")
        data['repositories'] = self.get_user_repositories(username)
        
        # Get social connections
        self.logger.info("Fetching followers...")
        data['followers'] = self.get_user_followers(username)
        
        self.logger.info("Fetching following...")
        data['following'] = self.get_user_following(username)
        
        # Get organizations
        self.logger.info("Fetching organizations...")
        data['organizations'] = self.get_user_organizations(username)
        
        # Get starred repositories
        self.logger.info("Fetching starred repositories...")
        data['starred_repos'] = self.get_user_starred_repos(username)
        
        # Get gists
        self.logger.info("Fetching gists...")
        data['gists'] = self.get_user_gists(username)
        
        # Get activity if requested
        if include_activity:
            self.logger.info(f"Fetching activity (last {activity_days} days)...")
            data['activity'] = self.get_user_activity(username, activity_days)
        
        # Get contribution statistics
        self.logger.info("Calculating contribution statistics...")
        data['contribution_stats'] = self.get_contribution_stats(username)
        
        # If it's an organization, get additional org data
        if account_type == 'organization':
            self.logger.info("Fetching organization members...")
            data['members'] = self.get_organization_members(username)
        
        self.logger.info(f"Comprehensive scrape completed for {username}")
        return data
    
    def scrape_multiple_users(self, usernames: List[str], **kwargs) -> Dict[str, Any]:
        """Scrape multiple users"""
        results = {}
        
        for username in usernames:
            self.logger.info(f"Scraping user {username} ({usernames.index(username) + 1}/{len(usernames)})")
            results[username] = self.scrape_user_comprehensive(username, **kwargs)
            
        return {
            'scraped_at': datetime.now().isoformat(),
            'total_users': len(usernames),
            'users': results
        }


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='GitHub User/Organization Scraper')
    parser.add_argument('username', help='GitHub username or organization name')
    parser.add_argument('--token', help='GitHub API token')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--format', choices=['json', 'csv'], default='json',
                       help='Output format')
    parser.add_argument('--no-activity', action='store_true',
                       help='Skip activity/events data')
    parser.add_argument('--activity-days', type=int, default=30,
                       help='Days of activity to fetch (default: 30)')
    parser.add_argument('--multiple', nargs='+',
                       help='Scrape multiple users (space-separated)')
    parser.add_argument('--profile-only', action='store_true',
                       help='Only fetch profile information')
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = GitHubUserScraper(token=args.token)
    
    try:
        if args.multiple:
            # Scrape multiple users
            usernames = args.multiple
            data = scraper.scrape_multiple_users(
                usernames,
                include_activity=not args.no_activity,
                activity_days=args.activity_days
            )
            filename = f"github_users_{'_'.join(usernames[:3])}"
        elif args.profile_only:
            # Profile only
            data = scraper.get_user_profile(args.username)
            filename = f"github_profile_{args.username}"
        else:
            # Single comprehensive scrape
            data = scraper.scrape_user_comprehensive(
                args.username,
                include_activity=not args.no_activity,
                activity_days=args.activity_days
            )
            filename = f"github_user_{args.username}"
        
        # Save data
        output_path = args.output or f"{filename}.{args.format}"
        save_data(data, output_path, format_type=args.format)
        
        print(f"Data saved to: {output_path}")
        
        # Print summary
        if isinstance(data, dict):
            if 'users' in data:
                print(f"Scraped {data['total_users']} users")
            elif 'profile' in data:
                profile = data['profile']
                print(f"User: {profile.get('login', 'Unknown')}")
                print(f"Name: {profile.get('name', 'N/A')}")
                print(f"Type: {profile.get('type', 'Unknown')}")
                print(f"Repositories: {len(data.get('repositories', []))}")
                print(f"Followers: {len(data.get('followers', []))}")
                print(f"Following: {len(data.get('following', []))}")
            else:
                print(f"Profile data for: {data.get('login', args.username)}")
    
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during scraping: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()