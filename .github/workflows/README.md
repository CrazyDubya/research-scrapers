# GitHub Actions Workflows

This directory contains production-ready GitHub Actions workflows for automating research scraping operations.

## 📁 Available Workflows

### `github-api-scraper-production.yml` 
**Main production workflow for GitHub API scraping**

- **Triggers**: Scheduled (daily 2 AM UTC), Manual, API/Webhook
- **Features**: Parallel execution, multiple output formats, comprehensive notifications
- **Security**: OIDC authentication, secrets management, rate limit monitoring
- **Documentation**: [Setup Guide](../../docs/WORKFLOW_SETUP_GUIDE.md)

### `research-scraper-scheduled.yml`
**Legacy scheduled scraper with Linear integration**

- **Triggers**: Scheduled (daily 2 AM UTC), Manual
- **Features**: Linear task updates, multi-scraper execution
- **Use Case**: Existing Linear workflow integration

### `linear-webhook-trigger.yml`
**Linear webhook integration for event-driven scraping**

- **Triggers**: repository_dispatch (Linear webhooks)
- **Features**: Linear task creation, webhook payload processing
- **Use Case**: Automated scraping triggered by Linear events

### `codeql-analysis.yml`
**Security scanning and code analysis**

- **Triggers**: Push, Pull Request, Scheduled
- **Features**: CodeQL security scanning, vulnerability detection
- **Use Case**: Continuous security monitoring

## 🚀 Quick Start

### 1. Configure Secrets

Go to **Settings > Secrets and variables > Actions** and add:

```bash
# Required
GITHUB_TOKEN          # GitHub Personal Access Token

# Optional (for notifications)
SMTP_USERNAME         # Email SMTP username  
SMTP_PASSWORD         # Email SMTP password
SLACK_WEBHOOK_URL     # Slack webhook URL

# Optional (for Linear integration)
LINEAR_API_KEY        # Linear API key
```

### 2. Manual Execution

1. Go to **Actions** tab
2. Select **GitHub API Scraper - Production**
3. Click **Run workflow**
4. Configure parameters:
   - Choose scraper mode
   - Enter target (repo, user, org)
   - Select output format
   - Configure data inclusion options
   - Set notification preferences

### 3. API/Webhook Trigger (Poke Integration)

Use the provided Python script:

```bash
# Install dependencies
pip install requests

# Set token
export GITHUB_TOKEN="your_token_here"

# Trigger workflow
python scripts/trigger_workflow.py \
  --mode repository \
  --target microsoft/vscode \
  --include-issues \
  --email notify@example.com
```

Or use cURL:

```bash
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/CrazyDubya/research-scrapers/dispatches \
  -d '{
    "event_type": "scrape-github-api",
    "client_payload": {
      "scraper_mode": "repository",
      "target": "microsoft/vscode",
      "output_format": "json"
    }
  }'
```

## 🔒 Security Best Practices

### Secrets Management

✅ **DO:**
- Store all credentials in GitHub Secrets
- Use least-privilege access tokens
- Rotate tokens regularly (every 90 days)
- Use different tokens for different environments
- Enable token expiration where possible
- Audit secret usage regularly

❌ **DON'T:**
- Commit tokens or credentials to repository
- Share tokens between projects
- Use personal tokens for production
- Log sensitive information
- Include secrets in workflow outputs

### Token Permissions

GitHub tokens should have minimal required scopes:

```
repo              # Full control of private repositories
read:org          # Read org and team membership (if needed)
read:user         # Read user profile data (if needed)
workflow          # Update GitHub Action workflows (if needed)
```

### Rate Limiting

The workflows implement several rate limit protections:

1. **Pre-flight checks**: Verify rate limits before execution
2. **Monitoring**: Log rate limit consumption
3. **Warnings**: Alert when limits are low
4. **Backoff**: Automatic retry with exponential backoff
5. **Throttling**: Built-in rate limiting in scrapers

### Input Validation

All inputs are validated:
- Target format validation based on scraper mode
- Parameter range validation
- Token presence verification
- Configuration syntax checking

## 📊 Workflow Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    TRIGGER SOURCES                       │
├─────────────┬─────────────────┬─────────────────────────┤
│  Scheduled  │  Manual (UI)    │  API/Webhook (Poke)     │
│  (Cron)     │  (Dispatch)     │  (repository_dispatch)   │
└─────────────┴─────────────────┴─────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              SETUP AND VALIDATION JOB                    │
├─────────────────────────────────────────────────────────┤
│  • Parse and validate inputs                            │
│  • Check GitHub API rate limits                         │
│  • Verify secrets and configuration                     │
│  • Prepare matrix strategy for parallel execution       │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                 SCRAPING EXECUTION                       │
├─────────────────────────────────────────────────────────┤
│  [Matrix Strategy - Parallel Jobs]                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Target 1 │  │ Target 2 │  │ Target 3 │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│  • Execute scraper with configuration                   │
│  • Validate and analyze output                          │
│  • Generate metadata                                     │
│  • Upload artifacts                                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│            AGGREGATION AND PROCESSING                    │
├─────────────────────────────────────────────────────────┤
│  • Download all artifacts                               │
│  • Aggregate results into single dataset                │
│  • Generate summary reports                             │
│  • Create consolidated artifacts                        │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   NOTIFICATIONS                          │
├─────────────────────────────────────────────────────────┤
│  • Email notifications                                   │
│  • Slack messages                                        │
│  • GitHub issue creation (on failure)                   │
│  • Job summaries                                         │
└─────────────────────────────────────────────────────────┘
```

## 🎯 Scraper Modes

| Mode | Description | Target Format | Use Case |
|------|-------------|---------------|----------|
| `repository` | Single repo metadata | `owner/repo` | Deep dive into one repository |
| `user` | User profile & repos | `username` | Analyze user activity |
| `issues` | Repository issues | `owner/repo` | Issue tracking analysis |
| `pull_requests` | Repository PRs | `owner/repo` | PR workflow analysis |
| `organization` | Org info & repos | `org_name` | Organization overview |
| `search_repos` | Search repositories | `query` | Find repos by criteria |
| `search_users` | Search users | `query` | Find users by criteria |
| `search_code` | Search code | `query` | Code pattern analysis |
| `batch_repos` | Multiple repos | `repo1,repo2,repo3` | Comparative analysis |
| `comprehensive` | Full repo analysis | `owner/repo` | Complete data extraction |

## 📈 Performance Optimization

### Parallel Execution
- Automatically splits comma-separated targets
- Configurable parallelism (max 5 concurrent jobs)
- Respects rate limits across parallel jobs

### Caching Strategy
- Python dependencies cached per workflow
- Cache key includes Python version and requirements hash
- Automatic cache invalidation on dependency changes

### Artifact Management
- Configurable retention periods (1-90 days)
- Compression level 9 for individual artifacts
- Compression level 6 for aggregated results
- Automatic cleanup of expired artifacts

## 🔍 Monitoring and Debugging

### Workflow Logs
All logs are available in the Actions tab:
1. Go to **Actions** tab
2. Select workflow run
3. Click on job name
4. Expand steps to see detailed logs

### Artifacts
Download artifacts from completed runs:
1. Go to workflow run
2. Scroll to **Artifacts** section
3. Download desired artifact

### Debug Mode
Enable verbose logging:
- Manual: Set `debug_mode: true`
- API: Include `"debug_mode": true` in payload

### Rate Limit Monitoring
Check rate limits before running:
```bash
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/rate_limit
```

## 🚨 Troubleshooting

### Common Issues

#### Issue: "Workflow not found"
**Solution**: Ensure workflow file is in `.github/workflows/` directory and properly named

#### Issue: "Invalid token"
**Solution**: 
- Verify token is set in repository secrets
- Check token hasn't expired
- Ensure token has required permissions

#### Issue: "Rate limit exceeded"
**Solution**:
- Wait for rate limit reset (1 hour)
- Use authenticated requests (5000/hr vs 60/hr)
- Reduce `max_items` parameter
- Enable parallel execution for better distribution

#### Issue: "Target not found"
**Solution**:
- Verify repository/user exists
- Check target format matches scraper mode
- Ensure repository is public or token has access

#### Issue: "Workflow doesn't trigger"
**Solution**:
- Check workflow syntax with `yamllint`
- Verify trigger configuration
- Check repository permissions
- Review webhook payload format

### Getting Help

1. **Check Documentation**: [Workflow Setup Guide](../../docs/WORKFLOW_SETUP_GUIDE.md)
2. **Review Logs**: Check workflow run logs in Actions tab
3. **Enable Debug Mode**: Run with debug logging enabled
4. **Check Status**: Use `scripts/trigger_workflow.py --check-status`
5. **Create Issue**: Report bugs with detailed information

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Repository Dispatch Events](https://docs.github.com/en/rest/reference/repos#create-a-repository-dispatch-event)

## 🤝 Contributing

When modifying workflows:

1. **Test Locally**: Validate YAML syntax
2. **Use Branches**: Create feature branches for changes
3. **Document Changes**: Update this README and setup guide
4. **Test Thoroughly**: Test with various configurations
5. **Review Security**: Ensure no secrets are exposed
6. **Update Version**: Update workflow version in comments

## 📝 Version History

### v2.0.0 (Current) - Production Release
- ✅ Comprehensive production workflow
- ✅ Multiple trigger methods (scheduled, manual, API)
- ✅ Matrix strategy for parallel execution
- ✅ Multiple output formats (JSON, CSV)
- ✅ Email and Slack notifications
- ✅ Rate limit monitoring
- ✅ Artifact management
- ✅ Security best practices
- ✅ Poke integration support

### v1.0.0 - Initial Release
- Basic scheduled workflow
- Linear integration
- Single scraper execution

---

**Maintained by**: Stephen Thompson  
**Last Updated**: 2025-01-05  
**Status**: Production Ready ✅