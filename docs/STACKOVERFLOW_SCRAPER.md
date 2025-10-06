# Stack Overflow Scraper

A comprehensive Stack Overflow scraper for extracting questions, answers, user profiles, and tag-based data. Part of the research-scrapers package.

## Features

- **Question Scraping**: Extract complete question data including answers, comments, and metadata
- **User Profile Scraping**: Get user statistics, reputation, badges, and activity
- **Tag-Based Filtering**: Search and filter questions by specific tags
- **Search Functionality**: Search questions using Stack Overflow's search engine
- **Rate Limiting**: Built-in rate limiting to respect Stack Overflow's servers
- **Multiple Output Formats**: Save data as JSON or CSV
- **Comprehensive CLI**: Easy-to-use command-line interface
- **Error Handling**: Robust error handling and retry mechanisms

## Installation

```bash
# Install the package
pip install -e .

# Or use the standalone script
python stackoverflow_scraper.py --help
```

## Quick Start

### Command Line Usage

```bash
# Scrape a single question
python stackoverflow_scraper.py question 12345678

# Scrape questions by tag
python stackoverflow_scraper.py tag python --max-questions 50

# Search questions
python stackoverflow_scraper.py search "machine learning" --max-questions 30

# Scrape user profile
python stackoverflow_scraper.py user 123456

# Scrape from URL
python stackoverflow_scraper.py url "https://stackoverflow.com/questions/12345678/example"
```

### Python API Usage

```python
from research_scrapers import StackOverflowScraper, Config
from research_scrapers.stackoverflow_scraper import ScrapingOptions

# Initialize scraper
config = Config()
scraper = StackOverflowScraper(config)

# Scrape a single question
question_data = scraper.scrape_question("12345678")

# Scrape questions by tag
options = ScrapingOptions(max_questions=20, include_comments=True)
questions = scraper.scrape_questions_by_tag("python", options)

# Scrape user profile
user_data = scraper.scrape_user_profile("123456")

# Search questions
search_results = scraper.search_questions("machine learning", options)
```

## Command Line Interface

### Available Commands

#### `question` - Scrape a Single Question
```bash
python stackoverflow_scraper.py question QUESTION_ID [OPTIONS]
```

**Arguments:**
- `QUESTION_ID`: Stack Overflow question ID (numeric)

**Example:**
```bash
python stackoverflow_scraper.py question 12345678 --output my_question.json
```

#### `tag` - Scrape Questions by Tag
```bash
python stackoverflow_scraper.py tag TAG_NAME [OPTIONS]
```

**Arguments:**
- `TAG_NAME`: Tag to filter by (e.g., python, javascript, machine-learning)

**Options:**
- `--sort {newest,active,votes,frequent}`: Sort order (default: newest)
- `--pages N`: Maximum pages to scrape (default: 5)
- `--max-questions N`: Maximum questions to scrape (default: 100)

**Example:**
```bash
python stackoverflow_scraper.py tag python --sort votes --max-questions 50 --pages 3
```

#### `search` - Search Questions
```bash
python stackoverflow_scraper.py search "QUERY" [OPTIONS]
```

**Arguments:**
- `QUERY`: Search query string

**Options:**
- `--sort {relevance,newest,votes,active}`: Sort order (default: relevance)
- `--pages N`: Maximum pages to scrape (default: 3)
- `--max-questions N`: Maximum questions to scrape (default: 100)

**Example:**
```bash
python stackoverflow_scraper.py search "neural networks tensorflow" --sort votes --max-questions 25
```

#### `user` - Scrape User Profile
```bash
python stackoverflow_scraper.py user USER_ID [OPTIONS]
```

**Arguments:**
- `USER_ID`: Stack Overflow user ID (numeric)

**Example:**
```bash
python stackoverflow_scraper.py user 123456 --output user_profile.json
```

#### `url` - Scrape from URL
```bash
python stackoverflow_scraper.py url "URL" [OPTIONS]
```

**Arguments:**
- `URL`: Stack Overflow URL to scrape

**Example:**
```bash
python stackoverflow_scraper.py url "https://stackoverflow.com/questions/12345678/how-to-do-something"
```

### Global Options

All commands support these options:

#### Content Control
- `--no-answers`: Skip scraping answers
- `--no-comments`: Skip scraping comments
- `--no-user-info`: Skip user information
- `--no-tags`: Skip tags
- `--no-votes`: Skip vote counts
- `--no-timestamps`: Skip timestamps

#### Limits
- `--max-answers N`: Maximum answers per question (default: 50)
- `--max-comments N`: Maximum comments per post (default: 20)

#### Output
- `--output FILE`: Output file path (auto-generated if not specified)
- `--format {json,csv}`: Output format (default: json)
- `--verbose`: Enable verbose logging

## Configuration

### Environment Variables

```bash
# Rate limiting
export SCRAPER_RATE_LIMIT=1.0  # requests per second

# Request settings
export SCRAPER_REQUEST_TIMEOUT=30
export SCRAPER_MAX_RETRIES=3

# Output settings
export SCRAPER_OUTPUT_DIR=./output
export SCRAPER_LOG_LEVEL=INFO

# User agent
export SCRAPER_USER_AGENT="Custom User Agent"
```

### Configuration File

Create a `config.json` file:

```json
{
  "rate_limit": 1.0,
  "request_timeout": 30,
  "max_retries": 3,
  "output_dir": "./output",
  "log_level": "INFO"
}
```

## Data Structure

### Question Data

```json
{
  "question_id": "12345678",
  "title": "How to do something in Python?",
  "body": "Question body text...",
  "body_html": "<p>Question body HTML...</p>",
  "tags": ["python", "programming"],
  "vote_count": 42,
  "view_count": 1500,
  "answer_count": 3,
  "author": {
    "display_name": "Username",
    "user_id": "123456",
    "reputation": 5000
  },
  "created_at": "2023-01-15T10:30:00Z",
  "last_edited_at": "2023-01-16T14:20:00Z",
  "url": "https://stackoverflow.com/questions/12345678",
  "scraped_at": "2024-01-20T15:45:30",
  "answers": [
    {
      "answer_id": "87654321",
      "body": "Answer text...",
      "body_html": "<p>Answer HTML...</p>",
      "vote_count": 25,
      "is_accepted": true,
      "author": {
        "display_name": "Expert",
        "user_id": "654321",
        "reputation": 15000
      },
      "created_at": "2023-01-15T11:00:00Z",
      "comments": [
        {
          "text": "Great answer!",
          "author": "Commenter",
          "author_user_id": "789012",
          "created_at": "2023-01-15T11:30:00Z",
          "vote_count": 3
        }
      ]
    }
  ],
  "comments": [
    {
      "text": "Could you clarify...?",
      "author": "Questioner",
      "author_user_id": "345678",
      "created_at": "2023-01-15T10:45:00Z",
      "vote_count": 1
    }
  ]
}
```

### User Profile Data

```json
{
  "user_id": "123456",
  "display_name": "Username",
  "reputation": 15000,
  "badges": {
    "gold_badges": 5,
    "silver_badges": 25,
    "bronze_badges": 100
  },
  "questions_asked": 50,
  "answers_given": 200,
  "member_since": "January 15, 2020",
  "location": "San Francisco, CA",
  "profile_url": "https://stackoverflow.com/users/123456",
  "scraped_at": "2024-01-20T15:45:30"
}
```

## Python API Reference

### StackOverflowScraper Class

```python
class StackOverflowScraper(WebScraper):
    def __init__(self, config: Optional[Config] = None)
    
    def scrape_question(self, question_id: Union[int, str], 
                       options: Optional[ScrapingOptions] = None) -> Dict[str, Any]
    
    def scrape_questions_by_tag(self, tag: str, 
                               options: Optional[ScrapingOptions] = None,
                               sort_by: str = 'newest',
                               page_limit: int = 5) -> List[Dict[str, Any]]
    
    def scrape_user_profile(self, user_id: Union[int, str]) -> Dict[str, Any]
    
    def search_questions(self, query: str, 
                        options: Optional[ScrapingOptions] = None,
                        sort_by: str = 'relevance',
                        page_limit: int = 3) -> List[Dict[str, Any]]
```

### ScrapingOptions Class

```python
@dataclass
class ScrapingOptions:
    include_answers: bool = True
    include_comments: bool = True
    include_user_info: bool = True
    include_tags: bool = True
    include_vote_counts: bool = True
    include_timestamps: bool = True
    
    max_questions: int = 100
    max_answers_per_question: int = 50
    max_comments_per_post: int = 20
    
    output_format: str = 'json'
    output_file: Optional[str] = None
    verbose: bool = False
```

## Examples

### Example 1: Research Python Questions

```bash
# Get the most voted Python questions
python stackoverflow_scraper.py tag python \
  --sort votes \
  --max-questions 100 \
  --output python_top_questions.json
```

### Example 2: Analyze Machine Learning Discussions

```bash
# Search for machine learning questions
python stackoverflow_scraper.py search "machine learning tensorflow" \
  --sort votes \
  --max-questions 50 \
  --max-answers 10 \
  --output ml_discussions.json
```

### Example 3: User Research

```bash
# Get profile of a high-reputation user
python stackoverflow_scraper.py user 22656 \
  --output expert_profile.json
```

### Example 4: Comprehensive Question Analysis

```python
from research_scrapers import StackOverflowScraper
from research_scrapers.stackoverflow_scraper import ScrapingOptions

# Setup
scraper = StackOverflowScraper()
options = ScrapingOptions(
    include_answers=True,
    include_comments=True,
    max_answers_per_question=20,
    max_comments_per_post=10
)

# Get questions about a specific topic
questions = scraper.scrape_questions_by_tag("neural-networks", options)

# Analyze the data
total_answers = sum(len(q.get('answers', [])) for q in questions)
avg_votes = sum(q.get('vote_count', 0) for q in questions) / len(questions)

print(f"Scraped {len(questions)} questions")
print(f"Total answers: {total_answers}")
print(f"Average votes: {avg_votes:.1f}")

# Get user profiles of top contributors
top_users = set()
for question in questions:
    if question.get('author', {}).get('user_id'):
        top_users.add(question['author']['user_id'])
    
    for answer in question.get('answers', []):
        if answer.get('author', {}).get('user_id'):
            top_users.add(answer['author']['user_id'])

# Scrape user profiles
user_profiles = []
for user_id in list(top_users)[:10]:  # Limit to top 10
    try:
        profile = scraper.scrape_user_profile(user_id)
        user_profiles.append(profile)
    except Exception as e:
        print(f"Failed to scrape user {user_id}: {e}")

print(f"Scraped {len(user_profiles)} user profiles")
```

## Rate Limiting and Best Practices

### Rate Limiting
- Default: 1 request per second
- Configurable via `SCRAPER_RATE_LIMIT` environment variable
- Built-in exponential backoff for failed requests

### Best Practices
1. **Respect Rate Limits**: Don't set rate limits too high
2. **Use Appropriate Limits**: Set reasonable `max_questions`, `max_answers` limits
3. **Handle Errors**: Always wrap scraping calls in try-catch blocks
4. **Save Incrementally**: For large scraping jobs, save data periodically
5. **Monitor Resources**: Watch memory usage for large datasets

### Error Handling

```python
from research_scrapers import StackOverflowScraper
from research_scrapers.stackoverflow_scraper import ScrapingOptions

scraper = StackOverflowScraper()

try:
    questions = scraper.scrape_questions_by_tag("python", 
                                               ScrapingOptions(max_questions=10))
    print(f"Successfully scraped {len(questions)} questions")
except Exception as e:
    print(f"Scraping failed: {e}")
finally:
    scraper.close()
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Install package in development mode
   pip install -e .
   ```

2. **Rate Limiting Issues**
   ```bash
   # Reduce rate limit
   export SCRAPER_RATE_LIMIT=0.5
   ```

3. **Memory Issues with Large Datasets**
   ```python
   # Use smaller batch sizes
   options = ScrapingOptions(max_questions=20, max_answers_per_question=10)
   ```

4. **Network Timeouts**
   ```bash
   # Increase timeout
   export SCRAPER_REQUEST_TIMEOUT=60
   ```

### Debug Mode

```bash
# Enable verbose logging
python stackoverflow_scraper.py tag python --verbose --max-questions 5
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### Version 1.0.0
- Initial release
- Question scraping with answers and comments
- User profile scraping
- Tag-based filtering
- Search functionality
- CLI interface
- JSON and CSV output formats