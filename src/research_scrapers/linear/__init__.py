"""
Linear Integration Module

This module provides Linear API integration for the research-scrapers package,
enabling automatic task creation and management from scraper results.

Author: Stephen Thompson
"""

from .client import LinearClient, LinearError, LinearRateLimitError, LinearAuthError

__all__ = [
    'LinearClient',
    'LinearError',
    'LinearRateLimitError',
    'LinearAuthError',
]
