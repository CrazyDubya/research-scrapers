# Linear Integration Documentation

## Overview

The research-scrapers package includes a comprehensive Linear integration that automatically creates tasks from scraper results. This integration enables seamless tracking of research findings, automated workflow creation, and team collaboration through Linear's project management platform.

## Key Features

✨ **Automatic Task Creation** - Convert scraper results into formatted Linear issues  
🎨 **Rich Formatting** - Beautiful markdown formatting for all scraper types  
🔄 **Multi-Scraper Support** - Works with GitHub, ArXiv, Stack Overflow, and Patent scrapers  
⚡ **Rate Limiting** - Built-in rate limiting and retry logic  
🛡️ **Error Handling** - Robust error handling with graceful degradation  
🔧 **Flexible Configuration** - Support for multiple teams, priorities, and workflows  

## Quick Start

### 1. Installation

The Linear integration is included in the research-scrapers package. No additional dependencies required!

```bash
pip install -r requirements.txt
```

### 2. Configuration

Set your Linear API key:

```bash
export LINEAR_API_KEY="lin_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

Get your API key from [Linear Settings → API → Personal API Keys](https://linear.app/settings/api)

### 3. Basic Usage

```python
from research_scrapers.linear import LinearClient
from research_scrapers.github_scraper import GitHubScraper

# Initialize clients
linear = LinearClient()
github = GitHubScraper()

# Scrape data
repo_data = github.scrape_repository("facebook", "react")

# Create Linear issue
issue = linear.create_issue_from_scraper_results(
    team_key="RES",  # Your team key
    scraper_results={"github_repo": repo_data},
    run_id="analysis-001"
)

print(f"Created issue: {issue.identifier}")
print(f"URL: {issue.url}")
```

## Documentation

### 📚 Comprehensive Guides

1. **[Integration Guide](../src/research_scrapers/linear/INTEGRATION_GUIDE.md)**
   - Complete integration documentation
   - Configuration options
   - API reference
   - Best practices
   - Troubleshooting

2. **[Examples Quick Start](../examples/LINEAR_EXAMPLES_README.md)**
   - Getting started guide
   - Example descriptions
   - Common patterns
   - GitHub Actions integration

3. **[Example Code](../examples/linear_integration_examples.py)**
   - 9 comprehensive examples
   - Real-world usage patterns
   - Error handling demonstrations
   - Custom formatting examples

## Supported Scrapers

### GitHub Scraper

```python
# Repository analysis
repo_data = github.scrape_repository("owner", "repo")
issue = linear.create_issue_from_scraper_results(
    team_key="RES",
    scraper_results={"github_repo": repo_data},
    run_id="github-001"
)
```

**Formatted Output Includes:**
- Repository statistics (stars, forks, watchers)
- Language and technology stack
- License information
- Issue and PR counts
- Recent activity metrics

### ArXiv Scraper

```python
# Research paper tracking
papers = arxiv.search_papers("machine learning", max_results=20)
issue = linear.create_issue_from_scraper_results(
    team_key="RES",
    scraper_results={"arxiv": papers},
    run_id="arxiv-001",
    title_prefix="Literature Review"
)
```

**Formatted Output Includes:**
- Paper titles and authors
- Publication dates
- Categories and classifications
- Abstracts
- ArXiv IDs with direct links

### Stack Overflow Scraper

```python
# Community trend analysis
questions = stackoverflow.search_questions("python machine learning", limit=30)
issue = linear.create_issue_from_scraper_results(
    team_key="RES",
    scraper_results={"stackoverflow": questions},
    run_id="so-001"
)
```

**Formatted Output Includes:**
- Question titles and scores
- Tags and categories
- Answer counts and status
- View counts
- Author information

### Patent Scraper

```python
# IP landscape analysis
patents = patent.search_patents("artificial intelligence", limit=25)
issue = linear.create_issue_from_scraper_results(
    team_key="RES",
    scraper_results={"patent": patents},
    run_id="patent-001"
)
```

**Formatted Output Includes:**
- Patent numbers and titles
- Inventors and assignees
- Filing and grant dates
- Patent abstracts
- Google Patents links

## Advanced Features

### Multi-Scraper Analysis

Combine multiple scrapers in a single issue:

```python
scraper_results = {
    "github_repo": github.scrape_repository("owner", "repo"),
    "github_issues": github.scrape_issues("owner", "repo", limit=50),
    "stackoverflow": stackoverflow.search_questions("repo_topic", limit=30)
}

issue = linear.create_issue_from_scraper_results(
    team_key="RES",
    scraper_results=scraper_results,
    run_id="comprehensive-001",
    title_prefix="Comprehensive Analysis"
)
```

### Batch Processing

Process multiple targets efficiently:

```python
repositories = [
    ("facebook", "react"),
    ("microsoft", "typescript"),
    ("google", "tensorflow")
]

for owner, repo in repositories:
    data = github.scrape_repository(owner, repo)
    issue = linear.create_issue_from_scraper_results(
        team_key="RES",
        scraper_results={"github_repo": data},
        run_id=f"batch-{owner}-{repo}"
    )
    print(f"Created: {issue.identifier}")
```

### Workflow Automation

Integrate with CI/CD pipelines:

```python
import os
from pathlib import Path
from research_scrapers.linear.client import create_issue_from_artifacts

# Create issue from artifacts directory (GitHub Actions)
issue = create_issue_from_artifacts(
    artifacts_dir=Path("./artifacts"),
    team_key=os.environ.get("LINEAR_TEAM_KEY", "RES"),
    run_id=os.environ.get("GITHUB_RUN_ID", "unknown"),
    workflow_url=f"https://github.com/{repo}/actions/runs/{run_id}"
)
```

### Custom Formatting

Create custom formatters for specialized needs:

```python
from research_scrapers.linear.formatters import LinearResultFormatter

class CustomFormatter(LinearResultFormatter):
    @staticmethod
    def format_custom_data(data):
        # Your formatting logic
        return "**Custom**: " + str(data)

# Use custom formatter
formatter = CustomFormatter()
markdown = formatter.format_scraper_results(results, "custom-001")
```

## GitHub Actions Integration

Example workflow for automated research:

```yaml
name: Weekly Research

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM
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
        run: pip install -r requirements.txt
      
      - name: Run research scrapers
        env:
          LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
          LINEAR_TEAM_KEY: ${{ secrets.LINEAR_TEAM_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python scripts/automated_research.py
```

## API Reference

### LinearClient

Main client for Linear integration.

#### Key Methods

- `create_issue_from_scraper_results()` - Create issue from scraper data
- `create_issue()` - Create a new Linear issue
- `update_issue()` - Update existing issue
- `add_comment()` - Add comment to issue
- `get_teams()` - List available teams
- `get_workflow_states()` - Get team workflow states

#### Example

```python
with LinearClient() as client:
    # Create issue
    issue = client.create_issue_from_scraper_results(
        team_key="RES",
        scraper_results=data,
        run_id="001",
        priority=2  # High priority
    )
    
    # Add comment
    client.add_comment(issue.id, "Additional notes...")
```

### LinearResultFormatter

Formats scraper results for Linear display.

#### Key Methods

- `format_scraper_results()` - Format complete results
- `format_github_repository()` - Format GitHub repo data
- `format_arxiv_papers()` - Format ArXiv papers
- `format_stackoverflow_questions()` - Format SO questions
- `format_patent_data()` - Format patent information

## Configuration Options

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `LINEAR_API_KEY` | Linear API key | Yes | - |
| `LINEAR_TEAM_KEY` | Default team key | No | - |
| `LINEAR_DEFAULT_PRIORITY` | Default issue priority (0-4) | No | 3 |
| `GITHUB_TOKEN` | GitHub token for higher rate limits | No | - |

### Issue Priorities

- **0** - No Priority
- **1** - Urgent
- **2** - High
- **3** - Medium (default)
- **4** - Low

## Best Practices

### 1. Use Context Managers

```python
with LinearClient() as linear:
    issue = linear.create_issue_from_scraper_results(...)
    # Automatic cleanup
```

### 2. Implement Retry Logic

```python
from functools import wraps
import time

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
        return wrapper
    return decorator
```

### 3. Validate Data

```python
if not scraper_results:
    raise ValueError("No scraper results to process")

for scraper_type, data in scraper_results.items():
    if not data:
        logger.warning(f"No data for {scraper_type}")
```

### 4. Monitor Rate Limits

```python
status = linear.get_rate_limit_status()
if status['remaining'] < 10:
    time.sleep(60)  # Wait before continuing
```

### 5. Use Meaningful Identifiers

```python
from datetime import datetime

run_id = f"github-analysis-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
```

## Troubleshooting

### Common Issues

#### Authentication Error

```
LinearAuthError: Authentication failed
```

**Solutions:**
- Verify `LINEAR_API_KEY` is set correctly
- Check API key has necessary permissions
- Test connection with simple query

#### Team Not Found

```
LinearError: Team with key 'XXX' not found
```

**Solutions:**
- List available teams: `linear.get_teams()`
- Check spelling and case sensitivity
- Verify team access permissions

#### Rate Limit Exceeded

```
LinearRateLimitError: Rate limit exceeded
```

**Solutions:**
- Implement exponential backoff
- Add delays between requests
- Use batch processing for multiple items

### Debug Mode

Enable detailed logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('research_scrapers.linear')
logger.setLevel(logging.DEBUG)
```

## Performance Tips

1. **Batch Similar Operations** - Group similar requests together
2. **Use Caching** - Cache team and workflow state data
3. **Implement Rate Limiting** - Respect API limits with delays
4. **Optimize Data** - Filter unnecessary data before formatting
5. **Async Processing** - Use async operations for large batches

## Examples

See [linear_integration_examples.py](../examples/linear_integration_examples.py) for:

- ✅ Basic GitHub integration
- ✅ Multi-scraper analysis
- ✅ ArXiv research tracking
- ✅ Stack Overflow trend analysis
- ✅ Patent landscape analysis
- ✅ Batch processing workflows
- ✅ CI/CD automation patterns
- ✅ Error handling and retry logic
- ✅ Custom formatting examples

## Support and Contributing

### Getting Help

1. Check the [Integration Guide](../src/research_scrapers/linear/INTEGRATION_GUIDE.md)
2. Review [example code](../examples/linear_integration_examples.py)
3. Search existing GitHub issues
4. Create a new issue with details

### Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## License

This integration is part of the research-scrapers package and follows the same license terms.

## Related Documentation

- [Main README](../README.md) - Package overview
- [Integration Guide](../src/research_scrapers/linear/INTEGRATION_GUIDE.md) - Detailed documentation
- [Examples Guide](../examples/LINEAR_EXAMPLES_README.md) - Getting started with examples
- [Linear API Docs](https://developers.linear.app/) - Official Linear API reference

---

**Ready to get started?** Check out the [Integration Guide](../src/research_scrapers/linear/INTEGRATION_GUIDE.md) and [Examples](../examples/linear_integration_examples.py)!