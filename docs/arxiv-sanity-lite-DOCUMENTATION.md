# arxiv-sanity-lite: Comprehensive Documentation

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Component Details](#component-details)
4. [Data Flows](#data-flows)
5. [Database Schema](#database-schema)
6. [API Endpoints](#api-endpoints)
7. [Workflows](#workflows)
8. [Enhancement Recommendations](#enhancement-recommendations)
9. [Optimization Opportunities](#optimization-opportunities)
10. [Deployment Guide](#deployment-guide)

---

## Overview

**arxiv-sanity-lite** is a lightweight web application for browsing, searching, and getting personalized recommendations for academic papers from arXiv. It's a simplified version of arxiv-sanity, designed to help researchers discover relevant papers efficiently.

### Key Features

- **Paper Browsing**: View latest papers from selected CS categories (CV, LG, CL, AI, NE, RO)
- **Full-Text Search**: Search papers by title, authors, and abstract
- **Tag-Based Organization**: Create custom tags to organize papers
- **SVM-Powered Recommendations**: Machine learning-based paper recommendations using TF-IDF features
- **Similar Paper Discovery**: Find papers similar to any given paper
- **Email Recommendations**: Periodic email digests with personalized recommendations
- **Paper Thumbnails**: Visual PDF thumbnails for quick scanning

### Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3, Flask 2.0.2 |
| Database | SQLite with sqlitedict |
| ML/Features | scikit-learn (TF-IDF, SVM) |
| Frontend | React 16, Babel, vanilla CSS |
| External APIs | arXiv API, SendGrid |

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SERVICES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│     ┌─────────────┐                              ┌─────────────────┐        │
│     │  arXiv API  │                              │  SendGrid API   │        │
│     └──────┬──────┘                              └────────┬────────┘        │
│            │                                              │                 │
└────────────┼──────────────────────────────────────────────┼─────────────────┘
             │                                              │
             ▼                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DAEMON PROCESSES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐   │
│  │  arxiv_daemon.py │  │  thumb_daemon.py │  │    send_emails.py        │   │
│  │  (Paper Fetcher) │  │  (PDF→Thumbnail) │  │  (Email Recommendations) │   │
│  └────────┬─────────┘  └────────┬─────────┘  └────────────┬─────────────┘   │
│           │                     │                         │                 │
└───────────┼─────────────────────┼─────────────────────────┼─────────────────┘
            │                     │                         │
            ▼                     ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         data/ directory                               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │ papers.db   │  │  dict.db    │  │ features.p  │  │ static/thumb│  │   │
│  │  │ (papers,    │  │ (tags,      │  │ (TF-IDF     │  │ (thumbnail  │  │   │
│  │  │  metas)     │  │  emails,    │  │  matrix,    │  │  images)    │  │   │
│  │  │             │  │  activity)  │  │  vocab,idf) │  │             │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│           ▲                     ▲                         ▲                 │
└───────────┼─────────────────────┼─────────────────────────┼─────────────────┘
            │                     │                         │
            ▼                     ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           COMPUTE LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                          compute.py                                   │   │
│  │        (TF-IDF Feature Extraction from Paper Abstracts)               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WEB APPLICATION                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                          serve.py (Flask)                             │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │   │
│  │  │   Routes   │  │  Ranking   │  │   Tags     │  │ Authentication │  │   │
│  │  │  Handler   │  │  Engine    │  │  Manager   │  │   (Sessions)   │  │   │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     templates/ (Jinja2)                               │   │
│  │  base.html │ index.html │ profile.html │ inspect.html │ stats.html   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     static/ (Frontend Assets)                         │   │
│  │  style.css │ paper_list.js │ paper_detail.js │ word_list.js          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER BROWSER                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     React Components (Client-Side)                    │   │
│  │       PaperList │ Paper │ TagList │ Tag │ WordList │ Word            │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Module Dependencies

```
aslite/
├── db.py          ← Central data access layer (all file I/O)
└── arxiv.py       ← arXiv API utilities

serve.py           ← Web server (imports db.py)
arxiv_daemon.py    ← Paper fetcher (imports db.py, arxiv.py)
compute.py         ← Feature extraction (imports db.py)
send_emails.py     ← Email service (imports db.py)
thumb_daemon.py    ← Thumbnail generator (imports db.py)
```

---

## Component Details

### 1. arxiv_daemon.py (Paper Fetcher)

**Purpose**: Periodically fetches new papers from arXiv API and stores them in the database.

**Key Behaviors**:
- Queries arXiv for papers in categories: `cs.CV`, `cs.LG`, `cs.CL`, `cs.AI`, `cs.NE`, `cs.RO`
- Fetches papers sorted by `lastUpdatedDate`
- Processes 100 papers per batch
- Implements retry logic with exponential backoff (up to 1000 retries)
- Early termination after N consecutive batches with no new papers

**Command-Line Arguments**:
| Argument | Default | Description |
|----------|---------|-------------|
| `-n, --num` | 100 | Maximum papers to fetch |
| `-s, --start` | 0 | Starting index for pagination |
| `-b, --break-after` | 3 | Stop after N consecutive zero-new batches |

**Execution Flow**:
```
1. Initialize database connections (papers.db)
2. For each batch of 100 papers:
   a. Query arXiv API
   b. Parse XML response via feedparser
   c. For each paper:
      - If new: store in database
      - If exists but newer version: replace
      - If exists and older: skip
   d. Check early termination condition
   e. Sleep 1-4 seconds between batches
3. Exit with code 0 if updates made, 1 otherwise
```

### 2. compute.py (Feature Extractor)

**Purpose**: Extracts TF-IDF features from paper abstracts for ML-based recommendations.

**Key Behaviors**:
- Combines title + abstract + author names into documents
- Uses scikit-learn's `TfidfVectorizer`
- Generates sparse feature matrix
- Configurable vocabulary size and document frequency thresholds

**TF-IDF Configuration**:
```python
TfidfVectorizer(
    lowercase=True,
    analyzer='word',
    stop_words='english',
    token_pattern=r'(?u)\b[a-zA-Z_][a-zA-Z0-9_]+\b',
    ngram_range=(1, 2),      # unigrams and bigrams
    max_features=20000,       # vocabulary size
    norm='l2',
    use_idf=True,
    smooth_idf=True,
    sublinear_tf=True,       # log(1 + tf)
    max_df=0.1,              # ignore terms in >10% of docs
    min_df=5                 # ignore terms in <5 docs
)
```

**Output Structure** (`features.p`):
```python
{
    'pids': list,      # Paper IDs in order
    'x': sparse_matrix, # TF-IDF matrix (n_papers x n_features)
    'vocab': dict,     # word -> index mapping
    'idf': array       # IDF values per feature
}
```

### 3. serve.py (Web Server)

**Purpose**: Flask web application serving the user interface and API endpoints.

**Key Components**:

#### Global State Management
- `get_papers()`: Lazy-loads paper database for request
- `get_metas()`: Lazy-loads metadata database for request
- `get_tags()`: Retrieves user's tags from database
- User sessions tracked via Flask's `session` object

#### Ranking Functions

| Function | Description | Returns |
|----------|-------------|---------|
| `search_rank(q)` | Full-text search with weighted scoring | (pids, scores) |
| `svm_rank(tags, pid, C)` | SVM-based recommendations | (pids, scores, words) |
| `time_rank()` | Sort by submission time | (pids, scores) |
| `random_rank()` | Random shuffle | (pids, scores) |

**Search Scoring Algorithm**:
```python
score = 0.0
score += 10.0 * unique_matches_in_authors
score += 20.0 * unique_matches_in_title
score += 1.0 * total_matches_in_abstract (capped at 3 per term)
```

**SVM Recommendation Algorithm**:
```python
1. Load TF-IDF features for all papers
2. Construct positive labels (1.0) for tagged papers or target pid
3. Train LinearSVC with balanced class weights
4. Score all papers using decision_function
5. Sort by score descending
6. Extract top positive/negative SVM weights as "words"
```

### 4. send_emails.py (Email Service)

**Purpose**: Sends personalized paper recommendations via email.

**Key Behaviors**:
- Uses SendGrid API for email delivery
- Generates SVM recommendations per user tag
- Merges recommendations across tags using MAX score
- Filters to recent papers only (configurable days)
- HTML email template with inline CSS

**Command-Line Arguments**:
| Argument | Default | Description |
|----------|---------|-------------|
| `-n, --num-recommendations` | 20 | Papers per email |
| `-t, --time-delta` | 3 | Recent papers (days) |
| `-d, --dry-run` | 0 | Test mode (no emails sent) |
| `-u, --user` | '' | Single user (for debugging) |
| `-m, --min-papers` | 1 | Minimum tagged papers required |

### 5. thumb_daemon.py (Thumbnail Generator)

**Purpose**: Downloads PDFs and generates thumbnail images for the UI.

**Key Behaviors**:
- Processes most recent 5,000 papers
- Downloads PDF from arXiv
- Converts first 8 pages to PNG thumbnails using ImageMagick
- Concatenates pages into single horizontal strip
- 20-second timeout per PDF conversion

**External Dependencies**:
- `convert` (ImageMagick) - PDF to PNG conversion
- `montage` (ImageMagick) - Image concatenation

### 6. aslite/db.py (Database Layer)

**Purpose**: Centralizes all file system I/O and database operations.

**Key Features**:
- Atomic file writes using temp files
- Compressed SQLite storage using zlib
- Context managers for safe database access

**Database Functions**:
| Function | Database | Table | Compression |
|----------|----------|-------|-------------|
| `get_papers_db()` | papers.db | papers | Yes (zlib) |
| `get_metas_db()` | papers.db | metas | No |
| `get_tags_db()` | dict.db | tags | Yes (zlib) |
| `get_last_active_db()` | dict.db | last_active | No |
| `get_email_db()` | dict.db | email | No |

### 7. aslite/arxiv.py (arXiv API)

**Purpose**: Utilities for interacting with arXiv API.

**Functions**:
| Function | Description |
|----------|-------------|
| `get_response(query, start)` | Fetch 100 papers from arXiv API |
| `parse_response(response)` | Parse XML feed into paper dicts |
| `parse_arxiv_url(url)` | Extract paper ID and version |
| `encode_feedparser_dict(d)` | Convert feedparser objects |
| `filter_latest_version(idvs)` | Keep only latest paper versions |

---

## Data Flows

### Flow 1: Paper Ingestion Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PAPER INGESTION FLOW                              │
└─────────────────────────────────────────────────────────────────────────┘

     ┌──────────┐         ┌──────────────────┐
     │ arXiv    │  HTTP   │ arxiv_daemon.py  │
     │ API      │◄────────│ get_response()   │
     │          │         │                  │
     └────┬─────┘         └────────┬─────────┘
          │                        │
          │ XML Feed               │ parse_response()
          ▼                        ▼
     ┌──────────────────────────────────────┐
     │           Paper Dict                 │
     │  {                                   │
     │    '_id': '2312.12345',              │
     │    '_time': 1702500000,              │
     │    'title': '...',                   │
     │    'summary': '...',                 │
     │    'authors': [...],                 │
     │    'tags': [{'term': 'cs.CV'}, ...]  │
     │  }                                   │
     └────────────────┬─────────────────────┘
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
   ┌─────────────┐         ┌─────────────┐
   │ papers.db   │         │ papers.db   │
   │ [papers]    │         │ [metas]     │
   │ (compressed)│         │ (_time only)│
   └─────────────┘         └─────────────┘
```

### Flow 2: Feature Computation Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      FEATURE COMPUTATION FLOW                            │
└─────────────────────────────────────────────────────────────────────────┘

   ┌─────────────┐
   │ papers.db   │
   │ [papers]    │
   └──────┬──────┘
          │
          │ for each paper:
          │   title + summary + authors
          ▼
   ┌──────────────────────────────────┐
   │         Document Corpus          │
   │  ["Paper Title Abstract...",     │
   │   "Another Paper Title...",      │
   │   ...]                           │
   └────────────────┬─────────────────┘
                    │
                    │ TfidfVectorizer.fit()
                    ▼
   ┌──────────────────────────────────┐
   │        Trained Vocabulary        │
   │  {'neural': 0, 'network': 1,     │
   │   'deep': 2, 'learning': 3, ...} │
   └────────────────┬─────────────────┘
                    │
                    │ TfidfVectorizer.transform()
                    ▼
   ┌──────────────────────────────────┐
   │      Sparse TF-IDF Matrix        │
   │  Shape: (n_papers, 20000)        │
   │  Format: scipy.sparse.csr_matrix │
   └────────────────┬─────────────────┘
                    │
                    │ save_features()
                    ▼
   ┌─────────────┐
   │ features.p  │
   │ (pickle)    │
   └─────────────┘
```

### Flow 3: User Request Flow (Recommendation)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    USER RECOMMENDATION REQUEST FLOW                      │
└─────────────────────────────────────────────────────────────────────────┘

   ┌──────────┐      GET /?rank=tags&tags=ml
   │  Browser │──────────────────────────────────┐
   └──────────┘                                  │
                                                 ▼
                                    ┌────────────────────┐
                                    │     serve.py       │
                                    │     main()         │
                                    └─────────┬──────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
                    ▼                         ▼                         ▼
          ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
          │   get_tags()    │       │ load_features() │       │  get_papers()   │
          │   (user tags)   │       │  (TF-IDF)       │       │  (paper data)   │
          └────────┬────────┘       └────────┬────────┘       └────────┬────────┘
                   │                         │                         │
                   └─────────────────────────┼─────────────────────────┘
                                             │
                                             ▼
                                   ┌─────────────────────┐
                                   │     svm_rank()      │
                                   │                     │
                                   │  1. Build y labels  │
                                   │  2. Train LinearSVC │
                                   │  3. Score all docs  │
                                   │  4. Sort by score   │
                                   └──────────┬──────────┘
                                              │
                                              ▼
                                   ┌─────────────────────┐
                                   │   Apply Filters     │
                                   │  - time_filter      │
                                   │  - skip_have        │
                                   │  - pagination       │
                                   └──────────┬──────────┘
                                              │
                                              ▼
                                   ┌─────────────────────┐
                                   │   render_pid()      │
                                   │   (for each paper)  │
                                   └──────────┬──────────┘
                                              │
                                              ▼
                                   ┌─────────────────────┐
                                   │  render_template()  │
                                   │   index.html        │
                                   └──────────┬──────────┘
                                              │
                                              ▼
   ┌──────────┐      HTML + JSON (papers, words)
   │  Browser │◄─────────────────────────────────
   └──────────┘
         │
         │  React renders components
         ▼
   ┌─────────────────────────────────────────────┐
   │          Client-Side Rendering              │
   │  PaperList → Paper (for each)              │
   │  TagList → Tag (for each)                  │
   │  WordList → Word (for each)                │
   └─────────────────────────────────────────────┘
```

### Flow 4: Tag Management Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TAG MANAGEMENT FLOW                               │
└─────────────────────────────────────────────────────────────────────────┘

   ┌──────────┐     onClick (+)
   │  Paper   │─────────────────┐
   │Component │                 │
   └──────────┘                 │
                                ▼
                    ┌───────────────────────┐
                    │  prompt("tag name:")  │
                    └───────────┬───────────┘
                                │
                                │ fetch("/add/{pid}/{tag}")
                                ▼
                    ┌───────────────────────┐
                    │     serve.py          │
                    │     add(pid, tag)     │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   get_tags_db('c')    │
                    │   (create mode)       │
                    └───────────┬───────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       │
          ┌─────────────────┐               │
          │ User exists?    │───No──────────┤
          └────────┬────────┘               │
                   │ Yes                    │
                   ▼                        ▼
          ┌─────────────────┐     ┌─────────────────┐
          │ tags_db[user]   │     │ Create empty    │
          │ = {...existing} │     │ tags_db[user]={}│
          └────────┬────────┘     └────────┬────────┘
                   │                       │
                   └───────────┬───────────┘
                               │
                               ▼
                    ┌───────────────────────┐
                    │  d[tag].add(pid)      │
                    │  tags_db[user] = d    │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │     dict.db [tags]    │
                    │     Updated!          │
                    └───────────────────────┘
```

---

## Database Schema

### papers.db

**Table: papers** (CompressedSqliteDict)
```
Key: paper_id (str) - e.g., "2312.12345"
Value: dict (compressed with zlib)
{
    '_id': str,           # Paper ID without version
    '_idv': str,          # Paper ID with version (e.g., "2312.12345v2")
    '_version': int,      # Version number
    '_time': float,       # Unix timestamp of last update
    '_time_str': str,     # Human-readable date (e.g., "Dec 14 2024")
    'title': str,         # Paper title
    'summary': str,       # Abstract text
    'authors': [          # List of authors
        {'name': str},
        ...
    ],
    'tags': [             # arXiv categories
        {'term': str},    # e.g., {'term': 'cs.CV'}
        ...
    ],
    'link': str,          # URL to paper page
    ...                   # Additional feedparser fields
}
```

**Table: metas** (SqliteDict - uncompressed)
```
Key: paper_id (str)
Value: dict
{
    '_time': float        # Unix timestamp (for fast time-based queries)
}
```

### dict.db

**Table: tags** (CompressedSqliteDict)
```
Key: username (str)
Value: dict (compressed)
{
    'tag_name': set([pid1, pid2, ...]),
    'another_tag': set([pid3, pid4, ...]),
    ...
}
```

**Table: last_active** (SqliteDict)
```
Key: username (str)
Value: int (Unix timestamp of last activity)
```

**Table: email** (SqliteDict)
```
Key: username (str)
Value: str (email address, or empty string)
```

### features.p (Pickle file)
```python
{
    'pids': list[str],              # Paper IDs, order matches matrix rows
    'x': scipy.sparse.csr_matrix,   # TF-IDF matrix (n_papers x n_features)
    'vocab': dict[str, int],        # word -> feature index
    'idf': numpy.ndarray            # IDF values (n_features,)
}
```

---

## API Endpoints

### Page Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main paper listing page |
| GET | `/inspect?pid=<id>` | Single paper detail view |
| GET | `/profile` | User profile/login page |
| GET | `/stats` | Database statistics |
| GET | `/about` | About page |

### Main Page Query Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `rank` | search, tags, pid, time, random | Ranking method |
| `q` | string | Search query (triggers rank=search) |
| `tags` | string | Comma-separated tag names, or "all" |
| `pid` | string | Paper ID for similarity search |
| `time_filter` | integer | Filter to papers within N days |
| `skip_have` | yes, no | Hide already-tagged papers |
| `svm_c` | float | SVM regularization parameter |
| `page_number` | integer | Pagination (25 papers per page) |

### Tag Management Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/add/<pid>/<tag>` | Add paper to tag |
| GET | `/sub/<pid>/<tag>` | Remove paper from tag |
| GET | `/del/<tag>` | Delete entire tag |

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/login` | Login with username (no password) |
| GET | `/logout` | Clear session |
| POST | `/register_email` | Set email for recommendations |

---

## Workflows

### Workflow 1: Initial Setup

```bash
# 1. Clone repository
git clone https://github.com/karpathy/arxiv-sanity-lite.git
cd arxiv-sanity-lite

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create data directory
mkdir -p data

# 4. Fetch initial papers
python arxiv_daemon.py -n 10000

# 5. Compute features
python compute.py

# 6. Generate thumbnails (optional, requires ImageMagick)
python thumb_daemon.py

# 7. Create secret key for sessions
python -c "import secrets; print(secrets.token_urlsafe(16))" > secret_key.txt

# 8. Start server
python serve.py
# or: flask run --host=0.0.0.0 --port=5000
```

### Workflow 2: Daily Update (Cron)

```bash
# Recommended crontab entries:

# Fetch new papers every 30 minutes
*/30 * * * * cd /path/to/arxiv-sanity-lite && python arxiv_daemon.py >> /var/log/arxiv-fetch.log 2>&1

# Recompute features daily at 3 AM
0 3 * * * cd /path/to/arxiv-sanity-lite && python compute.py >> /var/log/arxiv-compute.log 2>&1

# Generate thumbnails daily at 4 AM
0 4 * * * cd /path/to/arxiv-sanity-lite && python thumb_daemon.py >> /var/log/arxiv-thumb.log 2>&1

# Send recommendation emails daily at 8 AM
0 8 * * * cd /path/to/arxiv-sanity-lite && python send_emails.py >> /var/log/arxiv-email.log 2>&1
```

### Workflow 3: User Paper Discovery

```
1. User visits homepage (/?rank=time)
   → See latest papers sorted by time

2. User searches for topic (q=transformers)
   → Papers ranked by keyword match score

3. User finds interesting paper, clicks "+"
   → Prompt for tag name → Paper added to tag

4. User clicks tag link (rank=tags&tags=ml)
   → SVM trained on tagged papers
   → All papers ranked by SVM score
   → User discovers similar papers

5. User clicks "similar" on any paper (rank=pid&pid=2312.12345)
   → Find papers similar to specific paper

6. User clicks "inspect" on paper
   → See TF-IDF word weights
   → Understand what features matter
```

### Workflow 4: Email Recommendations

```
1. User logs in with username
2. User goes to /profile
3. User enters email address
4. User tags multiple papers with various tags
5. Daily cron job runs send_emails.py:
   a. For each user with email and tags:
      - Load their tagged papers
      - Train SVM per tag
      - Rank recent papers
      - Merge recommendations (MAX score)
      - Generate HTML email
      - Send via SendGrid
```

---

## Enhancement Recommendations

### High Priority

#### 1. Authentication & Security Improvements

**Current Issue**: Password-less authentication is insecure.

**Recommendations**:
- Implement proper authentication (OAuth2, magic links, or passwords)
- Add CSRF protection to forms
- Use `httponly` and `secure` flags on session cookies
- Add rate limiting to prevent abuse

```python
# Example: Add CSRF protection
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

# Example: Secure session configuration
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)
```

#### 2. Input Validation & Sanitization

**Current Issues**:
- Tag names not validated (could contain special characters)
- Paper IDs not validated in endpoints
- Email validation is minimal

**Recommendations**:
```python
# Add input validation
import re

def validate_tag(tag):
    if not tag or len(tag) > 50:
        return False
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', tag))

def validate_pid(pid):
    return bool(re.match(r'^\d{4}\.\d{4,5}$', pid))
```

#### 3. Error Handling Improvements

**Current Issue**: Many endpoints return plain text errors.

**Recommendations**:
- Return proper HTTP status codes
- Create consistent error response format
- Add user-friendly error pages

```python
from flask import jsonify

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', message="Page not found"), 404

@app.route('/add/<pid>/<tag>')
def add(pid=None, tag=None):
    if g.user is None:
        return jsonify({'error': 'Not authenticated'}), 401
    if not validate_pid(pid):
        return jsonify({'error': 'Invalid paper ID'}), 400
    # ...
```

### Medium Priority

#### 4. Database Optimizations

**Current Issues**:
- Reading entire database into memory for filtering
- No database indexing
- Autocommit on every write

**Recommendations**:
```python
# Add indexing for time-based queries
def get_metas_db_with_index(flag='r'):
    mdb = SqliteDict(PAPERS_DB_FILE, tablename='metas', flag=flag)
    if flag == 'c':
        mdb.conn.execute('CREATE INDEX IF NOT EXISTS idx_time ON metas(_time)')
    return mdb

# Use batch commits for daemon scripts
def store_batch(papers):
    with get_papers_db(flag='c', autocommit=False) as pdb:
        for p in papers:
            pdb[p['_id']] = p
        pdb.commit()
```

#### 5. Caching Layer

**Current Issue**: No caching, every request recomputes.

**Recommendations**:
```python
from functools import lru_cache
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@cache.memoize(timeout=300)  # 5 minutes
def get_recent_papers(days=7):
    # Expensive computation cached
    pass

# Or use Redis for distributed caching
cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0'
})
```

#### 6. Async Processing for Heavy Computations

**Current Issue**: SVM training blocks request.

**Recommendations**:
```python
# Use Celery for background tasks
from celery import Celery

celery = Celery('arxiv', broker='redis://localhost:6379/0')

@celery.task
def compute_recommendations(user_id):
    # Heavy SVM computation
    pass

# Pre-compute recommendations periodically
# instead of on-demand
```

#### 7. API Versioning

**Recommendation**: Add `/api/v1/` prefix for machine-readable endpoints:

```python
@app.route('/api/v1/papers')
def api_papers():
    return jsonify({'papers': papers, 'total': len(papers)})

@app.route('/api/v1/search')
def api_search():
    q = request.args.get('q', '')
    pids, scores = search_rank(q)
    return jsonify({'results': [{'pid': p, 'score': s} for p, s in zip(pids, scores)]})
```

### Low Priority (Nice-to-Have)

#### 8. Frontend Modernization

**Current Issues**:
- React 16 is outdated (current is 18)
- Babel in-browser compilation is slow
- No build system

**Recommendations**:
- Upgrade to React 18
- Add Vite or webpack build system
- Use TypeScript for type safety
- Consider TailwindCSS for styling

#### 9. Full-Text Search Enhancement

**Current Issue**: Simple substring matching.

**Recommendations**:
- Integrate Elasticsearch or Meilisearch
- Add fuzzy matching
- Support boolean operators (AND, OR, NOT)
- Add search result highlighting

#### 10. Export/Import Features

**Recommendations**:
- Export tagged papers to BibTeX
- Export to CSV/JSON
- Import tags from file
- API for integration with reference managers

```python
@app.route('/export/bibtex')
def export_bibtex():
    tags = get_tags()
    pids = set().union(*tags.values())
    bibtex = generate_bibtex(pids)
    return Response(bibtex, mimetype='application/x-bibtex')
```

---

## Optimization Opportunities

### Performance Optimizations

#### 1. Lazy Loading of Features

```python
# Current: Load all features into memory
features = load_features()  # Could be 100MB+

# Better: Memory-mapped numpy arrays
import numpy as np

def load_features_mmap():
    # Store features in numpy format instead of pickle
    x = np.load('data/features.npy', mmap_mode='r')
    return x
```

#### 2. Incremental Feature Updates

```python
# Current: Recompute all features daily
python compute.py  # Processes ALL papers

# Better: Only compute features for new papers
def update_features_incremental():
    existing_pids = set(features['pids'])
    new_papers = [p for p in pdb if p not in existing_pids]
    if new_papers:
        new_features = vectorizer.transform(new_papers)
        # Append to existing matrix
```

#### 3. Database Connection Pooling

```python
# Current: New connection per request
pdb = get_papers_db()

# Better: Connection pool
from sqlalchemy.pool import QueuePool

pool = QueuePool(
    lambda: sqlite3.connect('data/papers.db'),
    pool_size=5,
    max_overflow=10
)
```

#### 4. Pagination at Database Level

```python
# Current: Load all, then slice
pids = list(mdb.keys())  # Could be 100K+
pids = pids[start:end]

# Better: Use LIMIT/OFFSET in SQL
def get_recent_papers_paginated(offset, limit):
    conn = sqlite3.connect('data/papers.db')
    cursor = conn.execute(
        'SELECT key FROM metas ORDER BY value DESC LIMIT ? OFFSET ?',
        (limit, offset)
    )
    return [row[0] for row in cursor]
```

### Scalability Improvements

#### 1. Horizontal Scaling with Read Replicas

```
                    ┌─────────────────┐
                    │   Load Balancer │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
   ┌──────────┐       ┌──────────┐       ┌──────────┐
   │ Flask #1 │       │ Flask #2 │       │ Flask #3 │
   └────┬─────┘       └────┬─────┘       └────┬─────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
                    ┌─────────────────┐
                    │  SQLite (read)  │
                    │  or PostgreSQL  │
                    └─────────────────┘
```

#### 2. Migrate to PostgreSQL for Production

```python
# SQLite is great for simplicity, but PostgreSQL offers:
# - Better concurrent access
# - Full-text search (tsvector)
# - JSON/JSONB columns
# - Better scaling

from sqlalchemy import create_engine
engine = create_engine('postgresql://user:pass@localhost/arxiv')
```

#### 3. CDN for Static Assets

```nginx
# Nginx configuration for static file caching
location /static/ {
    alias /path/to/arxiv-sanity-lite/static/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}

location /static/thumb/ {
    alias /path/to/arxiv-sanity-lite/static/thumb/;
    expires 7d;
}
```

### Code Quality Improvements

#### 1. Add Type Hints

```python
from typing import Dict, List, Tuple, Optional
import numpy as np
from numpy.typing import NDArray

def svm_rank(
    tags: str = '',
    pid: str = '',
    C: float = 0.01
) -> Tuple[List[str], List[float], List[Dict[str, float]]]:
    ...
```

#### 2. Add Logging Throughout

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.route('/add/<pid>/<tag>')
def add(pid, tag):
    logger.info(f"User {g.user} adding paper {pid} to tag {tag}")
    ...
```

#### 3. Add Unit Tests

```python
# tests/test_serve.py
import pytest
from serve import app, search_rank, svm_rank

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_search_rank_empty():
    pids, scores = search_rank('')
    assert pids == []
    assert scores == []

def test_main_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'arxiv-sanity' in response.data
```

---

## Deployment Guide

### Production Deployment with Gunicorn + Nginx

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn (4 workers)
gunicorn -w 4 -b 127.0.0.1:8000 serve:app
```

**Nginx Configuration**:
```nginx
server {
    listen 80;
    server_name arxiv-sanity-lite.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /path/to/arxiv-sanity-lite/static;
        expires 30d;
    }
}
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .
RUN mkdir -p data

EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "serve:app"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./secret_key.txt:/app/secret_key.txt:ro
    environment:
      - FLASK_ENV=production

  daemon:
    build: .
    command: python arxiv_daemon.py -n 1000
    volumes:
      - ./data:/app/data
```

### Systemd Service

```ini
# /etc/systemd/system/arxiv-sanity.service
[Unit]
Description=Arxiv Sanity Lite
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/arxiv-sanity-lite
ExecStart=/usr/local/bin/gunicorn -w 4 -b 127.0.0.1:8000 serve:app
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Appendix

### A. File Manifest

```
arxiv-sanity-lite/
├── serve.py              # Flask web application (495 lines)
├── arxiv_daemon.py       # Paper fetching daemon (108 lines)
├── compute.py            # TF-IDF feature extraction (68 lines)
├── send_emails.py        # Email recommendation service (302 lines)
├── thumb_daemon.py       # PDF thumbnail generator (105 lines)
├── aslite/
│   ├── __init__.py
│   ├── db.py             # Database abstraction (149 lines)
│   └── arxiv.py          # arXiv API utilities (81 lines)
├── templates/
│   ├── base.html         # Base template (46 lines)
│   ├── index.html        # Main page (115 lines)
│   ├── profile.html      # User profile (68 lines)
│   ├── inspect.html      # Paper detail (22 lines)
│   ├── stats.html        # Statistics (31 lines)
│   └── about.html        # About page (28 lines)
├── static/
│   ├── style.css         # Stylesheet (299 lines)
│   ├── paper_list.js     # Paper components (106 lines)
│   ├── paper_detail.js   # Detail component (17 lines)
│   ├── word_list.js      # Word components (33 lines)
│   ├── favicon.png
│   └── search.png
├── data/
│   ├── readme.md
│   ├── papers.db         # (generated)
│   ├── dict.db           # (generated)
│   └── features.p        # (generated)
├── requirements.txt
├── Makefile
├── README.md
├── LICENSE
└── screenshot.jpg
```

### B. Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Flask | 2.0.2 | Web framework |
| feedparser | 6.0.8 | arXiv XML parsing |
| numpy | 1.21.4 | Numerical operations |
| scikit-learn | 1.0.1 | ML (TF-IDF, SVM) |
| sqlitedict | 1.7.0 | SQLite key-value store |
| sendgrid | (any) | Email delivery |
| requests | (any) | HTTP client |

### C. Environment Variables

| Variable | Purpose |
|----------|---------|
| `FLASK_ENV` | development/production |
| `FLASK_DEBUG` | Enable debug mode |
| `SECRET_KEY` | Alternative to secret_key.txt |

---

*Documentation generated: December 2024*
*Version: 1.0*
