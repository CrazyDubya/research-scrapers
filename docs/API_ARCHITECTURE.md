# API Architecture for Research-Scrapers

## Architecture Overview

The research-scrapers project implements a secure, scalable API architecture that integrates GitHub Actions, Linear API, and research scraping tools. This document outlines the complete architecture, design patterns, and implementation details.

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           External Triggers                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   Scheduled   │  │    Manual    │  │   Linear     │                  │
│  │   (Cron)     │  │   Dispatch   │  │   Webhook    │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
└─────────┼──────────────────┼──────────────────┼─────────────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
          ┌──────────────────▼────────────────────┐
          │    GitHub Actions Orchestration       │
          │  ┌────────────────────────────────┐   │
          │  │  Setup & Validation Job        │   │
          │  │  - Secret validation           │   │
          │  │  - Parameter configuration     │   │
          │  │  - Environment setup           │   │
          │  └────────────┬───────────────────┘   │
          │               │                        │
          │  ┌────────────▼───────────────────┐   │
          │  │  Scraper Execution Matrix      │   │
          │  │  - Python environment setup    │   │
          │  │  - Dependency installation     │   │
          │  │  - Parallel scraper execution  │   │
          │  └────────────┬───────────────────┘   │
          │               │                        │
          │  ┌────────────▼───────────────────┐   │
          │  │  Artifact Management           │   │
          │  │  - Output collection           │   │
          │  │  - Log aggregation             │   │
          │  │  - Secure storage              │   │
          │  └────────────┬───────────────────┘   │
          │               │                        │
          │  ┌────────────▼───────────────────┐   │
          │  │  Linear API Integration        │   │
          │  │  - Result formatting           │   │
          │  │  - Comment creation            │   │
          │  │  - Status updates              │   │
          │  └────────────┬───────────────────┘   │
          │               │                        │
          │  ┌────────────▼───────────────────┐   │
          │  │  Notification & Reporting      │   │
          │  │  - Status summaries            │   │
          │  │  - Error notifications         │   │
          │  │  - Audit logging               │   │
          │  └────────────────────────────────┘   │
          └───────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
     ┌────▼────┐                  ┌─────▼────┐
     │ GitHub  │                  │  Linear  │
     │   API   │                  │   API    │
     └─────────┘                  └──────────┘
```

## Component Architecture

### 1. Workflow Orchestration Layer

#### 1.1 Scheduled Workflow (`research-scraper-scheduled.yml`)

**Purpose**: Primary workflow for executing research scraping tasks

**Triggers**:
- Schedule: Daily at 2 AM UTC
- Manual dispatch with parameters
- Repository dispatch events

**Jobs**:
1. **Setup Job**
   - Validates secrets and permissions
   - Configures execution parameters
   - Generates unique run identifiers

2. **Scraper Execution Job**
   - Matrix strategy for parallel execution
   - Environment isolation per scraper
   - Result validation and artifact creation

3. **Linear Update Job**
   - Artifact collection and processing
   - Result formatting for Linear
   - API communication and error handling

4. **Notification Job**
   - Status aggregation
   - Summary generation
   - Alert distribution

#### 1.2 Webhook Trigger Workflow (`linear-webhook-trigger.yml`)

**Purpose**: Handle Linear webhook events and trigger scraper workflows

**Features**:
- Payload parsing and validation
- Automatic scraper type detection
- Workflow dispatch with parameters
- Status feedback to Linear

### 2. API Integration Layer

#### 2.1 GitHub API Client

**Implementation**: Built into scraper modules

**Features**:
```python
class GitHubAPIClient:
    """
    Secure GitHub API client with rate limiting and error handling.
    """
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.session = self._create_session()
        self.rate_limiter = RateLimiter(rate=5.0)
    
    def _create_session(self) -> requests.Session:
        """Create configured session with security headers."""
        session = requests.Session()
        session.headers.update({
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'research-scrapers/1.0'
        })
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        
        return session
    
    @rate_limit
    def request(self, method: str, endpoint: str, **kwargs):
        """Execute rate-limited API request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(
                method, url, timeout=30, **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
```

**Rate Limiting Strategy**:
- Authenticated: 5 requests/second
- Unauthenticated: 1 request/second
- Exponential backoff on 429 responses
- Request queuing for burst protection

#### 2.2 Linear API Client

**Implementation**: `scripts/update_linear_task.py`

**Architecture**:
```python
class LinearAPIClient:
    """
    GraphQL client for Linear API with security and error handling.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.linear.app/graphql"
        self.headers = self._build_headers()
    
    def execute_query(self, query: str, variables: dict = None) -> dict:
        """
        Execute GraphQL query with validation and error handling.
        """
        # Input validation
        self._validate_query(query)
        
        # Prepare request
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        # Execute with retry logic
        for attempt in range(3):
            try:
                response = self._send_request(payload)
                return self._process_response(response)
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
    
    def get_issue(self, issue_id: str) -> dict:
        """Fetch issue details by ID."""
        query = """
        query GetIssue($id: String!) {
          issue(id: $id) {
            id identifier title description
            state { id name }
            team { id name }
          }
        }
        """
        return self.execute_query(query, {"id": issue_id})
    
    def update_issue(self, issue_id: str, updates: dict) -> bool:
        """Update issue with provided changes."""
        mutation = """
        mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
          issueUpdate(id: $id, input: $input) {
            success
            issue { id }
          }
        }
        """
        result = self.execute_query(mutation, {
            "id": issue_id,
            "input": updates
        })
        return result.get('issueUpdate', {}).get('success', False)
    
    def add_comment(self, issue_id: str, body: str) -> bool:
        """Add comment to issue."""
        mutation = """
        mutation CreateComment($issueId: String!, $body: String!) {
          commentCreate(input: {issueId: $issueId, body: $body}) {
            success
            comment { id }
          }
        }
        """
        result = self.execute_query(mutation, {
            "issueId": issue_id,
            "body": body
        })
        return result.get('commentCreate', {}).get('success', False)
```

**Query Design Patterns**:

1. **Batched Updates**:
```graphql
mutation BatchUpdate($updates: [IssueUpdateInput!]!) {
  issues: issuesUpdate(updates: $updates) {
    success
    issues { id }
  }
}
```

2. **Optimized Queries**:
```graphql
query GetIssueWithComments($id: String!) {
  issue(id: $id) {
    id title description
    comments(first: 50) {
      nodes { id body createdAt }
    }
  }
}
```

### 3. Data Processing Layer

#### 3.1 Scraper Results Processor

**Architecture**:
```python
class ScraperResultsProcessor:
    """
    Process and format scraper results for various outputs.
    """
    
    @staticmethod
    def load_artifacts(artifacts_dir: Path) -> Dict[str, Any]:
        """Load all artifacts from directory."""
        results = {}
        for json_file in artifacts_dir.rglob("*.json"):
            scraper_type = json_file.stem.split('_')[0]
            results[scraper_type] = json.load(open(json_file))
        return results
    
    @staticmethod
    def format_for_linear(results: Dict, metadata: Dict) -> str:
        """Format results as Linear markdown."""
        return LinearFormatter.format(results, metadata)
    
    @staticmethod
    def format_for_json(results: Dict) -> str:
        """Format results as JSON."""
        return json.dumps(results, indent=2, ensure_ascii=False)
    
    @staticmethod
    def format_for_csv(results: Dict) -> str:
        """Format results as CSV."""
        return CSVFormatter.format(results)
```

#### 3.2 Data Transformation Pipeline

**Flow**:
```
Raw Scraper Output → Validation → Normalization → Enrichment → Formatting
```

**Implementation**:
```python
class DataPipeline:
    """Data transformation pipeline."""
    
    def __init__(self):
        self.validators = [
            SchemaValidator(),
            DataQualityValidator(),
            SecurityValidator()
        ]
        self.transformers = [
            NormalizationTransformer(),
            EnrichmentTransformer(),
            FormattingTransformer()
        ]
    
    def process(self, data: Dict) -> Dict:
        """Execute full pipeline."""
        # Validation
        for validator in self.validators:
            validator.validate(data)
        
        # Transformation
        result = data
        for transformer in self.transformers:
            result = transformer.transform(result)
        
        return result
```

### 4. Security Layer

#### 4.1 Secret Management

**Architecture**:
```yaml
# GitHub Secrets hierarchy
secrets:
  repository:
    - GITHUB_TOKEN
    - LINEAR_API_KEY
  
  environment:
    production:
      - PROD_GITHUB_TOKEN
      - PROD_LINEAR_KEY
    staging:
      - STAGING_GITHUB_TOKEN
      - STAGING_LINEAR_KEY
```

**Access Pattern**:
```python
class SecretManager:
    """Secure secret access and rotation."""
    
    @staticmethod
    def get_secret(name: str, environment: str = None) -> str:
        """Get secret with validation."""
        secret = os.environ.get(name)
        
        if not secret:
            raise ValueError(f"Secret {name} not found")
        
        # Validate format
        if name.endswith('_TOKEN'):
            SecretManager._validate_token(secret)
        elif name.endswith('_KEY'):
            SecretManager._validate_api_key(secret)
        
        return secret
    
    @staticmethod
    def _validate_token(token: str):
        """Validate GitHub token format."""
        if not token.startswith(('ghp_', 'gho_', 'ghs_')):
            raise ValueError("Invalid GitHub token format")
    
    @staticmethod
    def _validate_api_key(key: str):
        """Validate Linear API key format."""
        if not key.startswith('lin_api_'):
            raise ValueError("Invalid Linear API key format")
```

#### 4.2 Request Security

**Implementation**:
```python
class SecureHTTPClient:
    """HTTP client with security controls."""
    
    def __init__(self):
        self.session = self._create_secure_session()
    
    def _create_secure_session(self):
        """Create session with security configuration."""
        session = requests.Session()
        
        # SSL/TLS configuration
        session.verify = True  # Verify SSL certificates
        session.cert = None    # No client certificates
        
        # Security headers
        session.headers.update({
            'User-Agent': 'research-scrapers/1.0',
            'Accept': 'application/json',
            'X-Request-ID': str(uuid.uuid4())
        })
        
        # Timeout configuration
        session.timeout = (10, 30)  # (connect, read)
        
        return session
    
    def request(self, method: str, url: str, **kwargs):
        """Execute secure HTTP request."""
        # URL validation
        self._validate_url(url)
        
        # Request signing (if required)
        kwargs = self._sign_request(kwargs)
        
        # Execute with error handling
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.SSLError:
            logger.error("SSL verification failed")
            raise
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            raise
    
    def _validate_url(self, url: str):
        """Validate URL for security."""
        parsed = urllib.parse.urlparse(url)
        
        # Only HTTPS allowed
        if parsed.scheme != 'https':
            raise ValueError("Only HTTPS URLs allowed")
        
        # Whitelist domains
        allowed_domains = [
            'api.github.com',
            'api.linear.app'
        ]
        
        if parsed.netloc not in allowed_domains:
            raise ValueError(f"Domain {parsed.netloc} not allowed")
```

## Integration Patterns

### Pattern 1: Polling (Scheduled Execution)

```yaml
# Execute on schedule
on:
  schedule:
    - cron: '0 2 * * *'

# Best for:
# - Regular background tasks
# - Batch processing
# - Non-time-critical updates
```

### Pattern 2: Push (Webhook Integration)

```yaml
# Execute on external event
on:
  repository_dispatch:
    types: [linear-task-created]

# Best for:
# - Real-time responses
# - Event-driven workflows
# - User-initiated tasks
```

### Pattern 3: Hybrid (Manual + Automated)

```yaml
# Combined triggers
on:
  schedule: [...]
  workflow_dispatch: [...]
  repository_dispatch: [...]

# Best for:
# - Flexible execution
# - Testing and debugging
# - Production workloads
```

## Performance Optimization

### 1. Caching Strategy

```yaml
- name: Cache Python dependencies
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
```

### 2. Parallel Execution

```yaml
strategy:
  matrix:
    scraper: [github_repo, github_issue, github_user]
  max-parallel: 3
```

### 3. Artifact Compression

```yaml
- uses: actions/upload-artifact@v4
  with:
    compression-level: 9  # Maximum compression
```

## Monitoring and Observability

### 1. Metrics Collection

```python
class MetricsCollector:
    """Collect execution metrics."""
    
    def record_execution(self, scraper: str, duration: float, 
                        status: str, records: int):
        """Record scraper execution metrics."""
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'scraper': scraper,
            'duration_seconds': duration,
            'status': status,
            'records_processed': records
        }
        logger.info(f"METRICS: {json.dumps(metrics)}")
```

### 2. Error Tracking

```python
class ErrorTracker:
    """Track and categorize errors."""
    
    def track_error(self, error: Exception, context: dict):
        """Record error with context."""
        error_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'stack_trace': traceback.format_exc()
        }
        logger.error(f"ERROR: {json.dumps(error_data)}")
```

## Scalability Considerations

### Horizontal Scaling
- Matrix strategy for parallel scraper execution
- Multiple workflow instances for different targets
- Distributed artifact storage

### Vertical Scaling
- Configurable resource limits per job
- Memory-efficient data processing
- Streaming for large datasets

### Rate Limiting
- Token bucket algorithm for API calls
- Adaptive rate limiting based on quotas
- Request queuing and prioritization

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-04  
**Author**: Stephen Thompson