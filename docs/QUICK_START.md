# Quick Start Guide: Secure API Architecture

Get your research-scrapers project up and running with GitHub Actions and Linear integration in under 15 minutes.

## Prerequisites Checklist

- [ ] GitHub account with repository admin access
- [ ] Linear workspace membership
- [ ] 15 minutes of setup time

## Step-by-Step Setup

### Step 1: Configure Secrets (5 minutes)

#### 1.1 Create GitHub Personal Access Token

1. Visit: https://github.com/settings/tokens/new
2. Token name: `research-scrapers-automation`
3. Expiration: 90 days
4. Select scopes:
   - ✅ `repo` (all)
   - ✅ `workflow`
5. Click "Generate token"
6. **Copy the token** (starts with `ghp_`)

#### 1.2 Create Linear API Key

1. Visit: https://linear.app/settings/api
2. Click "Create new API key"
3. Name: `GitHub Actions Integration`
4. Permissions: ✅ Read, ✅ Write
5. Click "Create"
6. **Copy the API key** (starts with `lin_api_`)

#### 1.3 Add Secrets to Repository

1. Go to repository: `Settings` → `Secrets and variables` → `Actions`
2. Click `New repository secret`
3. Add first secret:
   - Name: `GITHUB_TOKEN`
   - Value: [Paste your GitHub token]
4. Add second secret:
   - Name: `LINEAR_API_KEY`
   - Value: [Paste your Linear API key]

✅ **Secrets configured successfully!**

### Step 2: Test the Workflow (5 minutes)

#### 2.1 Manual Trigger Test

1. Go to `Actions` tab in your repository
2. Click "Scheduled Research Scraper" workflow
3. Click "Run workflow" button
4. Configure test run:
   ```
   scraper_type: github_repo
   target: octocat/Hello-World
   linear_task_id: [leave empty]
   update_linear: false
   ```
5. Click "Run workflow"

#### 2.2 Verify Execution

Watch for these steps to complete:
- ✅ Setup and Validation
- ✅ Execute Research Scrapers
- ✅ Upload artifacts
- ✅ Generate summary

Expected time: 2-3 minutes

#### 2.3 Check Results

1. Click on the completed workflow run
2. Scroll to bottom: "Summary" section
3. Click "Artifacts" to download results
4. Verify JSON files are present

✅ **Workflow tested successfully!**

### Step 3: Create Linear Integration (5 minutes)

#### 3.1 Create Test Task in Linear

1. Go to your Linear workspace
2. Create new issue:
   ```
   Title: Test Research Scraper Integration
   
   Description:
   This is a test task for GitHub Actions integration.
   
   target: facebook/react
   
   Labels: scrape-repos
   ```
3. Note the issue ID (e.g., `ENG-123`)

#### 3.2 Trigger Scraper for Linear Task

1. Go to GitHub `Actions` tab
2. Run "Scheduled Research Scraper" workflow
3. Configure:
   ```
   scraper_type: github_repo
   target: facebook/react
   linear_task_id: ENG-123
   update_linear: true
   ```
4. Click "Run workflow"

#### 3.3 Verify Linear Update

1. Wait for workflow to complete (2-3 minutes)
2. Go back to your Linear task
3. Check for:
   - ✅ New comment with research results
   - ✅ Status updated to "Done"
   - ✅ Research findings formatted as markdown

✅ **Linear integration working!**

## Common Commands

### Manual Workflow Trigger
```bash
gh workflow run research-scraper-scheduled.yml \
  --field scraper_type="github_repo" \
  --field target="owner/repo" \
  --field linear_task_id="ENG-123" \
  --field update_linear=true
```

### View Latest Runs
```bash
gh run list --workflow=research-scraper-scheduled.yml --limit=5
```

### Download Artifacts
```bash
gh run download [RUN_ID] --dir ./downloads
```

### View Logs
```bash
gh run view --log
```

## Quick Troubleshooting

### ❌ Problem: "Secret not found"
**Solution**: Verify secrets in `Settings` → `Secrets and variables` → `Actions`

### ❌ Problem: "401 Unauthorized"
**Solution**: Check token hasn't expired, regenerate if needed

### ❌ Problem: "Linear update failed"
**Solution**: Verify Linear API key has write permissions

### ❌ Problem: "Workflow not found"
**Solution**: Ensure you're on the `main` branch with latest commits

## Next Steps

### Configure Scheduled Execution
Edit `.github/workflows/research-scraper-scheduled.yml`:

```yaml
schedule:
  # Change this cron expression
  - cron: '0 2 * * *'  # Daily at 2 AM UTC
  
# Examples:
# - cron: '0 */6 * * *'      # Every 6 hours
# - cron: '0 9 * * 1-5'      # Weekdays at 9 AM
# - cron: '0 0 1,15 * *'     # 1st and 15th of month
```

### Set Up Webhook Integration
See: [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md#webhook-configuration)

### Customize Scrapers
See: [README.md](../README.md) for scraper configuration options

### Enable Notifications
Add Slack webhook to secrets and uncomment notification step

## Architecture Documentation

For detailed information, see:

- **[API_ARCHITECTURE.md](./API_ARCHITECTURE.md)** - Complete system architecture
- **[SECURITY_ARCHITECTURE.md](./SECURITY_ARCHITECTURE.md)** - Security best practices
- **[INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)** - Detailed integration instructions

## Support

### Getting Help

1. **Check workflow logs**:
   ```bash
   gh run view --log-failed
   ```

2. **Review documentation**: Check the docs/ directory

3. **Open an issue**: Use the GitHub Issues tab

### Useful Links

- [GitHub Actions Documentation](https://docs.github.com/actions)
- [Linear API Documentation](https://developers.linear.app/)
- [GitHub CLI Documentation](https://cli.github.com/manual/)

---

**Setup Time**: ~15 minutes  
**Difficulty**: Beginner-friendly  
**Last Updated**: 2025-10-04