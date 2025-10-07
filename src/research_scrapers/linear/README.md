# Linear Integration Module

This module provides a production-ready Linear API client for the research-scrapers package, enabling automatic task creation and management from scraper results.

## Features

- **Comprehensive GraphQL Operations**: Full support for Linear's GraphQL API
- **Robust Error Handling**: Custom exceptions for different error types
- **Rate Limiting**: Built-in rate limiting with exponential backoff
- **Authentication Management**: Secure API key handling
- **Issue Management**: Create, update, and retrieve Linear issues
- **Comment System**: Add comments to issues with markdown support
- **Workflow State Management**: Handle Linear workflow states and transitions
- **Multi-Scraper Support**: Format results from all scrapers (GitHub, ArXiv, Stack Overflow, Patent)
- **Automatic Task Creation**: Create Linear tasks directly from scraper artifacts

## Quick Start

### Basic Usage

```python
from research_scrapers.linear import LinearClient

# Initialize client (uses LINEAR_API_KEY environment variable)
client = LinearClient()

# Or provide API key directly
client = LinearClient(api_key="lin_api_xxx")

# Create an issue
issue = client.create_issue(
    team_id="team_123",
    title="Research Task",
    description="Investigate machine learning trends",
    priority=2  # High priority
)

# Add a comment
client.add_comment(issue.id, "Found interesting papers on this topic")

# Update issue state
states = client.get_workflow_states(issue.team.id)
done_state = next(s for s in states if s.name.lower() == "done")
client.update_issue(issue.id, state_id=done_state.id)
```

### Integration with Scrapers

```python
from research_scrapers.linear import create_issue_from_artifacts
from pathlib import Path

# Create Linear issue from scraper artifacts
issue = create_issue_from_artifacts(
    artifacts_dir=Path("./artifacts"),
    team_key="RES",  # Team key instead of ID
    run_id="12345",
    workflow_url="https://github.com/user/repo/actions/runs/12345"
)

print(f"Created issue: {issue.identifier}")
```

### Context Manager Usage

```python
with LinearClient() as client:
    teams = client.get_teams()
    for team in teams:
        print(f"Team: {team.name} ({team.key})")
```

## API Reference

### LinearClient

The main client class for interacting with Linear's API.

#### Constructor

```python
LinearClient(
    api_key: Optional[str] = None,
    base_url: str = "https://api.linear.app/graphql",
    rate_limit: float = 50.0,
    timeout: int = 30,
    max_retries: int = 3
)
```

#### Core Methods

- `execute_query(query, variables=None)` - Execute GraphQL queries
- `get_teams(refresh_cache=False)` - Get all accessible teams
- `get_team_by_key(team_key)` - Get team by key (e.g., "RES")
- `get_workflow_states(team_id)` - Get workflow states for a team
- `get_issue(issue_id)` - Get issue details
- `create_issue(team_id, title, ...)` - Create a new issue
- `update_issue(issue_id, ...)` - Update an existing issue
- `add_comment(issue_id, body)` - Add comment to an issue

#### Scraper Integration Methods

- `format_scraper_results_for_linear(results, run_id, workflow_url=None)` - Format scraper results as markdown
- `create_issue_from_scraper_results(team_key, results, run_id, ...)` - Create issue from scraper results
- `update_issue_with_results(issue_id, results, run_id, ...)` - Update issue with new results

### Data Classes

#### LinearIssue
```python
@dataclass
class LinearIssue:
    id: str
    identifier: str  # e.g., "RES-123"
    title: str
    description: Optional[str]
    state: LinearWorkflowState
    team: LinearTeam
    priority: int
    created_at: datetime
    updated_at: datetime
    url: str
```

#### LinearTeam
```python
@dataclass
class LinearTeam:
    id: str
    name: str
    key: str  # e.g., "RES", "ENG"
```

#### LinearWorkflowState
```python
@dataclass
class LinearWorkflowState:
    id: str
    name: str  # e.g., "Backlog", "In Progress", "Done"
    type: str
    position: float
```

### Enums

#### IssueState
```python
class IssueState(Enum):
    BACKLOG = "Backlog"
    TODO = "Todo"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    DONE = "Done"
    CANCELED = "Canceled"
```

#### IssuePriority
```python
class IssuePriority(Enum):
    NO_PRIORITY = 0
    URGENT = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
```

### Exception Classes

- `LinearError` - Base Linear API exception
- `LinearRateLimitError` - Rate limit exceeded
- `LinearAuthError` - Authentication failed
- `LinearValidationError` - Data validation failed

## Configuration

### Environment Variables

- `LINEAR_API_KEY` - Your Linear API key (required)

### API Key Setup

1. Go to Linear Settings → API
2. Create a new Personal API Key
3. Set the `LINEAR_API_KEY` environment variable:
   ```bash
   export LINEAR_API_KEY="lin_api_your_key_here"
   ```

## Scraper Result Formatting

The client automatically formats results from all supported scrapers:

### GitHub Repository
- Repository metadata (name, description, stars, forks)
- Language and topics
- License information
- Issue counts

### GitHub Issues
- Issue list with titles, numbers, states
- Labels and authors
- Pagination for large result sets

### GitHub Users
- Profile information (name, bio, location)
- Statistics (followers, repos, etc.)
- Company and contact info

### ArXiv Papers
- Paper titles and authors
- Publication dates and categories
- Automatic author list truncation

### Stack Overflow Questions
- Question titles and scores
- Tags and answer counts
- View statistics

### Patents
- Patent titles and numbers
- Inventor and assignee information
- Filing and grant dates

## Integration Examples

### GitHub Actions Workflow

```yaml
- name: Update Linear Task
  env:
    LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
  run: |
    python -c "
    from research_scrapers.linear import create_issue_from_artifacts
    from pathlib import Path
    
    issue = create_issue_from_artifacts(
        artifacts_dir=Path('./artifacts'),
        team_key='RES',
        run_id='${{ github.run_id }}',
        workflow_url='${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}'
    )
    
    if issue:
        print(f'Created Linear issue: {issue.identifier}')
        print(f'URL: {issue.url}')
    "
```

### Custom Script Integration

```python
#!/usr/bin/env python3
import json
from pathlib import Path
from research_scrapers.linear import LinearClient

def main():
    # Load scraper results
    with open('github_results.json') as f:
        github_data = json.load(f)
    
    # Create Linear client
    with LinearClient() as client:
        # Get team
        team = client.get_team_by_key("RES")
        if not team:
            print("Team 'RES' not found")
            return
        
        # Create issue
        issue = client.create_issue_from_scraper_results(
            team_key="RES",
            scraper_results={"github_repo": github_data},
            run_id="manual-001"
        )
        
        print(f"Created issue: {issue.identifier}")
        print(f"URL: {issue.url}")

if __name__ == "__main__":
    main()
```

## Error Handling

The client provides comprehensive error handling:

```python
from research_scrapers.linear import (
    LinearClient, 
    LinearError, 
    LinearRateLimitError, 
    LinearAuthError
)

try:
    client = LinearClient()
    issue = client.create_issue(team_id="invalid", title="Test")
except LinearAuthError as e:
    print(f"Authentication failed: {e}")
except LinearRateLimitError as e:
    print(f"Rate limit exceeded: {e}")
except LinearError as e:
    print(f"Linear API error: {e}")
```

## Rate Limiting

The client automatically handles Linear's rate limits:

- Default: 50 requests per second
- Exponential backoff on rate limit errors
- Automatic retry with configurable attempts
- Rate limit status monitoring

## Caching

The client caches frequently accessed data:

- Team information
- Workflow states
- Automatic cache refresh options

## Best Practices

1. **Use Environment Variables**: Store API keys in environment variables
2. **Context Managers**: Use `with` statements for automatic cleanup
3. **Error Handling**: Always wrap API calls in try-catch blocks
4. **Team Keys**: Use team keys instead of IDs for better maintainability
5. **Batch Operations**: Group related operations to minimize API calls
6. **Rate Limiting**: Be mindful of rate limits in high-frequency scenarios

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify `LINEAR_API_KEY` is set correctly
   - Check API key permissions in Linear settings

2. **Team Not Found**
   - Ensure team key exists and is accessible
   - Use `get_teams()` to list available teams

3. **Rate Limit Errors**
   - Reduce request frequency
   - Increase retry delays
   - Use caching to minimize API calls

4. **GraphQL Errors**
   - Check query syntax and variables
   - Verify required fields are provided
   - Review Linear API documentation

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

client = LinearClient()
# Debug information will be logged
```

## Contributing

When contributing to this module:

1. Follow the existing code style and patterns
2. Add comprehensive error handling
3. Include docstrings for all public methods
4. Add unit tests for new functionality
5. Update this README for new features

## License

This module is part of the research-scrapers package and follows the same license terms.