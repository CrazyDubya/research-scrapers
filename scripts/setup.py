#!/usr/bin/env python3
"""Setup script for development environment.

This script helps set up the development environment for the research scrapers project.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Run a shell command and return success status.
    
    Args:
        command: Command to run
        description: Description of what the command does
    
    Returns:
        True if command succeeded, False otherwise
    """
    print(f"\n{description}...")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✓ Success")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible."""
    print("Checking Python version...")
    version = sys.version_info
    
    if version.major == 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("Please use Python 3.8 or higher")
        return False


def create_directories():
    """Create necessary directories."""
    print("\nCreating directories...")
    
    directories = [
        'output',
        'logs',
        'data',
        'temp'
    ]
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(exist_ok=True)
        print(f"✓ Created/verified: {path}")


def create_env_file():
    """Create example .env file."""
    env_file = Path('.env')
    
    if env_file.exists():
        print("\n.env file already exists")
        return
    
    print("\nCreating example .env file...")
    
    env_content = '''# Research Scrapers Configuration

# HTTP Settings
SCRAPER_REQUEST_TIMEOUT=30
SCRAPER_MAX_RETRIES=3
SCRAPER_RATE_LIMIT=1.0
SCRAPER_USER_AGENT="Research Scrapers Bot 1.0"

# Logging
SCRAPER_LOG_LEVEL=INFO
# SCRAPER_LOG_FILE=logs/scraper.log

# Output
SCRAPER_OUTPUT_DIR=output

# Proxy (uncomment and configure if needed)
# SCRAPER_PROXY=http://proxy.example.com:8080
# SCRAPER_PROXY_USERNAME=username
# SCRAPER_PROXY_PASSWORD=password

# API Keys (add your actual keys)
# GITHUB_API_KEY=your_github_token_here
# TWITTER_API_KEY=your_twitter_token_here
# REDDIT_API_KEY=your_reddit_token_here

# Database (uncomment and configure if needed)
# DATABASE_URL=postgresql://user:password@localhost:5432/research_db
'''
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"✓ Created {env_file}")
    print("  Please edit this file to add your actual API keys and configuration")


def install_dependencies():
    """Install Python dependencies."""
    commands = [
        ("pip install --upgrade pip", "Upgrading pip"),
        ("pip install -r requirements.txt", "Installing dependencies"),
        ("pip install -e .", "Installing package in development mode")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True


def setup_pre_commit():
    """Setup pre-commit hooks."""
    pre_commit_config = Path('.pre-commit-config.yaml')
    
    if not pre_commit_config.exists():
        print("\nCreating pre-commit configuration...")
        
        config_content = '''repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
  
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]
'''
        
        with open(pre_commit_config, 'w') as f:
            f.write(config_content)
        
        print(f"✓ Created {pre_commit_config}")
    
    # Install pre-commit hooks
    return run_command("pre-commit install", "Installing pre-commit hooks")


def run_tests():
    """Run the test suite."""
    return run_command("python -m pytest tests/ -v", "Running tests")


def main():
    """Main setup function."""
    print("Research Scrapers Development Environment Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Create .env file
    create_env_file()
    
    # Install dependencies
    if not install_dependencies():
        print("\n✗ Failed to install dependencies")
        sys.exit(1)
    
    # Setup pre-commit (optional)
    setup_pre_commit()
    
    # Run tests
    if run_tests():
        print("\n✓ All tests passed!")
    else:
        print("\n⚠ Some tests failed, but setup is complete")
    
    print("\n" + "=" * 50)
    print("Setup complete! 🎉")
    print("\nNext steps:")
    print("1. Edit .env file with your API keys and configuration")
    print("2. Run example scripts in the scripts/ directory")
    print("3. Check out the documentation in docs/")
    print("\nHappy scraping!")


if __name__ == '__main__':
    main()
