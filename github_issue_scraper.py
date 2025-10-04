#!/usr/bin/env python3
"""
GitHub Issue Scraper

Scrapes GitHub issues, pull requests, and discussions including:
- Issue metadata (title, body, labels, assignees)
- Comments and reactions
- Pull request details and reviews
- Discussion threads and replies
- Timeline events

Usage:
    python github_issue_scraper.py owner/repo --type issues [--state open] [--output file.json]
    python github_issue_scraper.py owner/repo --type pulls --labels bug,enhancement
    python github_issue_scraper.py owner/repo --type discussions --max-items 50
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


class GitHubIssueScraper:
    """Scraper for GitHub issues, pull requests, and discussions."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the issue scraper.
        
        Args:
            token: GitHub personal access token (optional)
        """
        self.client = GitHubAPIClient(token)
        self.rate_limiter = RateLimiter()
    
    def scrape_issues(self, owner: str, repo: str,
                     state: str = 'all',
                     labels: Optional[List[str]] = None,
                     assignee: Optional[str] = None,
                     max_items: int = 100,
                     include_comments: bool = True) -> Dict[str, Any]:
        """
        Scrape repository issues.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state ('open', 'closed', 'all')
            labels: Filter by labels
            assignee: Filter by assignee
            max_items: Maximum number of issues to fetch
            include_comments: Whether to include comments
            
        Returns:
            Dictionary containing issues data
        """
        logger.info(f"Scraping issues from {owner}/{repo}")
        
        data = {
            'scraped_at': datetime.utcnow().isoformat(),
            'repository': f"{owner}/{repo}",
            'type': 'issues',
            'filters': {
                'state': state,
                'labels': labels,
                'assignee': assignee
            },
            'issues': [],
            'total_count': 0
        }
        
        # Build query parameters
        params = {
            'state': state,
            'per_page': min(max_items, 100),
            'sort': 'updated',
            'direction': 'desc'
        }
        
        if labels:
            params['labels'] = ','.join(labels)
        if assignee:
            params['assignee'] = assignee
        
        # Fetch issues
        issues = self._fetch_paginated_data(
            f"{self.client.base_url}/repos/{owner}/{repo}/issues",
            params, max_items
        )
        
        # Filter out pull requests (GitHub API includes PRs in issues endpoint)
        issues = [issue for issue in issues if 'pull_request' not in issue]
        
        data['total_count'] = len(issues)
        
        # Process each issue
        for issue_data in issues:
            issue = self._process_issue(issue_data, owner, repo, include_comments)
            data['issues'].append(issue)
        
        logger.info(f"Scraped {len(data['issues'])} issues")
        return data
    
    def scrape_pull_requests(self, owner: str, repo: str,
                           state: str = 'all',
                           base: Optional[str] = None,
                           head: Optional[str] = None,
                           max_items: int = 100,
                           include_reviews: bool = True) -> Dict[str, Any]:
        """
        Scrape repository pull requests.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state ('open', 'closed', 'all')
            base: Filter by base branch
            head: Filter by head branch
            max_items: Maximum number of PRs to fetch
            include_reviews: Whether to include reviews
            
        Returns:
            Dictionary containing pull requests data
        """
        logger.info(f"Scraping pull requests from {owner}/{repo}")
        
        data = {
            'scraped_at': datetime.utcnow().isoformat(),
            'repository': f"{owner}/{repo}",
            'type': 'pull_requests',
            'filters': {
                'state': state,
                'base': base,
                'head': head
            },
            'pull_requests': [],
            'total_count': 0
        }
        
        # Build query parameters
        params = {
            'state': state,
            'per_page': min(max_items, 100),
            'sort': 'updated',
            'direction': 'desc'
        }
        
        if base:
            params['base'] = base
        if head:
            params['head'] = head
        
        # Fetch pull requests
        pulls = self._fetch_paginated_data(
            f"{self.client.base_url}/repos/{owner}/{repo}/pulls",
            params, max_items
        )
        
        data['total_count'] = len(pulls)
        
        # Process each pull request
        for pr_data in pulls:
            pr = self._process_pull_request(pr_data, owner, repo, include_reviews)
            data['pull_requests'].append(pr)
        
        logger.info(f"Scraped {len(data['pull_requests'])} pull requests")
        return data
    
    def scrape_discussions(self, owner: str, repo: str,
                         category: Optional[str] = None,
                         max_items: int = 100,
                         include_comments: bool = True) -> Dict[str, Any]:
        """
        Scrape repository discussions using GraphQL API.
        
        Args:
            owner: Repository owner
            repo: Repository name
            category: Filter by discussion category
            max_items: Maximum number of discussions to fetch
            include_comments: Whether to include comments
            
        Returns:
            Dictionary containing discussions data
        """
        logger.info(f"Scraping discussions from {owner}/{repo}")
        
        data = {
            'scraped_at': datetime.utcnow().isoformat(),
            'repository': f"{owner}/{repo}",
            'type': 'discussions',
            'filters': {
                'category': category
            },
            'discussions': [],
            'total_count': 0
        }
        
        # GraphQL query for discussions
        query = """
        query($owner: String!, $repo: String!, $first: Int!, $after: String) {
          repository(owner: $owner, name: $repo) {
            discussions(first: $first, after: $after, orderBy: {field: UPDATED_AT, direction: DESC}) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                id
                number
                title
                body
                bodyText
                url
                createdAt
                updatedAt
                author {
                  login
                  url
                }
                category {
                  name
                  slug
                }
                labels(first: 10) {
                  nodes {
                    name
                    color
                  }
                }
                reactions {
                  totalCount
                }
                comments {
                  totalCount
                }
                upvoteCount
                locked
                closed
              }
            }
          }
        }
        """
        
        variables = {
            'owner': owner,
            'repo': repo,
            'first': min(max_items, 100)
        }
        
        try:
            discussions = self._fetch_graphql_paginated(
                query, variables, max_items, ['repository', 'discussions']
            )
            
            # Filter by category if specified
            if category:
                discussions = [
                    d for d in discussions 
                    if d.get('category', {}).get('slug') == category
                ]
            
            data['total_count'] = len(discussions)
            
            # Process each discussion
            for discussion_data in discussions:
                discussion = self._process_discussion(
                    discussion_data, owner, repo, include_comments
                )
                data['discussions'].append(discussion)
            
        except Exception as e:
            logger.warning(f"Failed to fetch discussions (may not be enabled): {e}")
        
        logger.info(f"Scraped {len(data['discussions'])} discussions")
        return data
    
    def _process_issue(self, issue_data: Dict[str, Any], owner: str, repo: str,
                      include_comments: bool = True) -> Dict[str, Any]:
        """Process a single issue."""
        issue = {
            'number': issue_data.get('number'),
            'title': issue_data.get('title'),
            'body': issue_data.get('body'),
            'state': issue_data.get('state'),
            'url': issue_data.get('html_url'),
            'created_at': issue_data.get('created_at'),
            'updated_at': issue_data.get('updated_at'),
            'closed_at': issue_data.get('closed_at'),
            'author': {
                'username': issue_data.get('user', {}).get('login'),
                'url': issue_data.get('user', {}).get('html_url')
            },
            'assignees': [
                {
                    'username': assignee.get('login'),
                    'url': assignee.get('html_url')
                }
                for assignee in issue_data.get('assignees', [])
            ],
            'labels': [
                {
                    'name': label.get('name'),
                    'color': label.get('color'),
                    'description': label.get('description')
                }
                for label in issue_data.get('labels', [])
            ],
            'milestone': None,
            'reactions': {
                'total_count': issue_data.get('reactions', {}).get('total_count', 0)
            },
            'comments_count': issue_data.get('comments', 0),
            'comments': []
        }
        
        # Add milestone if present
        if issue_data.get('milestone'):
            issue['milestone'] = {
                'title': issue_data['milestone'].get('title'),
                'description': issue_data['milestone'].get('description'),
                'state': issue_data['milestone'].get('state'),
                'due_on': issue_data['milestone'].get('due_on')
            }
        
        # Fetch comments if requested
        if include_comments and issue['comments_count'] > 0:
            issue['comments'] = self._get_issue_comments(
                owner, repo, issue['number']
            )
        
        return issue
    
    def _process_pull_request(self, pr_data: Dict[str, Any], owner: str, repo: str,
                            include_reviews: bool = True) -> Dict[str, Any]:
        """Process a single pull request."""
        pr = {
            'number': pr_data.get('number'),
            'title': pr_data.get('title'),
            'body': pr_data.get('body'),
            'state': pr_data.get('state'),
            'url': pr_data.get('html_url'),
            'created_at': pr_data.get('created_at'),
            'updated_at': pr_data.get('updated_at'),
            'closed_at': pr_data.get('closed_at'),
            'merged_at': pr_data.get('merged_at'),
            'merged': pr_data.get('merged', False),
            'draft': pr_data.get('draft', False),
            'author': {
                'username': pr_data.get('user', {}).get('login'),
                'url': pr_data.get('user', {}).get('html_url')
            },
            'head': {
                'ref': pr_data.get('head', {}).get('ref'),
                'sha': pr_data.get('head', {}).get('sha'),
                'repo': pr_data.get('head', {}).get('repo', {}).get('full_name')
            },
            'base': {
                'ref': pr_data.get('base', {}).get('ref'),
                'sha': pr_data.get('base', {}).get('sha')
            },
            'assignees': [
                {
                    'username': assignee.get('login'),
                    'url': assignee.get('html_url')
                }
                for assignee in pr_data.get('assignees', [])
            ],
            'requested_reviewers': [
                {
                    'username': reviewer.get('login'),
                    'url': reviewer.get('html_url')
                }
                for reviewer in pr_data.get('requested_reviewers', [])
            ],
            'labels': [
                {
                    'name': label.get('name'),
                    'color': label.get('color')
                }
                for label in pr_data.get('labels', [])
            ],
            'additions': pr_data.get('additions', 0),
            'deletions': pr_data.get('deletions', 0),
            'changed_files': pr_data.get('changed_files', 0),
            'comments_count': pr_data.get('comments', 0),
            'review_comments_count': pr_data.get('review_comments', 0),
            'commits_count': pr_data.get('commits', 0),
            'reviews': []
        }
        
        # Fetch reviews if requested
        if include_reviews:
            pr['reviews'] = self._get_pr_reviews(owner, repo, pr['number'])
        
        return pr
    
    def _process_discussion(self, discussion_data: Dict[str, Any], owner: str, repo: str,
                          include_comments: bool = True) -> Dict[str, Any]:
        """Process a single discussion."""
        discussion = {
            'number': discussion_data.get('number'),
            'title': discussion_data.get('title'),
            'body': discussion_data.get('body'),
            'body_text': discussion_data.get('bodyText'),
            'url': discussion_data.get('url'),
            'created_at': discussion_data.get('createdAt'),
            'updated_at': discussion_data.get('updatedAt'),
            'author': {
                'username': discussion_data.get('author', {}).get('login'),
                'url': discussion_data.get('author', {}).get('url')
            },
            'category': {
                'name': discussion_data.get('category', {}).get('name'),
                'slug': discussion_data.get('category', {}).get('slug')
            },
            'labels': [
                {
                    'name': label.get('name'),
                    'color': label.get('color')
                }
                for label in discussion_data.get('labels', {}).get('nodes', [])
            ],
            'upvotes': discussion_data.get('upvoteCount', 0),
            'reactions_count': discussion_data.get('reactions', {}).get('totalCount', 0),
            'comments_count': discussion_data.get('comments', {}).get('totalCount', 0),
            'locked': discussion_data.get('locked', False),
            'closed': discussion_data.get('closed', False),
            'comments': []
        }
        
        return discussion
    
    def _get_issue_comments(self, owner: str, repo: str, issue_number: int) -> List[Dict[str, Any]]:
        """Get comments for an issue."""
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.client.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        comments_data = self._fetch_paginated_data(url, {'per_page': 100}, 500)
        
        comments = []
        for comment in comments_data:
            comments.append({
                'id': comment.get('id'),
                'body': comment.get('body'),
                'created_at': comment.get('created_at'),
                'updated_at': comment.get('updated_at'),
                'author': {
                    'username': comment.get('user', {}).get('login'),
                    'url': comment.get('user', {}).get('html_url')
                },
                'reactions': {
                    'total_count': comment.get('reactions', {}).get('total_count', 0)
                }
            })
        
        return comments
    
    def _get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """Get reviews for a pull request."""
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.client.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        reviews_data = self._fetch_paginated_data(url, {'per_page': 100}, 200)
        
        reviews = []
        for review in reviews_data:
            reviews.append({
                'id': review.get('id'),
                'state': review.get('state'),
                'body': review.get('body'),
                'submitted_at': review.get('submitted_at'),
                'author': {
                    'username': review.get('user', {}).get('login'),
                    'url': review.get('user', {}).get('html_url')
                }
            })
        
        return reviews
    
    def _fetch_paginated_data(self, url: str, params: Dict[str, Any], max_items: int) -> List[Dict[str, Any]]:
        """Fetch paginated data from REST API."""
        items = []
        page = 1
        per_page = params.get('per_page', 100)
        
        while len(items) < max_items:
            self.rate_limiter.wait_if_needed()
            
            current_params = params.copy()
            current_params['page'] = page
            current_params['per_page'] = min(per_page, max_items - len(items))
            
            response = self.client.get(url, params=current_params)
            data = response.json()
            
            if not data:
                break
            
            items.extend(data)
            
            if len(data) < per_page:
                break
            
            page += 1
        
        return items[:max_items]
    
    def _fetch_graphql_paginated(self, query: str, variables: Dict[str, Any], 
                               max_items: int, path: List[str]) -> List[Dict[str, Any]]:
        """Fetch paginated data from GraphQL API."""
        items = []
        has_next_page = True
        cursor = None
        
        while has_next_page and len(items) < max_items:
            self.rate_limiter.wait_if_needed()
            
            current_variables = variables.copy()
            current_variables['first'] = min(100, max_items - len(items))
            if cursor:
                current_variables['after'] = cursor
            
            response = self.client.post(
                f"{self.client.base_url}/graphql",
                json={'query': query, 'variables': current_variables}
            )
            
            data = response.json()
            
            if 'errors' in data:
                raise Exception(f"GraphQL errors: {data['errors']}")
            
            # Navigate to the data using the path
            current_data = data['data']
            for key in path:
                current_data = current_data[key]
            
            items.extend(current_data['nodes'])
            
            page_info = current_data['pageInfo']
            has_next_page = page_info['hasNextPage']
            cursor = page_info.get('endCursor')
        
        return items[:max_items]


def main():
    """Command-line interface for the issue scraper."""
    parser = argparse.ArgumentParser(
        description='Scrape GitHub issues, pull requests, and discussions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python github_issue_scraper.py microsoft/vscode --type issues --state open
  python github_issue_scraper.py facebook/react --type pulls --max-items 50
  python github_issue_scraper.py torvalds/linux --type issues --labels bug,regression
  python github_issue_scraper.py owner/repo --type discussions --category general
        """
    )
    
    parser.add_argument('repository', help='Repository in format owner/repo')
    parser.add_argument('--type', choices=['issues', 'pulls', 'discussions'], 
                       default='issues', help='Type of items to scrape')
    parser.add_argument('--state', choices=['open', 'closed', 'all'], 
                       default='all', help='Item state filter')
    parser.add_argument('--labels', help='Comma-separated list of labels to filter by')
    parser.add_argument('--assignee', help='Filter by assignee username')
    parser.add_argument('--category', help='Discussion category filter')
    parser.add_argument('--max-items', type=int, default=100,
                       help='Maximum number of items to fetch')
    parser.add_argument('--no-comments', action='store_true',
                       help='Skip fetching comments/reviews')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    parser.add_argument('--token', help='GitHub personal access token')
    
    args = parser.parse_args()
    
    # Parse repository
    if '/' not in args.repository:
        parser.error('Repository must be in format owner/repo')
    
    owner, repo = args.repository.split('/', 1)
    
    # Parse labels
    labels = args.labels.split(',') if args.labels else None
    
    # Use token from args or config
    token = args.token or GITHUB_TOKEN
    
    # Create scraper and fetch data
    scraper = GitHubIssueScraper(token)
    
    try:
        if args.type == 'issues':
            data = scraper.scrape_issues(
                owner, repo,
                state=args.state,
                labels=labels,
                assignee=args.assignee,
                max_items=args.max_items,
                include_comments=not args.no_comments
            )
        elif args.type == 'pulls':
            data = scraper.scrape_pull_requests(
                owner, repo,
                state=args.state,
                max_items=args.max_items,
                include_reviews=not args.no_comments
            )
        elif args.type == 'discussions':
            data = scraper.scrape_discussions(
                owner, repo,
                category=args.category,
                max_items=args.max_items,
                include_comments=not args.no_comments
            )
        
        # Save or print data
        if args.output:
            save_json(data, args.output)
            print(f"Data saved to {args.output}")
        else:
            print(json.dumps(data, indent=2))
        
        # Print summary
        logger.info("\n=== Scraping Summary ===")
        logger.info(f"Repository: {data['repository']}")
        logger.info(f"Type: {data['type']}")
        logger.info(f"Total items: {data['total_count']}")
        
    except Exception as e:
        logger.error(f"Error scraping {args.type}: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
