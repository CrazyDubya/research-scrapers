# Contributing to Research Scrapers

We welcome contributions to the Research Scrapers project! This document provides guidelines for contributing.

## Getting Started

### Development Environment Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/research-scrapers.git
   cd research-scrapers
   ```

2. **Set up Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Set up Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

5. **Run Tests**
   ```bash
   pytest
   ```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clean, readable code
- Follow the existing code style
- Add docstrings to new functions and classes
- Include type hints where appropriate

### 3. Add Tests

- Write tests for new functionality
- Ensure existing tests still pass
- Aim for good test coverage

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=research_scrapers --cov-report=html
```

### 4. Update Documentation

- Update docstrings
- Add examples if appropriate
- Update README.md if needed
- Add entries to docs/ if adding major features

### 5. Code Quality Checks

```bash
# Format code
black src/ tests/ scripts/

# Sort imports
isort src/ tests/ scripts/

# Lint code
flake8 src/ tests/ scripts/

# Type checking
mypy src/research_scrapers/
```

### 6. Commit Your Changes

```bash
git add .
git commit -m "Add feature: your feature description"
```

**Commit Message Guidelines:**
- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues and pull requests when applicable

### 7. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Code Style Guidelines

### Python Code Style

- Follow PEP 8
- Use Black for code formatting (line length: 88)
- Use isort for import sorting
- Use type hints where possible
- Write comprehensive docstrings

### Docstring Style

Use Google-style docstrings:

```python
def example_function(param1: str, param2: int = 0) -> bool:
    """Brief description of the function.
    
    Longer description if needed. Explain the purpose,
    behavior, and any important details.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (default: 0)
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is not an integer
    
    Example:
        >>> result = example_function("hello", 42)
        >>> print(result)
        True
    """
    pass
```

### Testing Guidelines

- Write unit tests for all new functions and classes
- Use descriptive test names
- Test both success and failure cases
- Use mocking for external dependencies
- Group related tests in classes

```python
class TestWebScraper:
    """Test cases for WebScraper class."""
    
    def test_init_with_default_config(self):
        """Test initialization with default config."""
        scraper = WebScraper()
        assert scraper.config is not None
    
    @requests_mock.Mocker()
    def test_get_page_success(self, m):
        """Test successful page retrieval."""
        # Test implementation
        pass
```

## Types of Contributions

### Bug Reports

When reporting bugs, please include:

- Python version
- Operating system
- Package version
- Minimal code example that reproduces the issue
- Full error traceback
- Expected vs actual behavior

### Feature Requests

When requesting features:

- Describe the use case
- Explain why the feature would be useful
- Provide examples of how it would be used
- Consider backward compatibility

### Code Contributions

We welcome:

- Bug fixes
- New features
- Performance improvements
- Documentation improvements
- Test improvements
- Example scripts

## Project Structure

```
research-scrapers/
├── src/research_scrapers/    # Main package code
├── tests/                   # Test files
├── docs/                    # Documentation
├── scripts/                 # Example scripts
├── requirements.txt         # Dependencies
├── setup.py                 # Package setup
├── pyproject.toml          # Modern Python packaging
└── pytest.ini              # Test configuration
```

## Adding New Scrapers

When adding new scraper classes:

1. **Inherit from BaseScraper**
   ```python
   class CustomScraper(BaseScraper):
       def scrape(self, *args, **kwargs):
           # Implementation
           pass
   ```

2. **Add Configuration Options**
   - Add new config options to `Config` class
   - Document the options
   - Provide sensible defaults

3. **Write Comprehensive Tests**
   - Test initialization
   - Test scraping functionality
   - Test error handling
   - Mock external dependencies

4. **Add Documentation**
   - Update API reference
   - Add usage examples
   - Update README if needed

5. **Add Example Script**
   - Create example in `scripts/`
   - Show practical usage
   - Include error handling

## Release Process

1. **Update Version Numbers**
   - `setup.py`
   - `pyproject.toml`
   - `src/research_scrapers/__init__.py`

2. **Update Changelog**
   - Add new features
   - List bug fixes
   - Note breaking changes

3. **Run Full Test Suite**
   ```bash
   pytest tests/ --cov=research_scrapers
   ```

4. **Create Release**
   - Tag the release
   - Create GitHub release
   - Upload to PyPI (if applicable)

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Features**: Open a GitHub Issue with feature request template
- **Security**: Email maintainers directly

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow the Golden Rule

## Recognition

Contributors will be:

- Listed in the README
- Mentioned in release notes
- Given credit in documentation

Thank you for contributing to Research Scrapers! 🎆
