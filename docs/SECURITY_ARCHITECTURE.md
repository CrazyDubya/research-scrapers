# Security Architecture for Research-Scrapers

## Overview

This document outlines the comprehensive security architecture for the research-scrapers project, focusing on secure API access, credential management, and integration patterns for GitHub Actions and Linear API.

## Security Principles

### 1. Zero Trust Architecture
- No hardcoded credentials in code or configuration files
- All API access requires explicit authentication
- Principle of least privilege for all integrations

### 2. Defense in Depth
- Multiple layers of security controls
- Environment isolation between development, staging, and production
- Comprehensive logging and monitoring

### 3. Secure by Default
- All workflows require explicit permissions
- Secrets are encrypted at rest and in transit
- Default deny policies for external access

## Credential Management

### GitHub Secrets Configuration

#### Required Secrets
```bash
# GitHub API Access
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Linear API Access  
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional: Enhanced monitoring
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/xxx/xxx
```

#### Secret Security Best Practices
1. **Rotation Policy**: Rotate secrets every 90 days
2. **Scope Limitation**: Use minimal required permissions
3. **Access Logging**: Monitor secret usage in workflow logs
4. **Environment Separation**: Different secrets for different environments

### GitHub Token Permissions

#### Minimum Required Permissions
```yaml
# For repository scraping
permissions:
  contents: read
  metadata: read
  
# For issue/PR scraping  
permissions:
  contents: read
  issues: read
  pull-requests: read
  
# For workflow execution
permissions:
  actions: read
  id-token: write  # For OIDC authentication
```

### Linear API Key Setup

#### Creating Linear API Key
1. Go to Linear Settings → API
2. Create new Personal API Key
3. Set appropriate scopes:
   - `read` - Read issues and projects
   - `write` - Update issues and add comments
4. Store securely in GitHub Secrets

## Workflow Security Architecture

### 1. Scheduled Workflow Security

#### Environment Isolation
```yaml
env:
  # Controlled environment variables
  PYTHON_VERSION: '3.11'
  CACHE_KEY_PREFIX: 'research-scraper-v1'
  
# Runtime security
runs-on: ubuntu-latest  # Use GitHub-hosted runners
```

#### Permission Model
```yaml
permissions:
  contents: read        # Read repository code
  id-token: write      # OIDC authentication
  actions: read        # Access workflow artifacts
```

### 2. Webhook Security

#### Repository Dispatch Validation
```yaml
on:
  repository_dispatch:
    types: [linear-task-created, linear-task-updated]
```

#### Payload Validation
- Verify webhook source authenticity
- Validate payload structure before processing
- Sanitize all input parameters

### 3. Artifact Security

#### Secure Artifact Handling
```yaml
- name: Upload artifacts
  uses: actions/upload-artifact@v4
  with:
    name: scraper-results-${{ matrix.scraper }}-${{ needs.setup.outputs.run_id }}
    path: |
      output/*.json
      logs/*.log
    retention-days: 30
    compression-level: 9
```

#### Data Classification
- **Public**: Repository metadata, public issue data
- **Internal**: Workflow logs, execution metrics
- **Confidential**: API keys, authentication tokens

## API Security Patterns

### 1. GitHub API Security

#### Rate Limiting
```python
# Authenticated rate limits
AUTHENTICATED_RATE_LIMIT = 5.0  # requests per second
DEFAULT_RATE_LIMIT = 1.0        # requests per second (unauthenticated)

# Implement exponential backoff
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 0.3
```

#### Request Security
```python
# Secure headers
headers = {
    'Authorization': f'token {github_token}',
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'research-scrapers/1.0'
}

# Timeout configuration
timeout = 30  # seconds
```

### 2. Linear API Security

#### GraphQL Security
```python
class LinearAPIClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Linear API key is required")
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": api_key
        }
    
    def execute_query(self, query: str, variables: Optional[Dict] = None):
        # Input validation
        if not query.strip():
            raise ValueError("Query cannot be empty")
        
        # Request timeout
        with urllib.request.urlopen(req, timeout=30) as response:
            # Response validation
            result = json.loads(response.read().decode('utf-8'))
            if 'errors' in result:
                raise Exception(f"GraphQL errors: {result['errors']}")
```

#### Query Sanitization
```python
# Prevent injection attacks
def sanitize_input(user_input: str) -> str:
    # Remove control characters
    sanitized = ''.join(char for char in user_input if ord(char) >= 32)
    # Limit length
    return sanitized[:1000]
```

## Network Security

### 1. HTTPS Enforcement
- All API calls use HTTPS/TLS 1.2+
- Certificate validation enabled
- No HTTP fallback allowed

### 2. Egress Control
```yaml
# Allowed external endpoints
allowed_endpoints:
  - api.github.com
  - api.linear.app
  - pypi.org (for dependencies)
```

### 3. Request Validation
```python
# Validate URLs before making requests
def validate_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return (
        parsed.scheme in ['https'] and
        parsed.netloc in ALLOWED_HOSTS and
        not parsed.netloc.startswith('localhost')
    )
```

## Data Protection

### 1. Data Classification

#### Sensitivity Levels
- **Public**: Open source repository data
- **Internal**: Workflow execution data
- **Restricted**: API keys, personal tokens
- **Confidential**: Private repository data

### 2. Data Handling

#### In Transit
- TLS 1.2+ for all API communications
- Certificate pinning for critical endpoints
- Request/response logging (excluding sensitive data)

#### At Rest
- GitHub Secrets encryption
- Temporary file encryption in workflows
- Secure artifact storage

#### Processing
```python
# Secure data processing
def process_sensitive_data(data: Dict) -> Dict:
    # Remove sensitive fields
    sensitive_fields = ['token', 'key', 'password', 'secret']
    
    cleaned_data = {}
    for key, value in data.items():
        if not any(field in key.lower() for field in sensitive_fields):
            cleaned_data[key] = value
    
    return cleaned_data
```

## Monitoring and Logging

### 1. Security Monitoring

#### Workflow Monitoring
```yaml
- name: Security scan
  run: |
    # Check for exposed secrets
    if grep -r "ghp_\|lin_api_" . --exclude-dir=.git; then
      echo "::error::Potential secret exposure detected"
      exit 1
    fi
```

#### API Usage Monitoring
```python
# Log API usage without exposing credentials
logger.info(f"API request: {method} {sanitized_url} - Status: {response.status_code}")
```

### 2. Audit Logging

#### Workflow Audit Trail
- All workflow executions logged
- Parameter tracking (sanitized)
- Success/failure metrics
- Performance monitoring

#### API Audit Trail
```python
def audit_api_call(endpoint: str, method: str, status: int, duration: float):
    audit_log = {
        'timestamp': datetime.utcnow().isoformat(),
        'endpoint': sanitize_url(endpoint),
        'method': method,
        'status_code': status,
        'duration_ms': duration * 1000,
        'user_agent': 'research-scrapers/1.0'
    }
    logger.info(f"API_AUDIT: {json.dumps(audit_log)}")
```

## Incident Response

### 1. Security Incident Types
- Credential compromise
- Unauthorized API access
- Data exposure
- Workflow manipulation

### 2. Response Procedures

#### Immediate Actions
1. **Revoke Compromised Credentials**
   ```bash
   # Rotate GitHub token
   gh auth refresh --scopes repo,read:org
   
   # Rotate Linear API key
   # Manual process in Linear settings
   ```

2. **Disable Affected Workflows**
   ```bash
   # Disable workflow
   gh workflow disable research-scraper-scheduled.yml
   ```

3. **Audit Recent Activity**
   ```bash
   # Check recent workflow runs
   gh run list --workflow=research-scraper-scheduled.yml --limit=50
   ```

### 3. Recovery Procedures
1. Update secrets with new credentials
2. Review and update security policies
3. Re-enable workflows after validation
4. Document lessons learned

## Compliance and Governance

### 1. Security Reviews
- Monthly security architecture review
- Quarterly penetration testing
- Annual third-party security audit

### 2. Change Management
- All security changes require approval
- Security impact assessment for new features
- Rollback procedures for security incidents

### 3. Documentation Maintenance
- Keep security documentation current
- Regular review of security procedures
- Training materials for team members

## Implementation Checklist

### Initial Setup
- [ ] Configure GitHub Secrets
- [ ] Set up Linear API key
- [ ] Deploy security workflows
- [ ] Configure monitoring

### Ongoing Maintenance
- [ ] Monthly secret rotation
- [ ] Quarterly security review
- [ ] Annual architecture assessment
- [ ] Continuous monitoring setup

### Emergency Procedures
- [ ] Incident response plan
- [ ] Credential revocation process
- [ ] Communication procedures
- [ ] Recovery documentation

## Security Contacts

### Internal Team
- **Security Lead**: Stephen Thompson
- **DevOps Lead**: [To be assigned]
- **Architecture Review**: [To be assigned]

### External Resources
- **GitHub Security**: security@github.com
- **Linear Support**: support@linear.app
- **Security Vendor**: [To be determined]

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-04  
**Next Review**: 2025-11-04  
**Owner**: Stephen Thompson