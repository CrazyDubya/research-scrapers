# Integration Guide: GitHub Actions + Linear API

## Overview

This guide provides step-by-step instructions for integrating the research-scrapers project with GitHub Actions and Linear API, enabling automated research workflows triggered by Linear tasks.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [GitHub Actions Setup](#github-actions-setup)
3. [Linear API Setup](#linear-api-setup)
4. [Webhook Configuration](#webhook-configuration)
5. [Testing & Validation](#testing--validation)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Accounts
- GitHub account with repository access
- Linear workspace with API access
- Python 3.11+ installed locally (for testing)

### Required Permissions
- **GitHub**: Repository admin or write access
- **Linear**: Workspace member with API key creation rights

## GitHub Actions Setup

### Step 1: Configure Repository Secrets

Navigate to your repository settings:

```
Repository → Settings → Secrets and variables → Actions → New repository secret
```

#### Create GitHub Token

1. Generate a Personal Access Token:
   ```
   GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   ```

2. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `read:org` (Read organization data)
   - ✅ `workflow` (Update GitHub Action workflows)

3. Copy the token (starts with `ghp_`)

4. Add to repository secrets:
   - **Name**: `GITHUB_TOKEN`
   - **Value**: Your generated token

#### Create Linear API Key

1. Generate Linear API Key:
   ```
   Linear → Settings → API → Create new API key
   ```

2. Set permissions:
   - ✅ `read` - Read issues and projects
   - ✅ `write` - Update issues and add comments

3. Copy the API key (starts with `lin_api_`)

4. Add to repository secrets:
   - **Name**: `LINEAR_API_KEY`
   - **Value**: Your Linear API key

### Step 2: Verify Workflow Files

The following workflow files should exist in `.github/workflows/`:

```bash
.github/workflows/
├── research-scraper-scheduled.yml    # Main scheduled workflow
├── linear-webhook-trigger.yml        # Linear webhook integration
└── codeql-analysis.yml              # Security scanning (existing)
```

### Step 3: Enable Workflow Permissions

1. Navigate to repository settings:
   ```
   Repository → Settings → Actions → General
   ```

2. Configure workflow permissions:
   - ✅ Read and write permissions
   - ✅ Allow GitHub Actions to create and approve pull requests

3. Set runner group (if using self-hosted):
   - Default: GitHub-hosted runners (recommended)

### Step 4: Test Manual Workflow

1. Navigate to Actions tab
2. Select "Scheduled Research Scraper"
3. Click "Run workflow"
4. Configure parameters:
   ```yaml
   scraper_type: github_repo
   target: octocat/Hello-World
   linear_task_id: [leave empty for testing]
   update_linear: false
   ```
5. Click "Run workflow"

Expected result: ✅ Workflow completes successfully with artifacts

## Linear API Setup

### Step 1: Create Integration

1. Go to Linear Settings → API
2. Create new Personal API Key
3. Name it: `Research Scrapers Integration`
4. Set description: `GitHub Actions automation for research scrapers`

### Step 2: Configure Webhook (Optional)

For automated triggering from Linear tasks:

1. Go to Linear Settings → Webhooks
2. Create new webhook:
   ```
   URL: https://github.com/YOUR_ORG/research-scrapers/dispatches
   Events: Issue created, Issue updated
   ```

3. Note: GitHub doesn't directly accept webhooks. Use one of these approaches:
   - **Option A**: Use a webhook proxy service (Zapier, Make.com)
   - **Option B**: Deploy a serverless function (AWS Lambda, Vercel)
   - **Option C**: Use Linear's GraphQL API directly in workflows

### Step 3: Linear Task Template

Create a task template for research requests:

```markdown
## Research Request

**Type**: [Repository/Issue/User Analysis]
**Target**: [GitHub URL or username]
**Priority**: [High/Medium/Low]

### Details
[Describe what you want to research]

### Expected Outputs
- [ ] Repository metadata
- [ ] Issue statistics
- [ ] Contributor analysis
- [ ] Custom analysis: [describe]

### Labels
Add appropriate labels:
- `scrape-repos` - Repository analysis
- `scrape-issues` - Issue analysis  
- `scrape-users` - User analysis
- `scrape-all` - Comprehensive analysis

---
*This task will trigger automated GitHub Actions workflow*
```

## Webhook Configuration

### Option A: Using Zapier (Easiest)

1. Create a Zapier account
2. Create new Zap:
   ```
   Trigger: Linear → New Issue
   Filter: Issue has label "research-request"
   Action: GitHub → Trigger Workflow
   ```

3. Configure GitHub action:
   ```yaml
   Repository: YOUR_ORG/research-scrapers
   Workflow: research-scraper-scheduled.yml
   Inputs:
     scraper_type: {{issue.labels}}
     target: {{issue.description | extract_target}}
     linear_task_id: {{issue.id}}
     update_linear: true
   ```

### Option B: Using GitHub Repository Dispatch

Create a webhook endpoint that converts Linear webhooks to GitHub repository dispatch events:

#### Deploy Serverless Function (Example: Vercel)

```javascript
// api/linear-webhook.js
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { action, data } = req.body;
  
  // Validate Linear webhook signature
  // ... (implement signature verification)
  
  // Convert to GitHub repository dispatch
  const githubPayload = {
    event_type: `linear-task-${action}`,
    client_payload: {
      task_id: data.id,
      task_title: data.title,
      task_description: data.description,
      labels: data.labels.map(l => l.name).join(',')
    }
  };
  
  // Send to GitHub
  const response = await fetch(
    `https://api.github.com/repos/YOUR_ORG/research-scrapers/dispatches`,
    {
      method: 'POST',
      headers: {
        'Authorization': `token ${process.env.GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(githubPayload)
    }
  );
  
  return res.status(200).json({ success: true });
}
```

Deploy to Vercel:
```bash
npm install -g vercel
vercel deploy
```

Add webhook URL to Linear:
```
https://your-app.vercel.app/api/linear-webhook
```

### Option C: Manual Trigger with Linear CLI

For simpler setups, manually trigger workflows:

```bash
#!/bin/bash
# trigger-scraper.sh

TASK_ID=$1
SCRAPER_TYPE=${2:-"all"}
TARGET=$3

gh workflow run research-scraper-scheduled.yml \
  --field scraper_type="$SCRAPER_TYPE" \
  --field target="$TARGET" \
  --field linear_task_id="$TASK_ID" \
  --field update_linear=true
```

Usage:
```bash
./trigger-scraper.sh "ISSUE-123" "github_repo" "facebook/react"
```

## Testing & Validation

### Test 1: GitHub Actions Workflow

```bash
# Clone repository
git clone https://github.com/YOUR_ORG/research-scrapers.git
cd research-scrapers

# Install dependencies
pip install -r requirements.txt

# Test scraper locally
export GITHUB_TOKEN="your_token"
python github_repo_scraper.py --target octocat/Hello-World

# Trigger workflow manually
gh workflow run research-scraper-scheduled.yml \
  --field scraper_type="github_repo" \
  --field target="octocat/Hello-World" \
  --field update_linear=false
```

### Test 2: Linear API Integration

```bash
# Test Linear API access
export LINEAR_API_KEY="your_key"
python scripts/update_linear_task.py \
  --artifacts-dir ./output \
  --task-id "YOUR-TASK-ID" \
  --run-id "test-run-001" \
  --workflow-url "https://example.com"
```

### Test 3: End-to-End Integration

1. Create a test task in Linear with label `scrape-repos`
2. Add target in description: `target: octocat/Hello-World`
3. If using webhooks, save the task
4. If manual, trigger workflow with task ID
5. Verify:
   - ✅ Workflow runs successfully
   - ✅ Artifacts are created
   - ✅ Linear task is updated with comment
   - ✅ Task status changes to "Done"

## Workflow Triggers

### Manual Trigger

```bash
gh workflow run research-scraper-scheduled.yml \
  --field scraper_type="github_repo" \
  --field target="owner/repo" \
  --field linear_task_id="ISSUE-123" \
  --field update_linear=true
```

### Scheduled Trigger

Runs automatically at 2 AM UTC daily:

```yaml
schedule:
  - cron: '0 2 * * *'
```

Customize schedule:
```yaml
# Run every 6 hours
- cron: '0 */6 * * *'

# Run weekdays at 9 AM
- cron: '0 9 * * 1-5'

# Run on 1st and 15th of month
- cron: '0 0 1,15 * *'
```

### Webhook Trigger (via Repository Dispatch)

```bash
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/YOUR_ORG/research-scrapers/dispatches \
  -d '{
    "event_type": "linear-task-created",
    "client_payload": {
      "task_id": "ISSUE-123",
      "task_title": "Research React repository",
      "task_description": "target: facebook/react",
      "labels": "scrape-repos"
    }
  }'
```

## Troubleshooting

### Common Issues

#### 1. Workflow Not Triggering

**Problem**: Workflow doesn't run on schedule or manual trigger

**Solutions**:
```bash
# Check workflow status
gh workflow list

# Enable workflow if disabled
gh workflow enable research-scraper-scheduled.yml

# View workflow runs
gh run list --workflow=research-scraper-scheduled.yml

# Check workflow syntax
yamllint .github/workflows/research-scraper-scheduled.yml
```

#### 2. Authentication Failures

**Problem**: `401 Unauthorized` or `403 Forbidden` errors

**Solutions**:
- Verify GitHub token has correct scopes
- Check token hasn't expired
- Ensure secrets are properly configured
- Test token manually:
  ```bash
  curl -H "Authorization: token YOUR_TOKEN" \
    https://api.github.com/user
  ```

#### 3. Linear API Errors

**Problem**: Linear updates fail with GraphQL errors

**Solutions**:
- Verify Linear API key is valid
- Check Linear issue ID format
- Test API access:
  ```bash
  curl -X POST https://api.linear.app/graphql \
    -H "Authorization: YOUR_KEY" \
    -H "Content-Type: application/json" \
    -d '{"query": "{ viewer { id name } }"}'
  ```

#### 4. Scraper Execution Failures

**Problem**: Scraper scripts fail or produce no output

**Solutions**:
- Check Python version (requires 3.11+)
- Verify all dependencies installed
- Review workflow logs:
  ```bash
  gh run view --log
  ```
- Test locally:
  ```bash
  python github_repo_scraper.py --target owner/repo --log logs/test.log
  ```

#### 5. Artifact Issues

**Problem**: Artifacts not uploaded or downloadable

**Solutions**:
- Check artifact retention settings (default 30 days)
- Verify output files exist before upload
- Check artifact size limits (10 GB max)
- List artifacts:
  ```bash
  gh run view RUN_ID --json artifacts
  ```

### Debug Mode

Enable debug logging in workflows:

```yaml
env:
  ACTIONS_STEP_DEBUG: true
  ACTIONS_RUNNER_DEBUG: true
```

Or set in repository settings:
```
Settings → Secrets → New secret
Name: ACTIONS_STEP_DEBUG
Value: true
```

### Getting Help

1. **Check workflow logs**:
   ```bash
   gh run view --log-failed
   ```

2. **Review documentation**:
   - [GitHub Actions Docs](https://docs.github.com/actions)
   - [Linear API Docs](https://developers.linear.app/)

3. **Contact support**:
   - GitHub Issues: Open issue in repository
   - Linear Support: support@linear.app

## Advanced Configuration

### Custom Scraper Parameters

Extend workflow inputs for custom parameters:

```yaml
inputs:
  depth:
    description: 'Scraping depth level'
    type: number
    default: 1
  
  filters:
    description: 'JSON filter criteria'
    type: string
    default: '{}'
```

### Multi-Environment Setup

Create environment-specific secrets:

```yaml
jobs:
  run-scrapers:
    environment: production  # or staging, development
    env:
      GITHUB_TOKEN: ${{ secrets.PROD_GITHUB_TOKEN }}
      LINEAR_API_KEY: ${{ secrets.PROD_LINEAR_KEY }}
```

### Notification Integrations

Add Slack/Discord notifications:

```yaml
- name: Notify on completion
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

**Last Updated**: 2025-10-04  
**Version**: 1.0  
**Maintainer**: Stephen Thompson