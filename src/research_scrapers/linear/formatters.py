"""
Result Formatters for Linear Integration

This module provides specialized formatters for different scraper result types,
enabling rich markdown formatting for Linear issues and comments.

Author: Stephen Thompson
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Union, Optional
from enum import Enum


class ScraperType(Enum):
    """Supported scraper types for formatting."""
    GITHUB_REPO = "github_repo"
    GITHUB_ISSUE = "github_issue"
    GITHUB_USER = "github_user"
    GITHUB_SEARCH = "github_search"
    ARXIV = "arxiv"
    STACKOVERFLOW = "stackoverflow"
    PATENT = "patent"


class LinearResultFormatter:
    """
    Formats scraper results for Linear issues and comments.
    
    This class provides specialized formatting for different types of scraper results,
    converting raw data into well-structured markdown suitable for Linear.
    """
    
    @staticmethod
    def format_header(run_id: str, workflow_url: Optional[str] = None) -> str:
        """
        Format the header section for Linear content.
        
        Args:
            run_id: Unique run identifier
            workflow_url: Optional URL to GitHub Actions workflow run
            
        Returns:
            Formatted markdown header
        """
        header = "# 🔬 Research Scraper Results\n\n"
        header += f"**Run ID**: `{run_id}`\n"
        header += f"**Timestamp**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        
        if workflow_url:
            header += f"**Workflow**: [View in GitHub Actions]({workflow_url})\n"
        
        header += "\n---\n\n"
        return header
    
    @staticmethod
    def format_github_repository(data: Dict[str, Any]) -> str:
        """
        Format GitHub repository data for Linear.
        
        Args:
            data: Repository data from GitHub API
            
        Returns:
            Formatted markdown string
        """
        if not isinstance(data, dict):
            return LinearResultFormatter._format_fallback(data)
        
        md = ""
        
        # Repository name and link
        if 'full_name' in data:
            repo_url = data.get('html_url', '#')
            md += f"**Repository**: [`{data['full_name']}`]({repo_url})\n"
        elif 'name' in data:
            owner = data.get('owner', {})
            if isinstance(owner, dict):
                owner_name = owner.get('login', 'Unknown')
            else:
                owner_name = str(owner) if owner else 'Unknown'
            md += f"**Repository**: `{owner_name}/{data['name']}`\n"
        
        # Description
        if 'description' in data and data['description']:
            description = data['description'][:200]  # Truncate long descriptions
            if len(data['description']) > 200:
                description += "..."
            md += f"**Description**: {description}\n"
        
        # Statistics
        stats = []
        if 'stargazers_count' in data:
            stats.append(f"⭐ {data['stargazers_count']:,} stars")
        if 'forks_count' in data:
            stats.append(f"🍴 {data['forks_count']:,} forks")
        if 'watchers_count' in data:
            stats.append(f"👀 {data['watchers_count']:,} watchers")
        
        if stats:
            md += f"**Stats**: {' • '.join(stats)}\n"
        
        # Technical details
        if 'language' in data and data['language']:
            md += f"**Primary Language**: {data['language']}\n"
        
        if 'size' in data:
            size_mb = data['size'] / 1024  # Convert KB to MB
            md += f"**Size**: {size_mb:.1f} MB\n"
        
        # Topics/Tags
        if 'topics' in data and data['topics']:
            topics = data['topics'][:10]  # Limit to first 10 topics
            topic_tags = ' '.join(f'`{topic}`' for topic in topics)
            md += f"**Topics**: {topic_tags}\n"
            if len(data['topics']) > 10:
                md += f"   *... and {len(data['topics']) - 10} more topics*\n"
        
        # License
        if 'license' in data and data['license']:
            if isinstance(data['license'], dict):
                license_name = data['license'].get('name', 'Unknown')
                license_url = data['license'].get('url')
                if license_url:
                    md += f"**License**: [{license_name}]({license_url})\n"
                else:
                    md += f"**License**: {license_name}\n"
            else:
                md += f"**License**: {data['license']}\n"
        
        # Issue and PR counts
        if 'open_issues_count' in data:
            md += f"**Open Issues**: {data['open_issues_count']:,}\n"
        
        # Dates
        if 'created_at' in data:
            created = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
            md += f"**Created**: {created.strftime('%Y-%m-%d')}\n"
        
        if 'updated_at' in data:
            updated = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
            md += f"**Last Updated**: {updated.strftime('%Y-%m-%d')}\n"
        
        # Additional metrics
        if 'network_count' in data and data['network_count'] > 0:
            md += f"**Network**: {data['network_count']:,} repositories\n"
        
        if 'subscribers_count' in data:
            md += f"**Subscribers**: {data['subscribers_count']:,}\n"
        
        return md
    
    @staticmethod
    def format_github_issues(data: Union[List[Dict], Dict]) -> str:
        """
        Format GitHub issues data for Linear.
        
        Args:
            data: Issues data from GitHub API (list or single issue)
            
        Returns:
            Formatted markdown string
        """
        if isinstance(data, dict):
            # Single issue
            return LinearResultFormatter._format_single_github_issue(data)
        
        if not isinstance(data, list):
            return LinearResultFormatter._format_fallback(data)
        
        md = f"**Total Issues Found**: {len(data)}\n\n"
        
        if not data:
            md += "*No issues found.*\n"
            return md
        
        # Group issues by state
        open_issues = [issue for issue in data if issue.get('state') == 'open']
        closed_issues = [issue for issue in data if issue.get('state') == 'closed']
        
        if open_issues:
            md += f"### 🟢 Open Issues ({len(open_issues)})\n\n"
            for i, issue in enumerate(open_issues[:5], 1):  # Show top 5
                md += LinearResultFormatter._format_issue_summary(issue, i)
            
            if len(open_issues) > 5:
                md += f"*... and {len(open_issues) - 5} more open issues*\n\n"
        
        if closed_issues:
            md += f"### 🔴 Closed Issues ({len(closed_issues)})\n\n"
            for i, issue in enumerate(closed_issues[:3], 1):  # Show top 3
                md += LinearResultFormatter._format_issue_summary(issue, i)
            
            if len(closed_issues) > 3:
                md += f"*... and {len(closed_issues) - 3} more closed issues*\n\n"
        
        return md
    
    @staticmethod
    def _format_single_github_issue(issue: Dict[str, Any]) -> str:
        """Format a single GitHub issue."""
        md = ""
        
        if 'title' in issue:
            issue_url = issue.get('html_url', '#')
            number = issue.get('number', 'N/A')
            md += f"**Issue**: [#{number} {issue['title']}]({issue_url})\n"
        
        if 'state' in issue:
            state_emoji = "🟢" if issue['state'] == 'open' else "🔴"
            md += f"**State**: {state_emoji} {issue['state'].title()}\n"
        
        if 'user' in issue and isinstance(issue['user'], dict):
            author = issue['user'].get('login', 'Unknown')
            author_url = issue['user'].get('html_url', '#')
            md += f"**Author**: [{author}]({author_url})\n"
        
        if 'labels' in issue and issue['labels']:
            labels = [label['name'] if isinstance(label, dict) else str(label) for label in issue['labels'][:5]]
            label_tags = ' '.join(f'`{label}`' for label in labels)
            md += f"**Labels**: {label_tags}\n"
        
        if 'created_at' in issue:
            created = datetime.fromisoformat(issue['created_at'].replace('Z', '+00:00'))
            md += f"**Created**: {created.strftime('%Y-%m-%d %H:%M UTC')}\n"
        
        if 'comments' in issue:
            md += f"**Comments**: {issue['comments']}\n"
        
        if 'body' in issue and issue['body']:
            body = issue['body'][:300]  # Truncate long bodies
            if len(issue['body']) > 300:
                body += "..."
            md += f"\n**Description**:\n> {body}\n"
        
        return md
    
    @staticmethod
    def _format_issue_summary(issue: Dict[str, Any], index: int) -> str:
        """Format a brief issue summary for lists."""
        title = issue.get('title', 'Untitled')
        number = issue.get('number', 'N/A')
        
        md = f"{index}. **#{number}**: {title}\n"
        
        # Add labels if available
        if 'labels' in issue and issue['labels']:
            labels = [label['name'] if isinstance(label, dict) else str(label) for label in issue['labels'][:3]]
            if labels:
                label_tags = ' '.join(f'`{label}`' for label in labels)
                md += f"   *Labels*: {label_tags}\n"
        
        # Add author if available
        if 'user' in issue and isinstance(issue['user'], dict):
            author = issue['user'].get('login', 'Unknown')
            md += f"   *Author*: {author}\n"
        
        md += "\n"
        return md
    
    @staticmethod
    def format_github_user(data: Dict[str, Any]) -> str:
        """
        Format GitHub user data for Linear.
        
        Args:
            data: User data from GitHub API
            
        Returns:
            Formatted markdown string
        """
        if not isinstance(data, dict):
            return LinearResultFormatter._format_fallback(data)
        
        md = ""
        
        # User profile
        if 'login' in data:
            user_url = data.get('html_url', '#')
            avatar_url = data.get('avatar_url')
            if avatar_url:
                md += f"**User**: [{data['login']}]({user_url}) ![avatar]({avatar_url}&s=20)\n"
            else:
                md += f"**User**: [{data['login']}]({user_url})\n"
        
        if 'name' in data and data['name']:
            md += f"**Name**: {data['name']}\n"
        
        if 'bio' in data and data['bio']:
            bio = data['bio'][:200]  # Truncate long bios
            if len(data['bio']) > 200:
                bio += "..."
            md += f"**Bio**: {bio}\n"
        
        # Contact and location
        if 'company' in data and data['company']:
            md += f"**Company**: {data['company']}\n"
        
        if 'location' in data and data['location']:
            md += f"**Location**: {data['location']}\n"
        
        if 'blog' in data and data['blog']:
            blog_url = data['blog']
            if not blog_url.startswith('http'):
                blog_url = f"https://{blog_url}"
            md += f"**Website**: [{data['blog']}]({blog_url})\n"
        
        if 'email' in data and data['email']:
            md += f"**Email**: {data['email']}\n"
        
        # Statistics
        stats = []
        if 'public_repos' in data:
            stats.append(f"📁 {data['public_repos']:,} repos")
        if 'followers' in data:
            stats.append(f"👥 {data['followers']:,} followers")
        if 'following' in data:
            stats.append(f"➡️ {data['following']:,} following")
        
        if stats:
            md += f"**Stats**: {' • '.join(stats)}\n"
        
        # Account details
        if 'type' in data:
            md += f"**Account Type**: {data['type']}\n"
        
        if 'created_at' in data:
            created = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
            md += f"**Member Since**: {created.strftime('%Y-%m-%d')}\n"
        
        if 'updated_at' in data:
            updated = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
            md += f"**Last Active**: {updated.strftime('%Y-%m-%d')}\n"
        
        return md
    
    @staticmethod
    def format_arxiv_papers(data: Union[List[Dict], Dict]) -> str:
        """
        Format ArXiv papers data for Linear.
        
        Args:
            data: ArXiv papers data
            
        Returns:
            Formatted markdown string
        """
        if isinstance(data, dict):
            # Single paper
            return LinearResultFormatter._format_single_arxiv_paper(data)
        
        if not isinstance(data, list):
            return LinearResultFormatter._format_fallback(data)
        
        md = f"**Total Papers Found**: {len(data)}\n\n"
        
        if not data:
            md += "*No papers found.*\n"
            return md
        
        # Show top 10 papers
        for i, paper in enumerate(data[:10], 1):
            md += LinearResultFormatter._format_arxiv_paper_summary(paper, i)
        
        if len(data) > 10:
            md += f"*... and {len(data) - 10} more papers*\n"
        
        return md
    
    @staticmethod
    def _format_single_arxiv_paper(paper: Dict[str, Any]) -> str:
        """Format a single ArXiv paper."""
        md = ""
        
        if 'title' in paper:
            arxiv_id = paper.get('id', paper.get('arxiv_id', ''))
            if arxiv_id:
                arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"
                md += f"**Paper**: [{paper['title']}]({arxiv_url})\n"
            else:
                md += f"**Paper**: {paper['title']}\n"
        
        if 'authors' in paper and paper['authors']:
            authors = paper['authors']
            if len(authors) <= 3:
                author_list = ', '.join(authors)
            else:
                author_list = f"{', '.join(authors[:3])} et al. ({len(authors)} total)"
            md += f"**Authors**: {author_list}\n"
        
        if 'published' in paper:
            md += f"**Published**: {paper['published']}\n"
        
        if 'categories' in paper and paper['categories']:
            categories = ' '.join(f'`{cat}`' for cat in paper['categories'][:5])
            md += f"**Categories**: {categories}\n"
        
        if 'summary' in paper and paper['summary']:
            summary = paper['summary'][:400]  # Truncate long summaries
            if len(paper['summary']) > 400:
                summary += "..."
            md += f"\n**Abstract**:\n> {summary}\n"
        
        return md
    
    @staticmethod
    def _format_arxiv_paper_summary(paper: Dict[str, Any], index: int) -> str:
        """Format a brief paper summary for lists."""
        title = paper.get('title', 'Untitled')
        
        md = f"{index}. **{title}**\n"
        
        if 'authors' in paper and paper['authors']:
            authors = paper['authors']
            if len(authors) <= 2:
                author_list = ', '.join(authors)
            else:
                author_list = f"{authors[0]} et al."
            md += f"   *Authors*: {author_list}\n"
        
        if 'published' in paper:
            md += f"   *Published*: {paper['published']}\n"
        
        if 'categories' in paper and paper['categories']:
            categories = ', '.join(f'`{cat}`' for cat in paper['categories'][:3])
            md += f"   *Categories*: {categories}\n"
        
        md += "\n"
        return md
    
    @staticmethod
    def format_stackoverflow_questions(data: Union[List[Dict], Dict]) -> str:
        """
        Format Stack Overflow questions data for Linear.
        
        Args:
            data: Stack Overflow questions data
            
        Returns:
            Formatted markdown string
        """
        if isinstance(data, dict):
            # Single question
            return LinearResultFormatter._format_single_stackoverflow_question(data)
        
        if not isinstance(data, list):
            return LinearResultFormatter._format_fallback(data)
        
        md = f"**Total Questions Found**: {len(data)}\n\n"
        
        if not data:
            md += "*No questions found.*\n"
            return md
        
        # Show top 10 questions
        for i, question in enumerate(data[:10], 1):
            md += LinearResultFormatter._format_stackoverflow_question_summary(question, i)
        
        if len(data) > 10:
            md += f"*... and {len(data) - 10} more questions*\n"
        
        return md
    
    @staticmethod
    def _format_single_stackoverflow_question(question: Dict[str, Any]) -> str:
        """Format a single Stack Overflow question."""
        md = ""
        
        if 'title' in question:
            question_url = question.get('link', '#')
            question_id = question.get('question_id', '')
            md += f"**Question**: [{question['title']}]({question_url})\n"
        
        if 'score' in question:
            md += f"**Score**: {question['score']}\n"
        
        if 'answer_count' in question:
            md += f"**Answers**: {question['answer_count']}\n"
        
        if 'view_count' in question:
            md += f"**Views**: {question['view_count']:,}\n"
        
        if 'tags' in question and question['tags']:
            tags = ' '.join(f'`{tag}`' for tag in question['tags'][:8])
            md += f"**Tags**: {tags}\n"
        
        if 'owner' in question and isinstance(question['owner'], dict):
            owner = question['owner']
            display_name = owner.get('display_name', 'Unknown')
            reputation = owner.get('reputation', 0)
            md += f"**Asked by**: {display_name} ({reputation:,} rep)\n"
        
        if 'creation_date' in question:
            created = datetime.fromtimestamp(question['creation_date'])
            md += f"**Created**: {created.strftime('%Y-%m-%d %H:%M UTC')}\n"
        
        if 'is_answered' in question:
            answered = "✅ Yes" if question['is_answered'] else "❌ No"
            md += f"**Answered**: {answered}\n"
        
        return md
    
    @staticmethod
    def _format_stackoverflow_question_summary(question: Dict[str, Any], index: int) -> str:
        """Format a brief question summary for lists."""
        title = question.get('title', 'Untitled')
        score = question.get('score', 0)
        
        md = f"{index}. **{title}** (Score: {score})\n"
        
        if 'tags' in question and question['tags']:
            tags = ', '.join(f'`{tag}`' for tag in question['tags'][:4])
            md += f"   *Tags*: {tags}\n"
        
        if 'answer_count' in question:
            answers = question['answer_count']
            is_answered = question.get('is_answered', False)
            status = "✅" if is_answered else "❌"
            md += f"   *Answers*: {answers} {status}\n"
        
        md += "\n"
        return md
    
    @staticmethod
    def format_patent_data(data: Union[List[Dict], Dict]) -> str:
        """
        Format patent data for Linear.
        
        Args:
            data: Patent data
            
        Returns:
            Formatted markdown string
        """
        if isinstance(data, dict):
            # Single patent
            return LinearResultFormatter._format_single_patent(data)
        
        if not isinstance(data, list):
            return LinearResultFormatter._format_fallback(data)
        
        md = f"**Total Patents Found**: {len(data)}\n\n"
        
        if not data:
            md += "*No patents found.*\n"
            return md
        
        # Show top 10 patents
        for i, patent in enumerate(data[:10], 1):
            md += LinearResultFormatter._format_patent_summary(patent, i)
        
        if len(data) > 10:
            md += f"*... and {len(data) - 10} more patents*\n"
        
        return md
    
    @staticmethod
    def _format_single_patent(patent: Dict[str, Any]) -> str:
        """Format a single patent."""
        md = ""
        
        if 'title' in patent:
            patent_number = patent.get('patent_number', patent.get('publication_number', ''))
            if patent_number:
                # Try to create a Google Patents URL
                google_url = f"https://patents.google.com/patent/{patent_number}"
                md += f"**Patent**: [{patent['title']}]({google_url})\n"
                md += f"**Number**: {patent_number}\n"
            else:
                md += f"**Patent**: {patent['title']}\n"
        
        if 'inventors' in patent and patent['inventors']:
            inventors = patent['inventors']
            if len(inventors) <= 3:
                inventor_list = ', '.join(inventors)
            else:
                inventor_list = f"{', '.join(inventors[:3])} et al. ({len(inventors)} total)"
            md += f"**Inventors**: {inventor_list}\n"
        
        if 'assignee' in patent and patent['assignee']:
            md += f"**Assignee**: {patent['assignee']}\n"
        
        if 'filing_date' in patent:
            md += f"**Filed**: {patent['filing_date']}\n"
        
        if 'grant_date' in patent:
            md += f"**Granted**: {patent['grant_date']}\n"
        
        if 'publication_date' in patent:
            md += f"**Published**: {patent['publication_date']}\n"
        
        if 'abstract' in patent and patent['abstract']:
            abstract = patent['abstract'][:400]  # Truncate long abstracts
            if len(patent['abstract']) > 400:
                abstract += "..."
            md += f"\n**Abstract**:\n> {abstract}\n"
        
        return md
    
    @staticmethod
    def _format_patent_summary(patent: Dict[str, Any], index: int) -> str:
        """Format a brief patent summary for lists."""
        title = patent.get('title', 'Untitled')
        patent_number = patent.get('patent_number', patent.get('publication_number', 'N/A'))
        
        md = f"{index}. **{title}** ({patent_number})\n"
        
        if 'inventors' in patent and patent['inventors']:
            inventors = patent['inventors']
            if len(inventors) <= 2:
                inventor_list = ', '.join(inventors)
            else:
                inventor_list = f"{inventors[0]} et al."
            md += f"   *Inventors*: {inventor_list}\n"
        
        if 'assignee' in patent and patent['assignee']:
            md += f"   *Assignee*: {patent['assignee']}\n"
        
        if 'grant_date' in patent:
            md += f"   *Granted*: {patent['grant_date']}\n"
        
        md += "\n"
        return md
    
    @staticmethod
    def _format_fallback(data: Any) -> str:
        """
        Fallback formatter for unknown or invalid data types.
        
        Args:
            data: Data to format
            
        Returns:
            JSON representation of the data
        """
        try:
            json_str = json.dumps(data, indent=2, default=str)
            # Truncate if too long
            if len(json_str) > 1500:
                json_str = json_str[:1500] + "\n... (truncated)"
            return f"```json\n{json_str}\n```\n"
        except Exception:
            # Last resort: string representation
            str_repr = str(data)
            if len(str_repr) > 1500:
                str_repr = str_repr[:1500] + "... (truncated)"
            return f"```\n{str_repr}\n```\n"
    
    @classmethod
    def format_scraper_results(
        cls,
        scraper_results: Dict[str, Any],
        run_id: str,
        workflow_url: Optional[str] = None
    ) -> str:
        """
        Format complete scraper results for Linear.
        
        Args:
            scraper_results: Dictionary of scraper results by type
            run_id: Unique run identifier
            workflow_url: Optional URL to GitHub Actions workflow run
            
        Returns:
            Complete formatted markdown string
        """
        # Start with header
        markdown = cls.format_header(run_id, workflow_url)
        
        if not scraper_results:
            markdown += "⚠️ No results to display. Check workflow logs for details.\n"
            return markdown
        
        # Format each scraper type
        for scraper_type, data in scraper_results.items():
            markdown += f"## {scraper_type.replace('_', ' ').title()}\n\n"
            
            try:
                # Determine formatter based on scraper type
                if scraper_type in ['github_repo', 'github-repo']:
                    formatted = cls.format_github_repository(data)
                elif scraper_type in ['github_issue', 'github-issue', 'github_issues']:
                    formatted = cls.format_github_issues(data)
                elif scraper_type in ['github_user', 'github-user']:
                    formatted = cls.format_github_user(data)
                elif scraper_type in ['arxiv']:
                    formatted = cls.format_arxiv_papers(data)
                elif scraper_type in ['stackoverflow', 'stack_overflow']:
                    formatted = cls.format_stackoverflow_questions(data)
                elif scraper_type in ['patent', 'patents']:
                    formatted = cls.format_patent_data(data)
                else:
                    # Unknown scraper type, use fallback
                    formatted = cls._format_fallback(data)
                
                markdown += formatted
                
            except Exception as e:
                # If formatting fails, use fallback
                markdown += f"*Error formatting results: {e}*\n\n"
                markdown += cls._format_fallback(data)
            
            markdown += "\n"
        
        return markdown