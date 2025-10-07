# Linear Integration Guide

## Overview

The Linear integration for research-scrapers provides seamless automatic task creation from scraper results. When your scrapers complete their work, the integration automatically creates Linear issues with formatted results, making it easy to track research findings and follow up on discoveries.

## Features

- **Automatic Task Creation**: Creates Linear issues from scraper results
- **Rich Formatting**: Converts raw scraper data into well-formatted markdown
- **Multi-Scraper Support**: Works with GitHub, ArXiv, Stack Overflow, and Patent scrapers
- **Flexible Configuration**: Supports different teams, priorities, and workflows
- **Error Handling**: Robust error handling with retry logic
- **Rate Limiting**: Respects Linear API rate limits

## Quick Start

### 1. Setup Linear API Access

First, obtain a Linear API key:

1. Go to Linear Settings → API → Personal API Keys
2. Create a new API key with appropriate permissions
3. Set the environment variable:

```bash
export LINEAR_API_KEY="lin_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 2. Basic Usage

```python
from research_scrapers.linear import LinearClient
from research_scrapers.github_scraper import GitHubScraper

# Initialize clients
linear_client = LinearClient()
github_scraper = GitHubScraper()

# Scrape some data
repo_data = github_scraper.scrape_repository("facebook", "react")

# Create Linear issue from results
issue = linear_client.create_issue_from_scraper_results(
    team_key="RES",  # Your Linear team key
    scraper_results={"github_repo": repo_data},
    run_id="manual-001",
    title_prefix="Research: React Repository Analysis"
)

print(f"Created issue: {issue.identifier} - {issue.title}")
```

### 3. Automated Workflow Integration

For GitHub Actions workflows, use the convenience function:

```python
from pathlib import Path
from research_scrapers.linear.client import create_issue_from_artifacts

# Create issue from artifacts directory (typically in CI/CD)
issue = create_issue_from_artifacts(
    artifacts_dir=Path("./artifacts"),
    team_key="RES",
    run_id=os.environ.get("GITHUB_RUN_ID", "unknown"),
    workflow_url=f"https://github.com/{repo}/actions/runs/{run_id}"
)
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `LINEAR_API_KEY` | Linear API key | Yes |
| `LINEAR_TEAM_KEY` | Default team key (optional) | No |
| `LINEAR_DEFAULT_PRIORITY` | Default issue priority (0-4) | No |

### Team Configuration

Get your team key from Linear:

```python
# List all available teams
teams = linear_client.get_teams()
for team in teams:
    print(f"Team: {team.name} (Key: {team.key})")
```

### Workflow States

Configure issue states based on your team's workflow:

```python
# Get workflow states for a team
team = linear_client.get_team_by_key("RES")
states = linear_client.get_workflow_states(team.id)

for state in states:
    print(f"State: {state.name} (Type: {state.type})")
```

## Scraper Integration

### GitHub Scraper

The Linear integration supports all GitHub scraper operations:

```python
from research_scrapers.github_scraper import GitHubScraper
from research_scrapers.linear import LinearClient

scraper = GitHubScraper(token="ghp_xxx")
linear = LinearClient()

# Repository analysis
repo_data = scraper.scrape_repository("microsoft", "vscode")
user_data = scraper.scrape_user("gaearon")
issues_data = scraper.scrape_issues("facebook", "react", limit=50)

# Combine results
scraper_results = {
    "github_repo": repo_data,
    "github_user": user_data,
    "github_issues": issues_data
}

# Create comprehensive issue
issue = linear.create_issue_from_scraper_results(
    team_key="RES",
    scraper_results=scraper_results,
    run_id="github-analysis-001"
)
```

### ArXiv Scraper

```python
from research_scrapers.arxiv_scraper import ArxivScraper

scraper = ArxivScraper()
papers = scraper.search_papers("machine learning", max_results=20)

issue = linear.create_issue_from_scraper_results(
    team_key="RES",
    scraper_results={"arxiv": papers},
    run_id="arxiv-ml-001",
    title_prefix="Literature Review"
)
```

### Stack Overflow Scraper

```python
from research_scrapers.stackoverflow_scraper import StackOverflowScraper

scraper = StackOverflowScraper()
questions = scraper.search_questions("python machine learning", limit=30)

issue = linear.create_issue_from_scraper_results(
    team_key="RES",
    scraper_results={"stackoverflow": questions},
    run_id="so-python-ml-001"
)
```

### Patent Scraper

```python
from research_scrapers.patent_scraper import PatentScraper

scraper = PatentScraper()
patents = scraper.search_patents("artificial intelligence", limit=25)

issue = linear.create_issue_from_scraper_results(
    team_key="RES",
    scraper_results={"patent": patents},
    run_id="patent-ai-001",
    title_prefix="Patent Analysis"
)
```

## Advanced Usage

### Custom Formatting

Create custom formatters for specific use cases:

```python
from research_scrapers.linear.formatters import LinearResultFormatter

class CustomFormatter(LinearResultFormatter):
    @staticmethod
    def format_custom_data(data):
        # Your custom formatting logic
        return f"**Custom Data**: {data}"

# Use custom formatter
formatter = CustomFormatter()
markdown = formatter.format_scraper_results(
    scraper_results,
    run_id="custom-001"
)

# Create issue with custom description
issue = linear.create_issue(
    team_id=team.id,
    title="Custom Analysis Results",
    description=markdown
)
```

### Batch Processing

Process multiple scraper results in batches:

```python
from research_scrapers.batch_processor import BatchProcessor
from research_scrapers.linear import LinearClient

batch_processor = BatchProcessor()
linear = LinearClient()

# Define batch job
def create_linear_issues(results_batch):
    for i, results in enumerate(results_batch):
        issue = linear.create_issue_from_scraper_results(
            team_key="RES",
            scraper_results=results,
            run_id=f"batch-{i:03d}"
        )
        yield issue

# Process in batches
results_list = [...]  # Your scraper results
issues = list(batch_processor.process_batch(
    results_list,
    create_linear_issues,
    batch_size=5
))
```

### Issue Updates

Update existing issues with new results:

```python
# Update existing issue
updated_issue = linear.update_issue_with_results(
    issue_id="existing-issue-id",
    scraper_results=new_results,
    run_id="update-001",
    append_to_description=True  # Append to existing description
)

# Add comment to existing issue
comment_id = linear.add_comment(
    issue_id="existing-issue-id",
    body="## Additional Findings\n\nNew research data..."
)
```

### Workflow Automation

Integrate with GitHub Actions for automated research workflows:

```yaml
# .github/workflows/research.yml
name: Automated Research

on:
  schedule:
    - cron: '0 9 * * 1'  # Weekly on Monday
  workflow_dispatch:

jobs:
  research:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-linear.txt
      
      - name: Run scrapers
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
        run: |
          python scripts/automated_research.py
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: research-results
          path: artifacts/
```

## Error Handling

The Linear integration includes comprehensive error handling:

```python
from research_scrapers.linear import LinearError, LinearRateLimitError

try:
    issue = linear.create_issue_from_scraper_results(
        team_key="INVALID",
        scraper_results=results,
        run_id="test-001"
    )
except LinearRateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    # Wait and retry
    time.sleep(60)
except LinearError as e:
    print(f"Linear API error: {e}")
    # Handle error appropriately
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Best Practices

### 1. Use Context Managers

Always use context managers to ensure proper cleanup:

```python
with LinearClient() as linear:
    issue = linear.create_issue_from_scraper_results(...)
    # Client automatically closed
```

### 2. Implement Retry Logic

For production workflows, implement retry logic:

```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay * (2 ** attempt))
            return None
        return wrapper
    return decorator

@retry_on_failure(max_retries=3)
def create_issue_with_retry(linear, **kwargs):
    return linear.create_issue_from_scraper_results(**kwargs)
```

### 3. Use Meaningful Run IDs

Create descriptive run IDs for better tracking:

```python
import datetime

run_id = f"github-analysis-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
```

### 4. Validate Data Before Creating Issues

```python
def validate_scraper_results(results):
    if not results:
        raise ValueError("No scraper results provided")
    
    for scraper_type, data in results.items():
        if not data:
            print(f"Warning: No data for {scraper_type}")
    
    return True

# Use validation
if validate_scraper_results(scraper_results):
    issue = linear.create_issue_from_scraper_results(...)
```

### 5. Monitor Rate Limits

```python
# Check rate limits before making requests
rate_status = linear.get_rate_limit_status()
if rate_status['remaining'] < 10:
    print("Rate limit low, waiting...")
    time.sleep(60)
```

## Troubleshooting

### Common Issues

1. **Authentication Error**
   ```
   LinearAuthError: Authentication failed
   ```
   - Check that `LINEAR_API_KEY` is set correctly
   - Verify the API key has necessary permissions

2. **Team Not Found**
   ```
   LinearError: Team with key 'XXX' not found
   ```
   - List available teams: `linear.get_teams()`
   - Check team key spelling and case

3. **Rate Limit Exceeded**
   ```
   LinearRateLimitError: Rate limit exceeded
   ```
   - Implement exponential backoff
   - Reduce request frequency
   - Use batch processing

4. **Invalid Data Format**
   ```
   ValidationError: Invalid repository data
   ```
   - Check scraper output format
   - Verify data is not empty or corrupted

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('research_scrapers.linear')
logger.setLevel(logging.DEBUG)
```

### Testing Connection

Test your Linear connection:

```python
try:
    linear = LinearClient()
    teams = linear.get_teams()
    print(f"Successfully connected. Found {len(teams)} teams.")
except Exception as e:
    print(f"Connection failed: {e}")
```

## API Reference

### LinearClient

Main client class for Linear integration.

#### Methods

- `create_issue_from_scraper_results()` - Create issue from scraper results
- `create_issue()` - Create a new issue
- `update_issue()` - Update existing issue
- `add_comment()` - Add comment to issue
- `get_teams()` - List available teams
- `get_workflow_states()` - Get team workflow states

### LinearResultFormatter

Formats scraper results for Linear display.

#### Methods

- `format_scraper_results()` - Format complete results
- `format_github_repository()` - Format GitHub repo data
- `format_arxiv_papers()` - Format ArXiv papers
- `format_stackoverflow_questions()` - Format SO questions
- `format_patent_data()` - Format patent data

## Examples Repository

See the `examples/linear_integration_examples.py` file for comprehensive examples of all integration patterns and use cases.

## Support

For issues and questions:

1. Check this guide and the examples
2. Review the Linear API documentation
3. Open an issue in the research-scrapers repository
4. Check the troubleshooting section above

## Contributing

To contribute to the Linear integration:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## License

This integration is part of the research-scrapers package and follows the same license terms.