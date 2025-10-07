#!/usr/bin/env python3
"""
Linear Integration Examples

This module provides comprehensive examples of how to use the Linear integration
with all available scrapers in the research-scrapers package. These examples
demonstrate automatic task creation, result formatting, and workflow integration.

Author: Stephen Thompson
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from research_scrapers.linear import LinearClient, LinearError, LinearRateLimitError
from research_scrapers.github_scraper import GitHubScraper
from research_scrapers.stackoverflow_scraper import StackOverflowScraper
from research_scrapers.patent_scraper import PatentScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_1_basic_github_integration():
    """
    Example 1: Basic GitHub repository analysis with Linear task creation.
    
    This example shows how to:
    1. Scrape GitHub repository data
    2. Create a Linear issue with the results
    3. Handle basic error cases
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic GitHub Integration")
    print("="*60)
    
    try:
        # Initialize clients
        github_scraper = GitHubScraper()
        linear_client = LinearClient()
        
        # Scrape repository data
        print("Scraping React repository...")
        repo_data = github_scraper.scrape_repository("facebook", "react")
        
        # Create Linear issue
        print("Creating Linear issue...")
        issue = linear_client.create_issue_from_scraper_results(
            team_key="RES",  # Replace with your team key
            scraper_results={"github_repo": repo_data},
            run_id=f"example-1-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            title_prefix="GitHub Analysis"
        )
        
        print(f"✅ Created issue: {issue.identifier} - {issue.title}")
        print(f"   URL: {issue.url}")
        
    except LinearError as e:
        print(f"❌ Linear error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        # Clean up
        if 'github_scraper' in locals():
            github_scraper.close()
        if 'linear_client' in locals():
            linear_client.close()


def example_2_multi_scraper_analysis():
    """
    Example 2: Multi-scraper analysis with comprehensive Linear issue.
    
    This example demonstrates:
    1. Using multiple scrapers (GitHub repo, user, issues)
    2. Combining results into a single comprehensive issue
    3. Custom title and priority settings
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: Multi-Scraper Analysis")
    print("="*60)
    
    github_scraper = None
    linear_client = None
    
    try:
        # Initialize clients
        github_scraper = GitHubScraper()
        linear_client = LinearClient()
        
        # Scrape multiple data sources
        print("Scraping repository data...")
        repo_data = github_scraper.scrape_repository("microsoft", "vscode")
        
        print("Scraping user data...")
        user_data = github_scraper.scrape_user("microsoft")
        
        print("Scraping recent issues...")
        issues_data = github_scraper.scrape_issues("microsoft", "vscode", state="open", limit=25)
        
        # Combine all results
        scraper_results = {
            "github_repo": repo_data,
            "github_user": user_data,
            "github_issues": issues_data
        }
        
        # Create comprehensive Linear issue
        print("Creating comprehensive Linear issue...")
        issue = linear_client.create_issue_from_scraper_results(
            team_key="RES",  # Replace with your team key
            scraper_results=scraper_results,
            run_id=f"vscode-analysis-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            title_prefix="Comprehensive Analysis: VS Code",
            priority=2  # High priority
        )
        
        print(f"✅ Created comprehensive issue: {issue.identifier}")
        print(f"   Title: {issue.title}")
        print(f"   URL: {issue.url}")
        print(f"   Data sources: {len(scraper_results)} scrapers")
        
        # Add a follow-up comment
        print("Adding follow-up comment...")
        comment_id = linear_client.add_comment(
            issue.id,
            "## Analysis Notes\n\n"
            "This comprehensive analysis includes:\n"
            "- Repository metadata and statistics\n"
            "- Organization profile information\n"
            "- Recent open issues for trend analysis\n\n"
            "**Next Steps:**\n"
            "- [ ] Review issue trends\n"
            "- [ ] Analyze contributor patterns\n"
            "- [ ] Compare with competitor projects"
        )
        
        print(f"✅ Added follow-up comment: {comment_id}")
        
    except LinearRateLimitError as e:
        print(f"⚠️ Rate limit exceeded: {e}")
        print("Consider implementing retry logic with exponential backoff")
    except LinearError as e:
        print(f"❌ Linear error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        # Clean up
        if github_scraper:
            github_scraper.close()
        if linear_client:
            linear_client.close()


def example_3_arxiv_research_tracking():
    """
    Example 3: ArXiv research paper tracking.
    
    This example shows:
    1. Searching ArXiv for research papers
    2. Creating Linear issues for literature review tracking
    3. Using custom formatting for academic content
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: ArXiv Research Tracking")
    print("="*60)
    
    linear_client = None
    
    try:
        # Note: This is a mock example since ArxivScraper might not be fully implemented
        # In practice, you would use the actual ArxivScraper
        
        # Mock ArXiv data (replace with actual scraper)
        arxiv_papers = [
            {
                "title": "Attention Is All You Need",
                "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
                "published": "2017-06-12",
                "categories": ["cs.CL", "cs.AI"],
                "summary": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
                "id": "1706.03762"
            },
            {
                "title": "BERT: Pre-training of Deep Bidirectional Transformers",
                "authors": ["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee"],
                "published": "2018-10-11",
                "categories": ["cs.CL"],
                "summary": "We introduce a new language representation model called BERT...",
                "id": "1810.04805"
            }
        ]
        
        # Initialize Linear client
        linear_client = LinearClient()
        
        # Create Linear issue for literature review
        print("Creating literature review tracking issue...")
        issue = linear_client.create_issue_from_scraper_results(
            team_key="RES",  # Replace with your team key
            scraper_results={"arxiv": arxiv_papers},
            run_id=f"arxiv-transformers-{datetime.now().strftime('%Y%m%d')}",
            title_prefix="Literature Review: Transformer Models",
            priority=3  # Medium priority
        )
        
        print(f"✅ Created literature review issue: {issue.identifier}")
        print(f"   Found {len(arxiv_papers)} relevant papers")
        print(f"   URL: {issue.url}")
        
        # Add research methodology comment
        methodology_comment = """
## Research Methodology

**Search Query**: "transformer attention mechanism"
**Date Range**: 2017-2023
**Categories**: cs.CL, cs.AI, cs.LG

**Review Criteria**:
- [ ] Novelty of approach
- [ ] Experimental validation
- [ ] Reproducibility
- [ ] Impact on field

**Status**: Initial paper collection complete
**Next**: Detailed analysis and categorization
        """
        
        comment_id = linear_client.add_comment(issue.id, methodology_comment)
        print(f"✅ Added methodology comment: {comment_id}")
        
    except LinearError as e:
        print(f"❌ Linear error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        if linear_client:
            linear_client.close()


def example_4_stackoverflow_trend_analysis():
    """
    Example 4: Stack Overflow trend analysis.
    
    This example demonstrates:
    1. Scraping Stack Overflow questions
    2. Analyzing technology trends
    3. Creating tracking issues for community insights
    """
    print("\n" + "="*60)
    print("EXAMPLE 4: Stack Overflow Trend Analysis")
    print("="*60)
    
    stackoverflow_scraper = None
    linear_client = None
    
    try:
        # Initialize clients
        stackoverflow_scraper = StackOverflowScraper()
        linear_client = LinearClient()
        
        # Search for trending Python questions
        print("Searching Stack Overflow for Python ML questions...")
        questions = stackoverflow_scraper.search_questions(
            "python machine learning",
            limit=30
        )
        
        # Create trend analysis issue
        print("Creating trend analysis issue...")
        issue = linear_client.create_issue_from_scraper_results(
            team_key="RES",  # Replace with your team key
            scraper_results={"stackoverflow": questions},
            run_id=f"so-python-ml-{datetime.now().strftime('%Y%m%d')}",
            title_prefix="Community Trends: Python ML on Stack Overflow"
        )
        
        print(f"✅ Created trend analysis issue: {issue.identifier}")
        print(f"   Analyzed {len(questions)} questions")
        print(f"   URL: {issue.url}")
        
        # Analyze trends and add insights
        if questions:
            # Calculate basic statistics
            total_score = sum(q.get('score', 0) for q in questions)
            avg_score = total_score / len(questions) if questions else 0
            answered_count = sum(1 for q in questions if q.get('is_answered', False))
            answer_rate = (answered_count / len(questions)) * 100 if questions else 0
            
            # Extract popular tags
            all_tags = []
            for q in questions:
                all_tags.extend(q.get('tags', []))
            
            tag_counts = {}
            for tag in all_tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Create insights comment
            insights = f"""
## Trend Analysis Results

**Dataset**: {len(questions)} questions analyzed
**Average Score**: {avg_score:.1f}
**Answer Rate**: {answer_rate:.1f}%

### Popular Tags
{chr(10).join(f"- `{tag}` ({count} questions)" for tag, count in popular_tags)}

### Key Insights
- High answer rate indicates active community engagement
- Popular tags show current technology focus
- Score distribution reveals question quality trends

### Recommendations
- [ ] Monitor emerging tags for new technologies
- [ ] Track answer quality metrics
- [ ] Identify knowledge gaps in community
            """
            
            comment_id = linear_client.add_comment(issue.id, insights)
            print(f"✅ Added trend analysis insights: {comment_id}")
        
    except Exception as e:
        print(f"❌ Error in Stack Overflow analysis: {e}")
    finally:
        if stackoverflow_scraper:
            stackoverflow_scraper.close()
        if linear_client:
            linear_client.close()


def example_5_patent_landscape_analysis():
    """
    Example 5: Patent landscape analysis.
    
    This example shows:
    1. Patent search and analysis
    2. Competitive intelligence tracking
    3. IP landscape monitoring
    """
    print("\n" + "="*60)
    print("EXAMPLE 5: Patent Landscape Analysis")
    print("="*60)
    
    patent_scraper = None
    linear_client = None
    
    try:
        # Initialize clients
        patent_scraper = PatentScraper()
        linear_client = LinearClient()
        
        # Search for AI-related patents
        print("Searching for AI patents...")
        patents = patent_scraper.search_patents(
            "artificial intelligence machine learning",
            limit=20
        )
        
        # Create patent landscape issue
        print("Creating patent landscape analysis issue...")
        issue = linear_client.create_issue_from_scraper_results(
            team_key="RES",  # Replace with your team key
            scraper_results={"patent": patents},
            run_id=f"patent-ai-{datetime.now().strftime('%Y%m%d')}",
            title_prefix="IP Landscape: AI & Machine Learning Patents",
            priority=2  # High priority for IP analysis
        )
        
        print(f"✅ Created patent landscape issue: {issue.identifier}")
        print(f"   Analyzed {len(patents)} patents")
        print(f"   URL: {issue.url}")
        
        # Add competitive analysis
        if patents:
            # Analyze assignees (companies)
            assignees = {}
            for patent in patents:
                assignee = patent.get('assignee', 'Unknown')
                assignees[assignee] = assignees.get(assignee, 0) + 1
            
            top_assignees = sorted(assignees.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Analyze filing trends by year
            filing_years = {}
            for patent in patents:
                filing_date = patent.get('filing_date', '')
                if filing_date:
                    year = filing_date[:4]  # Extract year
                    filing_years[year] = filing_years.get(year, 0) + 1
            
            competitive_analysis = f"""
## Competitive Intelligence Analysis

**Dataset**: {len(patents)} patents analyzed
**Technology Focus**: Artificial Intelligence & Machine Learning

### Top Patent Holders
{chr(10).join(f"- **{assignee}**: {count} patents" for assignee, count in top_assignees)}

### Filing Trends by Year
{chr(10).join(f"- **{year}**: {count} patents" for year, count in sorted(filing_years.items(), reverse=True))}

### Strategic Insights
- Market leaders in AI patent filings
- Technology evolution trends
- Potential collaboration or licensing opportunities
- White space identification for innovation

### Action Items
- [ ] Deep dive analysis on top assignees
- [ ] Technology gap analysis
- [ ] Prior art search for our innovations
- [ ] Freedom to operate assessment
            """
            
            comment_id = linear_client.add_comment(issue.id, competitive_analysis)
            print(f"✅ Added competitive analysis: {comment_id}")
        
    except Exception as e:
        print(f"❌ Error in patent analysis: {e}")
    finally:
        if patent_scraper:
            patent_scraper.close()
        if linear_client:
            linear_client.close()


def example_6_batch_processing_workflow():
    """
    Example 6: Batch processing workflow for multiple repositories.
    
    This example demonstrates:
    1. Processing multiple targets in batches
    2. Error handling and retry logic
    3. Progress tracking and reporting
    """
    print("\n" + "="*60)
    print("EXAMPLE 6: Batch Processing Workflow")
    print("="*60)
    
    github_scraper = None
    linear_client = None
    
    try:
        # Define repositories to analyze
        repositories = [
            ("facebook", "react"),
            ("microsoft", "typescript"),
            ("google", "tensorflow"),
            ("pytorch", "pytorch"),
            ("huggingface", "transformers")
        ]
        
        # Initialize clients
        github_scraper = GitHubScraper()
        linear_client = LinearClient()
        
        print(f"Processing {len(repositories)} repositories...")
        
        successful_issues = []
        failed_repos = []
        
        for i, (owner, repo) in enumerate(repositories, 1):
            try:
                print(f"[{i}/{len(repositories)}] Processing {owner}/{repo}...")
                
                # Scrape repository data
                repo_data = github_scraper.scrape_repository(owner, repo)
                
                # Create individual issue for each repo
                issue = linear_client.create_issue_from_scraper_results(
                    team_key="RES",  # Replace with your team key
                    scraper_results={"github_repo": repo_data},
                    run_id=f"batch-{datetime.now().strftime('%Y%m%d')}-{i:02d}",
                    title_prefix=f"Repository Analysis: {owner}/{repo}"
                )
                
                successful_issues.append((owner, repo, issue))
                print(f"   ✅ Created issue: {issue.identifier}")
                
                # Rate limiting - be nice to APIs
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Failed to process {owner}/{repo}: {e}")
                failed_repos.append((owner, repo, str(e)))
        
        # Create summary issue
        print("\nCreating batch processing summary...")
        
        summary_data = {
            "batch_summary": {
                "total_repositories": len(repositories),
                "successful": len(successful_issues),
                "failed": len(failed_repos),
                "success_rate": (len(successful_issues) / len(repositories)) * 100,
                "processed_repos": [f"{owner}/{repo}" for owner, repo in repositories],
                "successful_issues": [
                    {
                        "repo": f"{owner}/{repo}",
                        "issue_id": issue.identifier,
                        "issue_url": issue.url
                    }
                    for owner, repo, issue in successful_issues
                ],
                "failed_repos": [
                    {
                        "repo": f"{owner}/{repo}",
                        "error": error
                    }
                    for owner, repo, error in failed_repos
                ]
            }
        }
        
        summary_issue = linear_client.create_issue_from_scraper_results(
            team_key="RES",  # Replace with your team key
            scraper_results=summary_data,
            run_id=f"batch-summary-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            title_prefix="Batch Processing Summary"
        )
        
        print(f"✅ Created summary issue: {summary_issue.identifier}")
        print(f"   Success rate: {len(successful_issues)}/{len(repositories)} repositories")
        print(f"   URL: {summary_issue.url}")
        
    except Exception as e:
        print(f"❌ Batch processing error: {e}")
    finally:
        if github_scraper:
            github_scraper.close()
        if linear_client:
            linear_client.close()


def example_7_workflow_automation():
    """
    Example 7: Automated workflow with environment-based configuration.
    
    This example shows:
    1. Environment-based configuration
    2. Automated workflow patterns
    3. CI/CD integration patterns
    """
    print("\n" + "="*60)
    print("EXAMPLE 7: Workflow Automation")
    print("="*60)
    
    try:
        # Environment-based configuration
        team_key = os.environ.get('LINEAR_TEAM_KEY', 'RES')
        github_token = os.environ.get('GITHUB_TOKEN')
        run_id = os.environ.get('GITHUB_RUN_ID', f"manual-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        workflow_url = os.environ.get('GITHUB_WORKFLOW_URL')
        
        print(f"Configuration:")
        print(f"  Team Key: {team_key}")
        print(f"  Run ID: {run_id}")
        print(f"  GitHub Token: {'✓' if github_token else '✗'}")
        print(f"  Workflow URL: {'✓' if workflow_url else '✗'}")
        
        # Simulate automated research workflow
        research_targets = os.environ.get('RESEARCH_TARGETS', 'facebook/react,microsoft/vscode').split(',')
        
        print(f"\nAutomated research targets: {research_targets}")
        
        with GitHubScraper(token=github_token) as github_scraper, LinearClient() as linear_client:
            all_results = {}
            
            for target in research_targets:
                if '/' in target:
                    owner, repo = target.strip().split('/', 1)
                    print(f"Analyzing {owner}/{repo}...")
                    
                    try:
                        repo_data = github_scraper.scrape_repository(owner, repo)
                        all_results[f"github_repo_{owner}_{repo}"] = repo_data
                    except Exception as e:
                        print(f"  ⚠️ Failed to analyze {owner}/{repo}: {e}")
            
            if all_results:
                # Create consolidated issue
                issue = linear_client.create_issue_from_scraper_results(
                    team_key=team_key,
                    scraper_results=all_results,
                    run_id=run_id,
                    workflow_url=workflow_url,
                    title_prefix="Automated Research Workflow"
                )
                
                print(f"✅ Created automated workflow issue: {issue.identifier}")
                print(f"   URL: {issue.url}")
                
                # Set environment variable for downstream steps
                if 'GITHUB_ENV' in os.environ:
                    with open(os.environ['GITHUB_ENV'], 'a') as f:
                        f.write(f"LINEAR_ISSUE_ID={issue.id}\n")
                        f.write(f"LINEAR_ISSUE_URL={issue.url}\n")
                
            else:
                print("⚠️ No results to process")
        
    except Exception as e:
        print(f"❌ Workflow automation error: {e}")


def example_8_error_handling_and_retry():
    """
    Example 8: Comprehensive error handling and retry logic.
    
    This example demonstrates:
    1. Robust error handling patterns
    2. Retry logic with exponential backoff
    3. Graceful degradation strategies
    """
    print("\n" + "="*60)
    print("EXAMPLE 8: Error Handling and Retry Logic")
    print("="*60)
    
    def retry_with_backoff(func, max_retries=3, base_delay=1):
        """Retry function with exponential backoff."""
        for attempt in range(max_retries):
            try:
                return func()
            except LinearRateLimitError as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"   Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                else:
                    raise
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"   Error: {e}, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                else:
                    raise
        
        return None
    
    github_scraper = None
    linear_client = None
    
    try:
        # Initialize clients with error handling
        print("Initializing clients with error handling...")
        
        try:
            github_scraper = GitHubScraper()
            print("  ✅ GitHub scraper initialized")
        except Exception as e:
            print(f"  ❌ GitHub scraper failed: {e}")
            return
        
        try:
            linear_client = LinearClient()
            print("  ✅ Linear client initialized")
        except LinearError as e:
            print(f"  ❌ Linear client failed: {e}")
            return
        
        # Test connection and permissions
        print("\nTesting connections...")
        
        try:
            teams = linear_client.get_teams()
            print(f"  ✅ Linear connection OK ({len(teams)} teams available)")
        except Exception as e:
            print(f"  ❌ Linear connection failed: {e}")
            return
        
        # Attempt scraping with retry logic
        print("\nAttempting repository scraping with retry logic...")
        
        def scrape_repo():
            return github_scraper.scrape_repository("facebook", "react")
        
        repo_data = retry_with_backoff(scrape_repo, max_retries=3, base_delay=2)
        
        if repo_data:
            print("  ✅ Repository data scraped successfully")
            
            # Attempt Linear issue creation with retry
            print("Creating Linear issue with retry logic...")
            
            def create_issue():
                return linear_client.create_issue_from_scraper_results(
                    team_key="RES",  # Replace with your team key
                    scraper_results={"github_repo": repo_data},
                    run_id=f"retry-example-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                    title_prefix="Error Handling Example"
                )
            
            issue = retry_with_backoff(create_issue, max_retries=3, base_delay=2)
            
            if issue:
                print(f"  ✅ Issue created successfully: {issue.identifier}")
            else:
                print("  ❌ Failed to create issue after retries")
        else:
            print("  ❌ Failed to scrape repository after retries")
    
    except KeyboardInterrupt:
        print("\n⚠️ Operation interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.exception("Detailed error information:")
    finally:
        # Ensure cleanup happens
        print("\nCleaning up resources...")
        if github_scraper:
            try:
                github_scraper.close()
                print("  ✅ GitHub scraper closed")
            except Exception as e:
                print(f"  ⚠️ Error closing GitHub scraper: {e}")
        
        if linear_client:
            try:
                linear_client.close()
                print("  ✅ Linear client closed")
            except Exception as e:
                print(f"  ⚠️ Error closing Linear client: {e}")


def example_9_custom_formatting():
    """
    Example 9: Custom result formatting for specific use cases.
    
    This example shows:
    1. Custom formatters for specialized content
    2. Template-based formatting
    3. Conditional formatting based on data
    """
    print("\n" + "="*60)
    print("EXAMPLE 9: Custom Formatting")
    print("="*60)
    
    from research_scrapers.linear.formatters import LinearResultFormatter
    
    class CustomResearchFormatter(LinearResultFormatter):
        """Custom formatter for research-specific content."""
        
        @staticmethod
        def format_research_summary(data: Dict[str, Any]) -> str:
            """Format a research summary with custom sections."""
            md = "# 🔬 Research Summary\n\n"
            
            # Executive summary
            md += "## Executive Summary\n\n"
            md += f"**Research Focus**: {data.get('focus', 'General Analysis')}\n"
            md += f"**Data Sources**: {len(data.get('sources', []))} sources analyzed\n"
            md += f"**Key Findings**: {len(data.get('findings', []))} insights identified\n\n"
            
            # Methodology
            md += "## Methodology\n\n"
            methodology = data.get('methodology', {})
            md += f"**Approach**: {methodology.get('approach', 'Systematic analysis')}\n"
            md += f"**Time Period**: {methodology.get('period', 'Current')}\n"
            md += f"**Scope**: {methodology.get('scope', 'Comprehensive')}\n\n"
            
            # Key findings
            findings = data.get('findings', [])
            if findings:
                md += "## Key Findings\n\n"
                for i, finding in enumerate(findings, 1):
                    md += f"{i}. **{finding.get('title', 'Finding')}**\n"
                    md += f"   {finding.get('description', 'No description')}\n"
                    if finding.get('impact'):
                        md += f"   *Impact*: {finding['impact']}\n"
                    md += "\n"
            
            # Recommendations
            recommendations = data.get('recommendations', [])
            if recommendations:
                md += "## Recommendations\n\n"
                for i, rec in enumerate(recommendations, 1):
                    md += f"{i}. {rec}\n"
                md += "\n"
            
            return md
    
    try:
        # Create custom research data
        research_data = {
            "focus": "Open Source AI Libraries Landscape",
            "sources": ["GitHub", "ArXiv", "Stack Overflow"],
            "methodology": {
                "approach": "Multi-source comparative analysis",
                "period": "2023-2024",
                "scope": "Top 50 repositories by stars and activity"
            },
            "findings": [
                {
                    "title": "Transformer Architecture Dominance",
                    "description": "85% of top ML libraries implement transformer-based models",
                    "impact": "High - shapes future development priorities"
                },
                {
                    "title": "Python Ecosystem Leadership",
                    "description": "Python remains the dominant language for AI/ML development",
                    "impact": "Medium - confirms existing technology choices"
                }
            ],
            "recommendations": [
                "Focus development efforts on transformer-compatible architectures",
                "Maintain Python-first development approach",
                "Monitor emerging frameworks for early adoption opportunities"
            ]
        }
        
        # Use custom formatter
        formatter = CustomResearchFormatter()
        custom_markdown = formatter.format_research_summary(research_data)
        
        print("Custom formatted content:")
        print("-" * 40)
        print(custom_markdown[:500] + "..." if len(custom_markdown) > 500 else custom_markdown)
        print("-" * 40)
        
        # Create Linear issue with custom formatting
        with LinearClient() as linear_client:
            # Create issue with custom description
            issue = linear_client.create_issue(
                team_id="your-team-id",  # Replace with actual team ID
                title="Custom Research Summary Example",
                description=custom_markdown,
                priority=2
            )
            
            print(f"✅ Created custom formatted issue: {issue.identifier}")
            print(f"   URL: {issue.url}")
    
    except Exception as e:
        print(f"❌ Custom formatting error: {e}")


def main():
    """
    Main function to run all examples.
    
    Set environment variables to customize behavior:
    - LINEAR_API_KEY: Your Linear API key (required)
    - LINEAR_TEAM_KEY: Your Linear team key (default: "RES")
    - GITHUB_TOKEN: GitHub personal access token (optional, for higher rate limits)
    - RUN_EXAMPLES: Comma-separated list of example numbers to run (default: all)
    """
    print("Linear Integration Examples")
    print("=" * 60)
    
    # Check required environment variables
    if not os.environ.get('LINEAR_API_KEY'):
        print("❌ LINEAR_API_KEY environment variable is required")
        print("   Get your API key from Linear Settings → API → Personal API Keys")
        return
    
    # Determine which examples to run
    run_examples = os.environ.get('RUN_EXAMPLES', '1,2,3,4,5,6,7,8,9').split(',')
    run_examples = [int(x.strip()) for x in run_examples if x.strip().isdigit()]
    
    print(f"Running examples: {run_examples}")
    print(f"Team key: {os.environ.get('LINEAR_TEAM_KEY', 'RES')} (set LINEAR_TEAM_KEY to change)")
    
    # Example functions mapping
    examples = {
        1: example_1_basic_github_integration,
        2: example_2_multi_scraper_analysis,
        3: example_3_arxiv_research_tracking,
        4: example_4_stackoverflow_trend_analysis,
        5: example_5_patent_landscape_analysis,
        6: example_6_batch_processing_workflow,
        7: example_7_workflow_automation,
        8: example_8_error_handling_and_retry,
        9: example_9_custom_formatting
    }
    
    # Run selected examples
    for example_num in run_examples:
        if example_num in examples:
            try:
                examples[example_num]()
            except KeyboardInterrupt:
                print(f"\n⚠️ Example {example_num} interrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Example {example_num} failed: {e}")
                logger.exception(f"Detailed error for example {example_num}:")
        else:
            print(f"\n⚠️ Example {example_num} not found")
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()