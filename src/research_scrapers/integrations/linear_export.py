"""Export utilities for Linear data.

This module provides utilities for exporting Linear data to various formats
for analysis and reporting.
"""

import json
import csv
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from ..scrapers.linear_scraper import LinearScraper


logger = logging.getLogger(__name__)


class LinearExporter:
    """Utility class for exporting Linear data to various formats."""
    
    def __init__(self, linear_scraper: LinearScraper):
        """Initialize the exporter.
        
        Args:
            linear_scraper: Configured Linear scraper instance
        """
        self.linear_scraper = linear_scraper
    
    def export_team_issues_to_json(self, 
                                  team_id: str, 
                                  output_path: str,
                                  filters: Optional[Dict[str, Any]] = None) -> str:
        """Export team issues to JSON format.
        
        Args:
            team_id: Linear team ID
            output_path: Path to save the JSON file
            filters: Optional filters for issues
            
        Returns:
            Path to the created JSON file
        """
        logger.info(f"Exporting team {team_id} issues to JSON: {output_path}")
        
        # Fetch team issues
        issues = self.linear_scraper.get_team_issues(team_id, filters or {})
        
        # Add export metadata
        export_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'team_id': team_id,
                'total_issues': len(issues),
                'filters': filters or {}
            },
            'issues': issues
        }
        
        # Write to JSON file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(issues)} issues to {output_path}")
        return str(output_file)
    
    def export_team_issues_to_csv(self, 
                                 team_id: str, 
                                 output_path: str,
                                 filters: Optional[Dict[str, Any]] = None) -> str:
        """Export team issues to CSV format.
        
        Args:
            team_id: Linear team ID
            output_path: Path to save the CSV file
            filters: Optional filters for issues
            
        Returns:
            Path to the created CSV file
        """
        logger.info(f"Exporting team {team_id} issues to CSV: {output_path}")
        
        # Fetch team issues
        issues = self.linear_scraper.get_team_issues(team_id, filters or {})
        
        if not issues:
            logger.warning("No issues found to export")
            return output_path
        
        # Prepare CSV data
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Define CSV columns
        fieldnames = [
            'id', 'title', 'description', 'state', 'priority', 'assignee',
            'creator', 'created_at', 'updated_at', 'completed_at', 'labels',
            'url', 'external_id'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for issue in issues:
                # Flatten issue data for CSV
                csv_row = {
                    'id': issue.get('id', ''),
                    'title': issue.get('title', ''),
                    'description': (issue.get('description', '') or '')[:500],  # Truncate long descriptions
                    'state': issue.get('state', {}).get('name', ''),
                    'priority': self._priority_to_text(issue.get('priority', 0)),
                    'assignee': issue.get('assignee', {}).get('name', '') if issue.get('assignee') else '',
                    'creator': issue.get('creator', {}).get('name', ''),
                    'created_at': issue.get('createdAt', ''),
                    'updated_at': issue.get('updatedAt', ''),
                    'completed_at': issue.get('completedAt', ''),
                    'labels': ', '.join([label.get('name', '') for label in issue.get('labels', {}).get('nodes', [])]),
                    'url': issue.get('url', ''),
                    'external_id': issue.get('externalId', '')
                }
                writer.writerow(csv_row)
        
        logger.info(f"Exported {len(issues)} issues to {output_path}")
        return str(output_file)
    
    def export_project_summary(self, 
                              project_id: str, 
                              output_path: str,
                              format_type: str = 'json') -> str:
        """Export project summary with statistics.
        
        Args:
            project_id: Linear project ID
            output_path: Path to save the export file
            format_type: Export format ('json' or 'csv')
            
        Returns:
            Path to the created export file
        """
        logger.info(f"Exporting project {project_id} summary to {format_type}: {output_path}")
        
        # Fetch project data
        project = self.linear_scraper.get_project(project_id)
        project_issues = self.linear_scraper.get_project_issues(project_id)
        
        # Calculate statistics
        stats = self._calculate_project_stats(project_issues)
        
        # Prepare export data
        export_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'project_id': project_id,
                'project_name': project.get('name', ''),
                'project_description': project.get('description', '')
            },
            'statistics': stats,
            'issues': project_issues
        }
        
        if format_type.lower() == 'json':
            return self._export_to_json(export_data, output_path)
        elif format_type.lower() == 'csv':
            return self._export_project_to_csv(export_data, output_path)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def export_workspace_overview(self, 
                                 output_path: str,
                                 format_type: str = 'json') -> str:
        """Export workspace overview with all teams and projects.
        
        Args:
            output_path: Path to save the export file
            format_type: Export format ('json' or 'csv')
            
        Returns:
            Path to the created export file
        """
        logger.info(f"Exporting workspace overview to {format_type}: {output_path}")
        
        # Fetch workspace data
        teams = self.linear_scraper.get_teams()
        projects = self.linear_scraper.get_projects()
        
        # Prepare export data
        export_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'total_teams': len(teams),
                'total_projects': len(projects)
            },
            'teams': teams,
            'projects': projects
        }
        
        if format_type.lower() == 'json':
            return self._export_to_json(export_data, output_path)
        else:
            raise ValueError(f"Workspace overview only supports JSON format")
    
    def _calculate_project_stats(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for project issues.
        
        Args:
            issues: List of project issues
            
        Returns:
            Dictionary with calculated statistics
        """
        if not issues:
            return {
                'total_issues': 0,
                'by_state': {},
                'by_priority': {},
                'by_assignee': {},
                'completion_rate': 0
            }
        
        stats = {
            'total_issues': len(issues),
            'by_state': {},
            'by_priority': {},
            'by_assignee': {},
            'completion_rate': 0
        }
        
        completed_count = 0
        
        for issue in issues:
            # Count by state
            state = issue.get('state', {}).get('name', 'Unknown')
            stats['by_state'][state] = stats['by_state'].get(state, 0) + 1
            
            if state.lower() in ['done', 'completed', 'closed']:
                completed_count += 1
            
            # Count by priority
            priority = self._priority_to_text(issue.get('priority', 0))
            stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
            
            # Count by assignee
            assignee = issue.get('assignee', {}).get('name', 'Unassigned') if issue.get('assignee') else 'Unassigned'
            stats['by_assignee'][assignee] = stats['by_assignee'].get(assignee, 0) + 1
        
        # Calculate completion rate
        stats['completion_rate'] = (completed_count / len(issues)) * 100 if issues else 0
        
        return stats
    
    def _priority_to_text(self, priority: int) -> str:
        """Convert priority number to text.
        
        Args:
            priority: Priority number (0-4)
            
        Returns:
            Priority text representation
        """
        priority_map = {
            0: 'No Priority',
            1: 'Urgent',
            2: 'High',
            3: 'Medium',
            4: 'Low'
        }
        return priority_map.get(priority, 'Unknown')
    
    def _export_to_json(self, data: Dict[str, Any], output_path: str) -> str:
        """Export data to JSON file.
        
        Args:
            data: Data to export
            output_path: Path to save the file
            
        Returns:
            Path to the created file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return str(output_file)
    
    def _export_project_to_csv(self, data: Dict[str, Any], output_path: str) -> str:
        """Export project data to CSV file.
        
        Args:
            data: Project data to export
            output_path: Path to save the file
            
        Returns:
            Path to the created file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        issues = data.get('issues', [])
        
        if not issues:
            # Create empty CSV with headers
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['No issues found in project'])
            return str(output_file)
        
        # Define CSV columns
        fieldnames = [
            'id', 'title', 'description', 'state', 'priority', 'assignee',
            'creator', 'created_at', 'updated_at', 'completed_at', 'labels', 'url'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for issue in issues:
                csv_row = {
                    'id': issue.get('id', ''),
                    'title': issue.get('title', ''),
                    'description': (issue.get('description', '') or '')[:500],
                    'state': issue.get('state', {}).get('name', ''),
                    'priority': self._priority_to_text(issue.get('priority', 0)),
                    'assignee': issue.get('assignee', {}).get('name', '') if issue.get('assignee') else '',
                    'creator': issue.get('creator', {}).get('name', ''),
                    'created_at': issue.get('createdAt', ''),
                    'updated_at': issue.get('updatedAt', ''),
                    'completed_at': issue.get('completedAt', ''),
                    'labels': ', '.join([label.get('name', '') for label in issue.get('labels', {}).get('nodes', [])]),
                    'url': issue.get('url', '')
                }
                writer.writerow(csv_row)
        
        return str(output_file)
