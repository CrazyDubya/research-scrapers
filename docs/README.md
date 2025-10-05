# Research Scrapers Documentation

Comprehensive documentation for the research scrapers package.

## Table of Contents

- [Getting Started](getting-started.md)
- [Quick Start Guide](QUICK_START.md)
- [Configuration](configuration.md)
- [Integration Guide](INTEGRATION_GUIDE.md)
- [API Architecture](API_ARCHITECTURE.md)
- [Security Architecture](SECURITY_ARCHITECTURE.md)
- [Contributing](contributing.md)
- [Roadmap](../ROADMAP.md)

## Quick Links

- [Installation Guide](getting-started.md#installation)
- [Basic Usage](getting-started.md#basic-usage)
- [Configuration Options](configuration.md)
- [Integration Patterns](INTEGRATION_GUIDE.md)
- [Platform Roadmap](../ROADMAP.md)

## 🚀 What's New

### Linear Integration (RUB-50)
We're actively developing a comprehensive Linear API integration. See the [Roadmap](../ROADMAP.md) for:
- Detailed feature specifications
- Implementation timeline
- Usage examples and architecture
- Track progress: [Linear Project RUB-50](https://linear.app/rubberducky/issue/RUB-50)

### Enhanced Documentation
- **Notion Workspace**: Detailed project planning and requirements documentation
- **Integration Guides**: Platform-specific integration patterns
- **Architecture Docs**: System design and security architecture

## Documentation Structure

```
docs/
├── README.md                    # This file
├── getting-started.md           # Installation and basic usage
├── QUICK_START.md               # Quick start guide
├── configuration.md             # Configuration options
├── contributing.md              # Development guidelines
├── INTEGRATION_GUIDE.md         # Platform integration patterns
├── API_ARCHITECTURE.md          # System architecture and design
└── SECURITY_ARCHITECTURE.md     # Security best practices
```

## Core Documentation

### [Getting Started](getting-started.md)
Learn how to install and set up the research scrapers package.

**Topics Covered:**
- Installation methods
- Basic configuration
- First scraping example
- Common use cases

### [Quick Start Guide](QUICK_START.md)
Rapid introduction to get scraping quickly.

**Topics Covered:**
- 5-minute setup
- Essential examples
- Common patterns
- Troubleshooting basics

### [Configuration](configuration.md)
Detailed information about configuration options.

**Topics Covered:**
- Environment variables
- Configuration files
- Programmatic configuration
- Best practices

### [Integration Guide](INTEGRATION_GUIDE.md)
Comprehensive guide to integrating with various platforms.

**Topics Covered:**
- GitHub API integration
- Linear integration (coming soon - RUB-50)
- Cross-platform synchronization
- Authentication patterns
- Rate limiting strategies

### [API Architecture](API_ARCHITECTURE.md)
System design and architectural patterns.

**Topics Covered:**
- Component architecture
- Data flow diagrams
- API design principles
- Extensibility patterns

### [Security Architecture](SECURITY_ARCHITECTURE.md)
Security best practices and implementation details.

**Topics Covered:**
- Authentication methods
- API key management
- Data privacy
- Security considerations

### [Contributing](contributing.md)
Guidelines for contributing to the project.

**Topics Covered:**
- Development workflow
- Code standards
- Testing requirements
- Pull request process

## Platform-Specific Guides

### GitHub Integration
The GitHub scraper provides production-ready access to GitHub's REST API.

**Key Features:**
- Repository, user, and organization scraping
- Issue and pull request management
- Search functionality
- Rate limit handling

**Documentation:**
- [GitHub API Architecture](API_ARCHITECTURE.md#github-integration)
- [Authentication Setup](SECURITY_ARCHITECTURE.md#github-authentication)
- Examples in main [README](../README.md#github-scraper)

### Linear Integration (RUB-50) - Coming Soon

Comprehensive Linear API integration for project management workflows.

**Planned Features:**
- Issue and project scraping
- Team analytics
- Cross-platform synchronization
- Workflow automation

**Documentation:**
- [Roadmap - Linear Integration](../ROADMAP.md#linear-integration-rub-50---in-planning)
- [Integration Specifications](INTEGRATION_GUIDE.md)
- [Linear Project Tracking](https://linear.app/rubberducky/issue/RUB-50)
- **Notion Documentation**: Contact maintainers for access to detailed planning docs

### Future Integrations

See the [Roadmap](../ROADMAP.md) for planned integrations:
- Notion API
- Jira
- GitLab
- Confluence

## External Resources

### Notion Documentation
Comprehensive project planning and architecture documentation maintained in Notion.

**Access:**
Request access from project maintainers for:
- Detailed Linear integration specifications
- Architecture decision records
- Implementation guides
- API requirements and schemas

### Linear Project Board
Track development progress and upcoming features.

**Links:**
- [RUB-50: Linear Integration](https://linear.app/rubberducky/issue/RUB-50)
- Sprint planning and milestones
- Feature prioritization

## Examples & Tutorials

### Basic Examples
```python
# Simple web scraping
from research_scrapers import WebScraper

scraper = WebScraper()
result = scraper.scrape('https://example.com')
print(result)
```

### GitHub Integration
```python
# GitHub repository scraping
from research_scrapers import GitHubScraper

with GitHubScraper() as scraper:
    repo = scraper.scrape_repository("facebook", "react")
    print(f"Stars: {repo['stargazers_count']}")
```

### Coming Soon: Linear Integration
```python
# Linear issue scraping (RUB-50)
from research_scrapers import LinearScraper

scraper = LinearScraper(api_key="lin_api_xxx")
issues = scraper.scrape_issues(team_key="RUB")
```

For more examples, see:
- Main [README Examples](../README.md#examples)
- [Integration Guide](INTEGRATION_GUIDE.md)
- [Quick Start Guide](QUICK_START.md)

## API Reference

Comprehensive API documentation is being developed. Current resources:

- Class documentation in source files
- Inline docstrings
- [API Architecture document](API_ARCHITECTURE.md)

## Development

### Setting Up Development Environment
```bash
git clone https://github.com/CrazyDubya/research-scrapers.git
cd research-scrapers
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Running Tests
```bash
pytest tests/ -v
pytest tests/ --cov=research_scrapers
```

### Contributing
See [Contributing Guidelines](contributing.md) for detailed information.

## Support & Community

### Getting Help
- 🐛 [Report Issues](https://github.com/CrazyDubya/research-scrapers/issues)
- 💡 [Feature Requests](https://github.com/CrazyDubya/research-scrapers/issues)
- 💬 [Discussions](https://github.com/CrazyDubya/research-scrapers/discussions)
- 📋 [Linear Project Board](https://linear.app/rubberducky/project/rub-50)

### Stay Updated
- Check the [Roadmap](../ROADMAP.md) for upcoming features
- Follow the Linear project for RUB-50 progress
- Review Notion documentation for detailed planning

## License

MIT License - see [LICENSE](../LICENSE) for details.

---

**Last Updated**: January 2025  
**Version**: 1.x (Linear integration coming in 2.0)  
**Maintained By**: Research Scrapers Team
