#!/usr/bin/env python3
"""
Example script demonstrating GitHubScraper usage.

This script shows how to use the GitHubScraper class to scrape
various types of data from GitHub's API.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import directly to avoid scraper.py issue
import importlib.util
spec = importlib.util.spec_from_file_location(
    "github_scraper", 
    Path(__file__).parent.parent / "src" / "research_scrapers" / "github_scraper.py"
)
github_scraper_module = importlib.util.module_from_spec(spec)
sys.modules["github_scraper"] = github_scraper_module
spec.loader.exec_module(github_scraper_module)
GitHubScraper = github_scraper_module.GitHubScraper

from utils import setup_logging

# Setup logging
logger = setup_logging(level='INFO')


def main():
    """Demonstrate GitHubScraper functionality."""
    
    logger.info("Starting GitHubScraper example")
    
    # Initialize scraper (uses GITHUB_TOKEN env var if available)
    with GitHubScraper() as scraper:
        
        # Example 1: Scrape a repository
        logger.info("Example 1: Scraping repository...")
        try:
            repo = scraper.scrape_repository("facebook", "react")
            print(f"\n📦 Repository: {repo['full_name']}")
            print(f"   Description: {repo['description']}")
            print(f"   ⭐ Stars: {repo['stargazers_count']:,}")
            print(f"   🔱 Forks: {repo['forks_count']:,}")
            print(f"   Language: {repo['language']}")
            print(f"   License: {repo['license']['name'] if repo['license'] else 'None'}")
        except Exception as e:
            logger.error(f"Failed to scrape repository: {e}")
        
        # Example 2: Scrape a user
        logger.info("\nExample 2: Scraping user...")
        try:
            user = scraper.scrape_user("torvalds")
            print(f"\n👤 User: {user['login']}")
            print(f"   Name: {user['name']}")
            print(f"   Bio: {user['bio']}")
            print(f"   Public Repos: {user['public_repos']}")
            print(f"   Followers: {user['followers']:,}")
            print(f"   Following: {user['following']:,}")
        except Exception as e:
            logger.error(f"Failed to scrape user: {e}")
        
        # Example 3: Search repositories
        logger.info("\nExample 3: Searching repositories...")
        try:
            results = scraper.search_repositories(
                "machine learning language:python stars:>1000",
                sort="stars",
                limit=5
            )
            print(f"\n🔍 Search Results (top 5):")
            for i, repo in enumerate(results, 1):
                print(f"   {i}. {repo['full_name']}")
                print(f"      ⭐ {repo['stargazers_count']:,} stars")
                print(f"      {repo['description'][:80]}...")
        except Exception as e:
            logger.error(f"Failed to search repositories: {e}")
        
        # Example 4: Get issues
        logger.info("\nExample 4: Fetching issues...")
        try:
            issues = scraper.scrape_issues("python", "cpython", state="open", limit=5)
            print(f"\n🐛 Open Issues (first 5):")
            for issue in issues:
                print(f"   #{issue['number']}: {issue['title']}")
                print(f"      Created: {issue['created_at']}")
        except Exception as e:
            logger.error(f"Failed to fetch issues: {e}")
        
        # Example 5: Check rate limit
        logger.info("\nExample 5: Checking rate limit...")
        try:
            status = scraper.get_rate_limit_status()
            core = status['resources']['core']
            search = status['resources']['search']
            
            print(f"\n📊 Rate Limit Status:")
            print(f"   Core API: {core['remaining']}/{core['limit']} remaining")
            print(f"   Search API: {search['remaining']}/{search['limit']} remaining")
        except Exception as e:
            logger.error(f"Failed to check rate limit: {e}")
    
    logger.info("\nExample completed successfully!")


if __name__ == '__main__':
    main()
