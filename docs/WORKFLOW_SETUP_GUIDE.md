# GitHub Actions Workflow Setup Guide

This guide covers the setup and usage of the production-ready GitHub Actions workflow for the research-scrapers repository.

## 🚀 Quick Start

The workflow `github-api-scraper-production.yml` provides three execution methods:

1. **Scheduled** - Runs daily at 2 AM UTC automatically
2. **Manual** - Triggered via GitHub Actions UI with custom parameters
3. **API/Webhook** - Triggered by external systems (Poke integration)

## 📋 Prerequisites

### Required Secrets

Set these secrets in your repository settings (`Settings > Secrets and variables > Actions`):

```bash
# Required
GITHUB_TOKEN          # GitHub Personal Access Token with repo access

# Optional (for notifications)
SMTP_USERNAME         # Email SMTP username
SMTP_PASSWORD         # Email SMTP password
SLACK_WEBHOOK_URL     # Slack webhook URL for notifications
```

### GitHub Token Setup

1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate a new token with these scopes:
   - `repo` (Full control of private repositories)
   - `read:org` (Read org and team membership)
   - `read:user` (Read user profile data)
3. Add the token as `GITHUB_TOKEN` secret in your repository

## 🔧 Configuration Options

### Manual Execution Parameters

When running manually via Actions tab, you can configure:

| Parameter | Description | Options | Default |
|-----------|-------------|---------|---------|
| `scraper_mode` | Type of scraping operation | repository, user, issues, pull_requests, organization, search_repos, search_users, search_code, batch_repos, comprehensive | repository |
| `target` | Target to scrape | owner/repo, username, org name, or search query | microsoft/vscode |
| `output_format` | Output file format | json, csv, both | json |
| `include_commits` | Include commit history | true/false | false |
| `include_issues` | Include issues data | true/false | false |
| `include_pull_requests` | Include PR data | true/false | false |
| `max_items` | Maximum items to fetch | number | 100 |
| `parallel_execution` | Enable parallel processing | true/false | true |
| `notification_email` | Email for notifications | email address | (empty) |
| `slack_webhook` | Slack webhook URL | URL | (empty) |
| `artifact_retention_days` | How long to keep artifacts | number | 30 |
| `debug_mode` | Enable debug logging | true/false | false |

### Scraper Modes

#### `repository`
Scrapes comprehensive repository information including metadata, statistics, contributors, languages, topics, releases, README, license, and file tree.

**Target format**: `owner/repo` (e.g., `microsoft/vscode`)

#### `user`
Scrapes user profile information, repositories, and activity.

**Target format**: `username` (e.g., `torvalds`)

#### `issues`
Scrapes issues from a repository with detailed information.

**Target format**: `owner/repo` (e.g., `facebook/react`)

#### `pull_requests`
Scrapes pull requests from a repository.

**Target format**: `owner/repo` (e.g., `google/tensorflow`)

#### `organization`
Scrapes organization information and repositories.

**Target format**: `org_name` (e.g., `microsoft`)

#### `search_repos`
Searches repositories using GitHub's search API.

**Target format**: Search query (e.g., `machine learning language:python stars:>1000`)

#### `search_users`
Searches users using GitHub's search API.

**Target format**: Search query (e.g., `location:seattle followers:>100`)

#### `search_code`
Searches code using GitHub's search API.

**Target format**: Search query (e.g., `def scrape_repository language:python`)

#### `batch_repos`
Scrapes multiple repositories in parallel.

**Target format**: Comma-separated list (e.g., `microsoft/vscode,facebook/react,google/tensorflow`)

#### `comprehensive`
Performs comprehensive scraping including commits, issues, and pull requests.

**Target format**: `owner/repo` or comma-separated list

## 🌐 API/Webhook Integration (Poke)

### Repository Dispatch Trigger

External systems can trigger the workflow using GitHub's repository dispatch API:

```bash
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  https://api.github.com/repos/CrazyDubya/research-scrapers/dispatches \
  -d '{
    "event_type": "scrape-github-api",
    "client_payload": {
      "scraper_mode": "repository",
      "target": "microsoft/vscode",
      "output_format": "json",
      "include_commits": false,
      "include_issues": true,
      "include_pull_requests": true,
      "max_items": 100,
      "parallel_execution": true,
      "notification_email": "user@example.com",
      "debug_mode": false
    }
  }'
```

### Poke Integration

For Poke integration, use the `poke-trigger` event type:

```bash
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  https://api.github.com/repos/CrazyDubya/research-scrapers/dispatches \
  -d '{
    "event_type": "poke-trigger",
    "client_payload": {
      "scraper_mode": "comprehensive",
      "target": "owner/repo",
      "output_format": "both",
      "notification_email": "notifications@yourcompany.com"
    }
  }'
```

## 📊 Output Formats

### JSON Output
- Complete structured data
- Preserves all relationships and metadata
- Ideal for programmatic consumption
- File naming: `{mode}_{target}_{run_id}.json`

### CSV Output
- Flattened data structure
- Compatible with spreadsheet applications
- Suitable for data analysis
- File naming: `{mode}_{target}_{run_id}.csv`

### Artifacts
All outputs are uploaded as GitHub Actions artifacts with configurable retention periods.

## 📧 Notifications

### Email Notifications
Configure SMTP settings in repository secrets:
- `SMTP_USERNAME`: Your SMTP username
- `SMTP_PASSWORD`: Your SMTP password

The workflow uses Gmail SMTP by default. For other providers, modify the workflow file.

### Slack Notifications
Add your Slack webhook URL as `SLACK_WEBHOOK_URL` secret or provide it as a workflow input.

### Automatic Issue Creation
On workflow failures, an issue is automatically created with:
- Failure details
- Configuration used
- Links to workflow logs
- Troubleshooting steps

## 🔍 Monitoring and Debugging

### Rate Limit Monitoring
The workflow automatically checks GitHub API rate limits before execution and warns if limits are low.

### Debug Mode
Enable debug mode for verbose logging:
- Set `debug_mode: true` in manual execution
- Or include `"debug_mode": true` in API payload

### Logs and Artifacts
- All execution logs are saved as artifacts
- Metadata files include execution details
- Aggregated results provide summary information

## 🛡️ Security Best Practices

### Secrets Management
- Never commit tokens or credentials to the repository
- Use GitHub Secrets for all sensitive information
- Rotate tokens regularly
- Use least-privilege access tokens

### OIDC Authentication
The workflow uses OpenID Connect (OIDC) for secure authentication where supported.

### Input Validation
- All inputs are validated before execution
- Target formats are checked based on scraper mode
- Rate limits are monitored to prevent abuse

## 🚨 Troubleshooting

### Common Issues

#### "Rate limit exceeded"
- Wait for rate limit reset (shown in logs)
- Use authenticated requests (ensure GITHUB_TOKEN is set)
- Reduce `max_items` parameter
- Enable parallel execution for better rate limit utilization

#### "Repository not found"
- Verify repository name format (`owner/repo`)
- Check if repository is public or token has access
- Ensure target exists and is accessible

#### "Invalid target format"
- Check target format matches scraper mode requirements
- For batch operations, use comma-separated format
- Remove extra spaces or special characters

#### "Workflow fails to start"
- Verify all required secrets are configured
- Check repository permissions
- Ensure workflow file syntax is valid

### Getting Help

1. Check workflow logs in Actions tab
2. Review the automatically created issue on failures
3. Enable debug mode for detailed logging
4. Check GitHub API status at https://www.githubstatus.com/

## 📈 Performance Optimization

### Parallel Execution
- Enable for batch operations
- Automatically splits comma-separated targets
- Respects rate limits across parallel jobs

### Caching
- Python dependencies are cached automatically
- Reduces setup time for subsequent runs

### Artifact Management
- Configure retention periods based on needs
- Use compression to reduce storage costs
- Clean up old artifacts regularly

## 🔄 Workflow Maintenance

### Regular Updates
- Monitor for new GitHub API features
- Update Python dependencies in requirements.txt
- Review and update rate limiting strategies

### Monitoring
- Set up alerts for workflow failures
- Monitor artifact storage usage
- Review rate limit consumption patterns

## 📚 Examples

### Basic Repository Scraping
```yaml
scraper_mode: repository
target: microsoft/vscode
output_format: json
include_commits: false
include_issues: true
max_items: 50
```

### Comprehensive Analysis
```yaml
scraper_mode: comprehensive
target: facebook/react
output_format: both
include_commits: true
include_issues: true
include_pull_requests: true
max_items: 200
notification_email: analyst@company.com
```

### Batch Processing
```yaml
scraper_mode: batch_repos
target: microsoft/vscode,facebook/react,google/tensorflow
output_format: json
parallel_execution: true
max_items: 100
```

### User Analysis
```yaml
scraper_mode: user
target: torvalds
output_format: csv
notification_email: research@company.com
```

### Search Operations
```yaml
scraper_mode: search_repos
target: "machine learning language:python stars:>1000"
output_format: both
max_items: 50
```

## 🎯 Best Practices

1. **Start Small**: Begin with single repositories before batch operations
2. **Monitor Rate Limits**: Keep an eye on API usage
3. **Use Appropriate Modes**: Choose the right scraper mode for your needs
4. **Configure Notifications**: Set up alerts for important operations
5. **Regular Maintenance**: Keep dependencies and tokens updated
6. **Document Usage**: Track what you're scraping and why
7. **Respect GitHub's Terms**: Follow GitHub's API terms of service
8. **Optimize for Performance**: Use parallel execution and appropriate limits

---

For additional support or feature requests, please create an issue in the repository.