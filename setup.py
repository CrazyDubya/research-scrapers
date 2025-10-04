#!/usr/bin/env python3
"""Setup script for the research scrapers package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
with open('requirements.txt', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            # Remove version constraints for setup.py
            package = line.split('>=')[0].split('==')[0].split('<')[0]
            requirements.append(package)

setup(
    name="research-scrapers",
    version="0.1.0",
    author="Stephen Thompson",
    author_email="your.email@example.com",
    description="A comprehensive toolkit for scraping and analyzing data from various research sources",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CrazyDubya/research-scrapers",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.11.0",
            "requests-mock>=1.11.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "pre-commit>=3.4.0",
        ],
        "selenium": [
            "selenium>=4.15.0",
            "webdriver-manager>=4.0.0",
        ],
        "async": [
            "aiohttp>=3.8.0",
            "aiofiles>=23.0.0",
        ],
        "database": [
            "sqlalchemy>=2.0.0",
            "psycopg2-binary>=2.9.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "research-scraper=research_scrapers.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="web scraping, research, data collection, automation, selenium, beautifulsoup",
    project_urls={
        "Bug Reports": "https://github.com/CrazyDubya/research-scrapers/issues",
        "Source": "https://github.com/CrazyDubya/research-scrapers",
        "Documentation": "https://github.com/CrazyDubya/research-scrapers/tree/main/docs",
    },
)
