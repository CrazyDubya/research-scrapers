# GitHub Actions Workflow - Quick Reference Card

## 🚀 Trigger Methods

### 1. Scheduled (Automatic)
Runs daily at 2 AM UTC automatically - no action needed.

### 2. Manual (GitHub UI)
```
1. Go to repository → Actions tab
2. Select "GitHub API Scraper - Production"
3. Click "Run workflow" button
4. Fill in parameters
5. Click green "Run workflow" button
```

### 3. API/Webhook (Poke Integration)

**cURL:**
```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  https://api.github.com/repos/CrazyDubya/research-scrapers/dispatches \
  -d '{
    "event_type": "scrape-github-api",
    "client_payload": {
      "scraper_mode": "repository",
      "target": "microsoft/vscode"
    }
  }'
```

**Python:**
```bash
export GITHUB_TOKEN="your_token"
python scripts/trigger_workflow.py --mode repository --target microsoft/vscode
```

---

## 📋 Scraper Modes Cheat Sheet

| Mode | Target Format | Example |
|------|---------------|---------|
| `repository` | `owner/repo` | `microsoft/vscode` |
| `user` | `username` | `torvalds` |
| `issues` | `owner/repo` | `facebook/react` |
| `pull_requests` | `owner/repo` | `google/tensorflow` |
| `organization` | `org_name` | `microsoft` |
| `batch_repos` | `repo1,repo2,repo3` | `microsoft/vscode,facebook/react` |
| `comprehensive` | `owner/repo` | `google/tensorflow` |
| `search_repos` | `search query` | `language:python stars:>1000` |
| `search_users` | `search query` | `location:seattle followers:>100` |
| `search_code` | `search query` | `def scrape language:python` |

---

## ⚡ Common Commands

### Check Workflow Status
```bash
python scripts/trigger_workflow.py --check-status
```

### Create Sample Config
```bash
python scripts/trigger_workflow.py --create-config
```

### Scrape Single Repository
```bash
python scripts/trigger_workflow.py \
  --mode repository \
  --target owner/repo \
  --include-issues
```

### Batch Scrape Multiple Repos
```bash
python scripts/trigger_workflow.py \
  --mode batch_repos \
  --target "repo1,repo2,repo3" \
  --parallel \
  --format both
```

### Comprehensive Analysis
```bash
python scripts/trigger_workflow.py \
  --mode comprehensive \
  --target owner/repo \
  --include-commits \
  --include-issues \
  --include-prs \
  --max-items 200
```

### With Email Notification
```bash
python scripts/trigger_workflow.py \
  --mode repository \
  --target owner/repo \
  --email your-email@example.com
```

### Debug Mode
```bash
python scripts/trigger_workflow.py \
  --mode repository \
  --target owner/repo \
  --debug
```

---

## 🔑 Required Secrets

Go to: **Settings → Secrets and variables → Actions**

### Required
```
GITHUB_TOKEN = ghp_your_personal_access_token
```

### Optional (Notifications)
```
SMTP_USERNAME = your-email@gmail.com
SMTP_PASSWORD = your-app-password
SLACK_WEBHOOK_URL = https://hooks.slack.com/services/...
```

---

## 📊 Output Files

| File Type | Pattern | Example |
|-----------|---------|---------|
| JSON | `{mode}_{target}_{run_id}.json` | `repository_microsoft_vscode_20250105.json` |
| CSV | `{mode}_{target}_{run_id}.csv` | `repository_microsoft_vscode_20250105.csv` |
| Logs | `{mode}_{target}_{run_id}.log` | `repository_microsoft_vscode_20250105.log` |
| Metadata | `metadata_{target}_{run_id}.json` | `metadata_microsoft_vscode_20250105.json` |

**Download**: Actions → Workflow Run → Artifacts section

---

## ⚙️ Key Parameters

| Parameter | Options | Default |
|-----------|---------|---------|
| `output_format` | json, csv, both | json |
| `include_commits` | true, false | false |
| `include_issues` | true, false | false |
| `include_pull_requests` | true, false | false |
| `max_items` | 1-1000 | 100 |
| `parallel_execution` | true, false | true |
| `artifact_retention_days` | 1-90 | 30 |
| `debug_mode` | true, false | false |

---

## 🚨 Troubleshooting Quick Fixes

### "Rate limit exceeded"
```bash
# Check current rate limit
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/rate_limit
```
**Fix**: Wait 1 hour or use authenticated requests

### "Invalid token"
**Fix**: Generate new token at Settings → Developer settings → Personal access tokens

### "Repository not found"
**Fix**: Verify repository exists and is accessible with your token

### "Workflow not triggering"
**Fix**: Check workflow file is in `.github/workflows/` directory

### "Artifacts not showing"
**Fix**: Wait for workflow to complete, check retention period hasn't expired

---

## 📈 Rate Limits

| Type | Unauthenticated | Authenticated |
|------|-----------------|---------------|
| Core API | 60/hour | 5,000/hour |
| Search API | 10/minute | 30/minute |

**Tip**: Always use authentication for better limits!

---

## 🔗 Quick Links

- **Repository**: https://github.com/CrazyDubya/research-scrapers
- **Actions Tab**: https://github.com/CrazyDubya/research-scrapers/actions
- **Setup Guide**: [docs/WORKFLOW_SETUP_GUIDE.md](WORKFLOW_SETUP_GUIDE.md)
- **Workflows README**: [.github/workflows/README.md](../.github/workflows/README.md)
- **GitHub API Docs**: https://docs.github.com/en/rest
- **Rate Limits**: https://docs.github.com/en/rest/rate-limit

---

## 💡 Pro Tips

1. **Start small**: Test with single repos before batch operations
2. **Use debug mode**: Enable when troubleshooting issues
3. **Monitor rate limits**: Check before large operations
4. **Set notifications**: Configure email/Slack for important jobs
5. **Clean artifacts**: Review retention periods to manage storage
6. **Use parallel execution**: Enable for batch operations (5x faster)
7. **Check logs first**: Most issues show clearly in workflow logs
8. **Rotate tokens**: Update GitHub tokens every 90 days

---

## 📞 Need Help?

1. ✅ Check [Setup Guide](WORKFLOW_SETUP_GUIDE.md)
2. ✅ Review workflow logs in Actions tab
3. ✅ Enable `--debug` mode
4. ✅ Check [Workflows README](../.github/workflows/README.md)
5. ✅ Create issue with `scraper-failure` label

---

**Quick Start**: Copy and run this now!
```bash
export GITHUB_TOKEN="your_token_here"
python scripts/trigger_workflow.py --mode repository --target microsoft/vscode
```

---

**Status**: ✅ Production Ready  
**Last Updated**: 2025-01-05  
**Version**: 2.0.0