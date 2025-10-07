"""
Linear Integration Module

This module provides Linear API integration for the research-scrapers package,
enabling automatic task creation and management from scraper results.

Author: Stephen Thompson
"""

from .client import (
    LinearClient,
    LinearError,
    LinearRateLimitError,
    LinearAuthError,
    LinearValidationError,
    LinearTeam,
    LinearWorkflowState,
    LinearIssue,
    IssueState,
    IssuePriority,
    ScraperType,
    create_linear_client,
    create_issue_from_artifacts
)

from .formatters import LinearResultFormatter

__all__ = [
    # Client
    'LinearClient',
    'create_linear_client',
    'create_issue_from_artifacts',
    
    # Exceptions
    'LinearError',
    'LinearRateLimitError',
    'LinearAuthError',
    'LinearValidationError',
    
    # Data Classes
    'LinearTeam',
    'LinearWorkflowState',
    'LinearIssue',
    
    # Enums
    'IssueState',
    'IssuePriority',
    'ScraperType',
    
    # Formatters
    'LinearResultFormatter',
]

__version__ = '1.0.0'
