# Linear Integration Examples - Quick Start Guide

## Overview

This directory contains comprehensive examples demonstrating how to use the Linear integration with all scrapers in the research-scrapers package. The examples show real-world usage patterns for automatic task creation from scraper results.

## Prerequisites

1. **Linear API Key**: Get your API key from [Linear Settings → API → Personal API Keys](https://linear.app/settings/api)
2. **Python 3.8+**: Ensure you have Python 3.8 or higher installed
3. **Dependencies**: Install required packages

```bash
# Install core dependencies
pip install -r requirements.txt

# Optional: Install Linear-specific enhancements
pip install -r requirements-linear.txt
```

## Setup

### 1. Set Environment Variables

```bash
# Required
export LINEAR_API_KEY="lin_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Optional
export LINEAR_TEAM_KEY="RES"  # Your team key (default: "RES")
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"  # For higher GitHub API rate limits
```

### 2. Verify Setup

```bash
# Test your Linear connection
python -c "
from research_scrapers.linear import LinearClient
client = LinearClient()
teams = client.get_teams()
print(f'Connected! Found {len(teams)} teams.')
for team in teams:
    print(f'  - {team.name} ({team.key})')
"
```

## Running Examples

### Run All Examples

```bash
cd examples
python linear_integration_examples.py
```

### Run Specific Examples

```bash
# Run only examples 1, 3, and 5
RUN_EXAMPLES=1,3,5 python linear_integration_examples.py
```

### Configure Team Key

```bash
# Use a different Linear team
LINEAR_TEAM_KEY="ENG" python linear_integration_examples.py
```

## Example Descriptions

### Example 1: Basic GitHub Integration
**What it does**: Demonstrates basic GitHub repository scraping and Linear issue creation.
**Use case**: Quick repository analysis and tracking.
**Run time**: ~10 seconds

```bash
RUN_EXAMPLES=1 python linear_integration_examples.py
```

### Example 2: Multi-Scraper Analysis
**What it does**: Combines multiple GitHub scrapers (repo, user, issues) into one comprehensive issue.
**Use case**: Deep-dive repository ecosystem analysis.
**Run time**: ~30 seconds

```bash
RUN_EXAMPLES=2 python linear_integration_examples.py
```

### Example 3: ArXiv Research Tracking
**What it does**: Creates Linear issues for academic paper tracking and literature review.
**Use case**: Research paper discovery and review management.
**Run time**: ~15 seconds

```bash
RUN_EXAMPLES=3 python linear_integration_examples.py
```

### Example 4: Stack Overflow Trend Analysis
**What it does**: Analyzes Stack Overflow questions and creates trend reports in Linear.
**Use case**: Community sentiment and technology trend monitoring.
**Run time**: ~20 seconds

```bash
RUN_EXAMPLES=4 python linear_integration_examples.py
```

### Example 5: Patent Landscape Analysis
**What it does**: Searches patents and creates competitive intelligence reports.
**Use case**: IP landscape monitoring and competitor analysis.
**Run time**: ~25 seconds

```bash
RUN_EXAMPLES=5 python linear_integration_examples.py
```

### Example 6: Batch Processing Workflow
**What it does**: Processes multiple repositories in batches with progress tracking.
**Use case**: Large-scale repository analysis and comparison.
**Run time**: ~2 minutes

```bash
RUN_EXAMPLES=6 python linear_integration_examples.py
```

### Example 7: Workflow Automation
**What it does**: Demonstrates CI/CD integration patterns with environment-based config.
**Use case**: Automated research workflows in GitHub Actions.
**Run time**: ~15 seconds

```bash
# Simulate GitHub Actions environment
GITHUB_RUN_ID="12345" \
RESEARCH_TARGETS="facebook/react,microsoft/vscode" \
RUN_EXAMPLES=7 python linear_integration_examples.py
```

### Example 8: Error Handling and Retry
**What it does**: Shows robust error handling patterns with retry logic.
**Use case**: Production-ready implementations with fault tolerance.
**Run time**: ~20 seconds

```bash
RUN_EXAMPLES=8 python linear_integration_examples.py
```

### Example 9: Custom Formatting
**What it does**: Demonstrates custom formatters for specialized content types.
**Use case**: Tailored report formats for specific research needs.
**Run time**: ~10 seconds

```bash
RUN_EXAMPLES=9 python linear_integration_examples.py
```

## Common Usage Patterns

### Basic Issue Creation

```python
from research_scrapers.linear import LinearClient
from research_scrapers.github_scraper import GitHubScraper

# Initialize
linear = LinearClient()
github = GitHubScraper()

# Scrape and create issue
repo_data = github.scrape_repository("facebook", "react")
issue = linear.create_issue_from_scraper_results(
    team_key="RES",
    scraper_results={"github_repo": repo_data},
    run_id="analysis-001"
)

print(f"Created: {issue.url}")
```

### Batch Processing

```python
repos = [("facebook", "react"), ("microsoft", "vscode")]

for owner, repo in repos:
    data = github.scraper_repository(owner, repo)
    issue = linear.create_issue_from_scraper_results(
        team_key="RES",
        scraper_results={"github_repo": data},
        run_id=f"batch-{owner}-{repo}"
    )
    print(f"Created: {issue.identifier}")
```

### Adding Comments

```python
# Create initial issue
issue = linear.create_issue_from_scraper_results(...)

# Add follow-up comment
comment_id = linear.add_comment(
    issue.id,
    "## Additional Analysis\n\nNew findings..."
)
```

### Error Handling

```python
from research_scrapers.linear import LinearError, LinearRateLimitError

try:
    issue = linear.create_issue_from_scraper_results(...)
except LinearRateLimitError:
    print("Rate limit hit, waiting...")
    time.sleep(60)
    # Retry...
except LinearError as e:
    print(f"Linear API error: {e}")
```

## GitHub Actions Integration

Example workflow file (`.github/workflows/research.yml`):

```yaml
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
      
      - name: Run research scrapers
        env:
          LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
          LINEAR_TEAM_KEY: ${{ secrets.LINEAR_TEAM_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python examples/linear_integration_examples.py
```

## Troubleshooting

### Issue: "LINEAR_API_KEY environment variable is required"

**Solution**: Set your Linear API key
```bash
export LINEAR_API_KEY="lin_api_xxx"
```

### Issue: "Team with key 'XXX' not found"

**Solution**: Check available teams
```python
from research_scrapers.linear import LinearClient
client = LinearClient()
teams = client.get_teams()
for team in teams:
    print(f"{team.name}: {team.key}")
```

### Issue: Rate limit exceeded

**Solution**: Implement delays between requests
```python
import time
time.sleep(1)  # Wait 1 second between requests
```

### Issue: Authentication failed

**Solutions**:
1. Check API key is correct and not expired
2. Verify API key has required permissions
3. Test connection with simple query

```python
client = LinearClient()
try:
    teams = client.get_teams()
    print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")
```

## Best Practices

1. **Use Context Managers**: Always use `with` statements for automatic cleanup
   ```python
   with LinearClient() as linear:
       issue = linear.create_issue_from_scraper_results(...)
   ```

2. **Implement Retry Logic**: Add exponential backoff for production use
   ```python
   @retry_with_backoff(max_retries=3, base_delay=1)
   def create_issue():
       return linear.create_issue_from_scraper_results(...)
   ```

3. **Validate Data**: Check scraper results before creating issues
   ```python
   if not scraper_results:
       raise ValueError("No data to process")
   ```

4. **Use Meaningful Run IDs**: Create descriptive identifiers
   ```python
   run_id = f"github-analysis-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
   ```

5. **Monitor Rate Limits**: Check remaining quota periodically
   ```python
   status = linear.get_rate_limit_status()
   if status['remaining'] < 10:
       time.sleep(60)  # Wait before continuing
   ```

## Additional Resources

- [Linear Integration Guide](../src/research_scrapers/linear/INTEGRATION_GUIDE.md) - Comprehensive documentation
- [Linear API Documentation](https://developers.linear.app/) - Official API reference
- [Research Scrapers Documentation](../README.md) - Main package documentation

## Support

For issues or questions:

1. Check the [Integration Guide](../src/research_scrapers/linear/INTEGRATION_GUIDE.md)
2. Review example code in `linear_integration_examples.py`
3. Search existing issues in the repository
4. Create a new issue with:
   - Example code that reproduces the problem
   - Error messages and logs
   - Environment details (Python version, OS, etc.)

## Contributing

To add new examples:

1. Add your example function to `linear_integration_examples.py`
2. Follow the existing naming convention: `example_N_description()`
3. Include comprehensive docstrings
4. Add error handling
5. Update this README with example description
6. Test thoroughly before submitting PR

## License

These examples are part of the research-scrapers package and follow the same license terms.