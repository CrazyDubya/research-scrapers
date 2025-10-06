"""Stack Overflow scraper for questions, answers, users, and tags.

This scraper provides comprehensive Stack Overflow data extraction capabilities
including questions with answers and comments, user profiles, and tag-based searches.
It follows the established patterns from other scrapers in this package.

Features:
- Question scraping with full answer threads
- User profile and activity scraping
- Tag-based question filtering
- Search functionality
- Rate limiting and error handling
- Multiple output formats
- Comprehensive CLI interface

Author: Stephen Thompson
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlparse, parse_qs
from dataclasses import dataclass, asdict

# Import base scraper classes and utilities
from .scraper import WebScraper
from .config import Config
from .utils import (
    setup_logging, rate_limit, retry_on_failure, clean_text,
    save_to_json, create_output_directory, validate_url, extract_domain
)

import requests
from bs4 import BeautifulSoup
import logging


@dataclass
class ScrapingOptions:
    """Configuration options for Stack Overflow scraping."""
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


class StackOverflowScraper(WebScraper):
    """Stack Overflow scraper for questions, answers, and user data."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the Stack Overflow scraper.
        
        Args:
            config: Configuration object
        """
        super().__init__(config)
        self.base_url = "https://stackoverflow.com"
        self.api_base_url = "https://api.stackexchange.com/2.3"
        
        # Setup session headers for Stack Overflow
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        self.logger.info("Initialized Stack Overflow scraper")
    
    def scrape_question(self, question_id: Union[int, str], 
                       options: Optional[ScrapingOptions] = None) -> Dict[str, Any]:
        """Scrape a single Stack Overflow question with answers and comments.
        
        Args:
            question_id: Stack Overflow question ID
            options: Scraping configuration options
            
        Returns:
            Dictionary containing question data
        """
        if options is None:
            options = ScrapingOptions()
        
        self.logger.info(f"Scraping question {question_id}")
        
        url = f"{self.base_url}/questions/{question_id}"
        response = self.get_page(url)
        soup = self.parse_html(response.text)
        
        # Extract question data
        question_data = self._extract_question_data(soup, options)
        question_data['question_id'] = str(question_id)
        question_data['url'] = url
        question_data['scraped_at'] = datetime.now().isoformat()
        
        # Extract answers if requested
        if options.include_answers:
            question_data['answers'] = self._extract_answers(soup, options)
        
        return question_data
    
    def scrape_questions_by_tag(self, tag: str, 
                               options: Optional[ScrapingOptions] = None,
                               sort_by: str = 'newest',
                               page_limit: int = 5) -> List[Dict[str, Any]]:
        """Scrape questions filtered by tag.
        
        Args:
            tag: Tag to filter by (e.g., 'python', 'javascript')
            options: Scraping configuration options
            sort_by: Sort order ('newest', 'active', 'votes', 'frequent')
            page_limit: Maximum number of pages to scrape
            
        Returns:
            List of question dictionaries
        """
        if options is None:
            options = ScrapingOptions()
        
        self.logger.info(f"Scraping questions for tag '{tag}' (max {options.max_questions})")
        
        questions = []
        page = 1
        
        while len(questions) < options.max_questions and page <= page_limit:
            url = f"{self.base_url}/questions/tagged/{tag}"
            params = {
                'tab': sort_by,
                'page': page
            }
            
            response = self.get_page(url, params=params)
            soup = self.parse_html(response.text)
            
            # Extract question summaries from the listing page
            question_summaries = self._extract_question_summaries(soup)
            
            if not question_summaries:
                break
            
            for summary in question_summaries:
                if len(questions) >= options.max_questions:
                    break
                
                # Get full question data
                try:
                    question_id = summary['question_id']
                    full_question = self.scrape_question(question_id, options)
                    
                    # Merge summary data with full data
                    full_question.update(summary)
                    questions.append(full_question)
                    
                    # Rate limiting
                    time.sleep(1.0 / self.config.RATE_LIMIT)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to scrape question {summary.get('question_id')}: {e}")
                    continue
            
            page += 1
        
        self.logger.info(f"Scraped {len(questions)} questions for tag '{tag}'")
        return questions
    
    def scrape_user_profile(self, user_id: Union[int, str]) -> Dict[str, Any]:
        """Scrape a Stack Overflow user profile.
        
        Args:
            user_id: Stack Overflow user ID
            
        Returns:
            Dictionary containing user profile data
        """
        self.logger.info(f"Scraping user profile {user_id}")
        
        url = f"{self.base_url}/users/{user_id}"
        response = self.get_page(url)
        soup = self.parse_html(response.text)
        
        user_data = self._extract_user_data(soup)
        user_data['user_id'] = str(user_id)
        user_data['profile_url'] = url
        user_data['scraped_at'] = datetime.now().isoformat()
        
        return user_data
    
    def search_questions(self, query: str, 
                        options: Optional[ScrapingOptions] = None,
                        sort_by: str = 'relevance',
                        page_limit: int = 3) -> List[Dict[str, Any]]:
        """Search Stack Overflow questions by query.
        
        Args:
            query: Search query
            options: Scraping configuration options
            sort_by: Sort order ('relevance', 'newest', 'votes', 'active')
            page_limit: Maximum number of pages to scrape
            
        Returns:
            List of question dictionaries
        """
        if options is None:
            options = ScrapingOptions()
        
        self.logger.info(f"Searching questions for '{query}' (max {options.max_questions})")
        
        questions = []
        page = 1
        
        while len(questions) < options.max_questions and page <= page_limit:
            url = f"{self.base_url}/search"
            params = {
                'q': query,
                'tab': sort_by,
                'page': page
            }
            
            response = self.get_page(url, params=params)
            soup = self.parse_html(response.text)
            
            # Extract question summaries from search results
            question_summaries = self._extract_question_summaries(soup)
            
            if not question_summaries:
                break
            
            for summary in question_summaries:
                if len(questions) >= options.max_questions:
                    break
                
                try:
                    question_id = summary['question_id']
                    full_question = self.scrape_question(question_id, options)
                    full_question.update(summary)
                    questions.append(full_question)
                    
                    # Rate limiting
                    time.sleep(1.0 / self.config.RATE_LIMIT)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to scrape question {summary.get('question_id')}: {e}")
                    continue
            
            page += 1
        
        self.logger.info(f"Found {len(questions)} questions for query '{query}'")
        return questions
    
    def _extract_question_data(self, soup: BeautifulSoup, 
                              options: ScrapingOptions) -> Dict[str, Any]:
        """Extract question data from question page soup."""
        question_data = {}
        
        # Find the main question post
        question_post = soup.find('div', {'class': 'question'}) or soup.find('div', {'data-questionid': True})
        
        if not question_post:
            raise ValueError("Could not find question post on page")
        
        # Extract basic question info
        title_elem = soup.find('h1', {'class': 'fs-headline1'}) or soup.find('h1')
        if title_elem:
            question_data['title'] = clean_text(title_elem.get_text())
        
        # Question body
        body_elem = question_post.find('div', {'class': 's-prose'}) or question_post.find('div', {'class': 'post-text'})
        if body_elem:
            question_data['body'] = clean_text(body_elem.get_text())
            question_data['body_html'] = str(body_elem)
        
        # Tags
        if options.include_tags:
            tags = []
            tag_elements = soup.find_all('a', {'class': 'post-tag'})
            for tag_elem in tag_elements:
                tags.append(clean_text(tag_elem.get_text()))
            question_data['tags'] = tags
        
        # Vote count
        if options.include_vote_counts:
            vote_elem = question_post.find('div', {'class': 'js-vote-count'}) or question_post.find('span', {'class': 'vote-count-post'})
            if vote_elem:
                try:
                    question_data['vote_count'] = int(clean_text(vote_elem.get_text()))
                except (ValueError, TypeError):
                    question_data['vote_count'] = 0
        
        # View count
        view_elem = soup.find('div', {'class': 'mb12'}) or soup.find('div', string=re.compile(r'viewed'))
        if view_elem:
            view_text = clean_text(view_elem.get_text())
            view_match = re.search(r'(\d+(?:,\d+)*)\s*times?', view_text)
            if view_match:
                try:
                    question_data['view_count'] = int(view_match.group(1).replace(',', ''))
                except ValueError:
                    question_data['view_count'] = 0
        
        # User info
        if options.include_user_info:
            user_info = self._extract_post_user_info(question_post)
            question_data['author'] = user_info
        
        # Timestamps
        if options.include_timestamps:
            timestamps = self._extract_post_timestamps(question_post)
            question_data.update(timestamps)
        
        # Comments
        if options.include_comments:
            question_data['comments'] = self._extract_comments(
                question_post, options.max_comments_per_post
            )
        
        return question_data
    
    def _extract_answers(self, soup: BeautifulSoup, 
                        options: ScrapingOptions) -> List[Dict[str, Any]]:
        """Extract answers from question page soup."""
        answers = []
        
        # Find answer posts
        answer_posts = soup.find_all('div', {'class': 'answer'}) or soup.find_all('div', {'data-answerid': True})
        
        for answer_post in answer_posts[:options.max_answers_per_question]:
            answer_data = {}
            
            # Answer ID
            answer_id = answer_post.get('data-answerid') or answer_post.get('id', '').replace('answer-', '')
            if answer_id:
                answer_data['answer_id'] = answer_id
            
            # Answer body
            body_elem = answer_post.find('div', {'class': 's-prose'}) or answer_post.find('div', {'class': 'post-text'})
            if body_elem:
                answer_data['body'] = clean_text(body_elem.get_text())
                answer_data['body_html'] = str(body_elem)
            
            # Vote count
            if options.include_vote_counts:
                vote_elem = answer_post.find('div', {'class': 'js-vote-count'}) or answer_post.find('span', {'class': 'vote-count-post'})
                if vote_elem:
                    try:
                        answer_data['vote_count'] = int(clean_text(vote_elem.get_text()))
                    except (ValueError, TypeError):
                        answer_data['vote_count'] = 0
            
            # Accepted answer
            accepted_elem = answer_post.find('div', {'class': 'accepted-answer'}) or answer_post.find('svg', {'class': 'svg-icon iconCheckmarkLg'})
            answer_data['is_accepted'] = accepted_elem is not None
            
            # User info
            if options.include_user_info:
                user_info = self._extract_post_user_info(answer_post)
                answer_data['author'] = user_info
            
            # Timestamps
            if options.include_timestamps:
                timestamps = self._extract_post_timestamps(answer_post)
                answer_data.update(timestamps)
            
            # Comments
            if options.include_comments:
                answer_data['comments'] = self._extract_comments(
                    answer_post, options.max_comments_per_post
                )
            
            answers.append(answer_data)
        
        return answers
    
    def _extract_question_summaries(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract question summaries from listing pages."""
        summaries = []
        
        # Find question summary elements
        question_elements = soup.find_all('div', {'class': 'question-summary'}) or soup.find_all('div', {'id': re.compile(r'question-summary-\d+')})
        
        for elem in question_elements:
            summary = {}
            
            # Extract question ID from various possible locations
            question_id = None
            
            # Try data attributes
            question_id = elem.get('data-question-id') or elem.get('id', '').replace('question-summary-', '')
            
            # Try link href
            if not question_id:
                link_elem = elem.find('a', {'class': 'question-hyperlink'}) or elem.find('h3').find('a') if elem.find('h3') else None
                if link_elem and link_elem.get('href'):
                    href = link_elem['href']
                    id_match = re.search(r'/questions/(\d+)/', href)
                    if id_match:
                        question_id = id_match.group(1)
            
            if not question_id:
                continue
            
            summary['question_id'] = question_id
            
            # Title
            title_elem = elem.find('a', {'class': 'question-hyperlink'}) or elem.find('h3').find('a') if elem.find('h3') else None
            if title_elem:
                summary['title'] = clean_text(title_elem.get_text())
            
            # Tags
            tag_elements = elem.find_all('a', {'class': 'post-tag'})
            summary['tags'] = [clean_text(tag.get_text()) for tag in tag_elements]
            
            # Vote count
            vote_elem = elem.find('span', {'class': 'vote-count-post'}) or elem.find('div', {'class': 'votes'})
            if vote_elem:
                try:
                    vote_text = clean_text(vote_elem.get_text())
                    summary['vote_count'] = int(re.search(r'-?\d+', vote_text).group())
                except (ValueError, TypeError, AttributeError):
                    summary['vote_count'] = 0
            
            # Answer count
            answer_elem = elem.find('div', {'class': 'status'}) or elem.find('div', string=re.compile(r'answer'))
            if answer_elem:
                try:
                    answer_text = clean_text(answer_elem.get_text())
                    answer_match = re.search(r'(\d+)', answer_text)
                    summary['answer_count'] = int(answer_match.group(1)) if answer_match else 0
                except (ValueError, TypeError):
                    summary['answer_count'] = 0
            
            # View count
            view_elem = elem.find('div', {'class': 'views'})
            if view_elem:
                try:
                    view_text = clean_text(view_elem.get_text())
                    view_match = re.search(r'(\d+(?:,\d+)*)', view_text)
                    if view_match:
                        summary['view_count'] = int(view_match.group(1).replace(',', ''))
                except (ValueError, TypeError):
                    summary['view_count'] = 0
            
            summaries.append(summary)
        
        return summaries
    
    def _extract_user_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract user profile data from user page soup."""
        user_data = {}
        
        # User name
        name_elem = soup.find('h1', {'class': 'fs-headline2'}) or soup.find('h1')
        if name_elem:
            user_data['display_name'] = clean_text(name_elem.get_text())
        
        # Reputation
        rep_elem = soup.find('div', {'class': 'fs-title'}) or soup.find('span', {'class': 'reputation-score'})
        if rep_elem:
            try:
                rep_text = clean_text(rep_elem.get_text())
                # Handle reputation with commas and k/m suffixes
                rep_match = re.search(r'([\d,]+(?:\.\d+)?)\s*([km]?)', rep_text.lower())
                if rep_match:
                    number = float(rep_match.group(1).replace(',', ''))
                    suffix = rep_match.group(2)
                    if suffix == 'k':
                        number *= 1000
                    elif suffix == 'm':
                        number *= 1000000
                    user_data['reputation'] = int(number)
            except (ValueError, TypeError):
                user_data['reputation'] = 0
        
        # Badges
        badge_counts = {}
        badge_elements = soup.find_all('div', {'class': 'badge'}) or soup.find_all('span', {'class': re.compile(r'badge\d')})
        
        for badge_elem in badge_elements:
            badge_text = clean_text(badge_elem.get_text())
            # Extract badge count and type
            badge_match = re.search(r'(\d+)\s*(gold|silver|bronze)', badge_text.lower())
            if badge_match:
                count = int(badge_match.group(1))
                badge_type = badge_match.group(2)
                badge_counts[f'{badge_type}_badges'] = count
        
        user_data['badges'] = badge_counts
        
        # Profile stats
        stats_section = soup.find('div', {'class': 'grid--cell'}) or soup.find('div', {'id': 'stats'})
        if stats_section:
            # Questions asked
            questions_elem = stats_section.find('div', string=re.compile(r'questions?', re.I))
            if questions_elem:
                try:
                    q_text = clean_text(questions_elem.get_text())
                    q_match = re.search(r'(\d+(?:,\d+)*)', q_text)
                    if q_match:
                        user_data['questions_asked'] = int(q_match.group(1).replace(',', ''))
                except (ValueError, TypeError):
                    pass
            
            # Answers given
            answers_elem = stats_section.find('div', string=re.compile(r'answers?', re.I))
            if answers_elem:
                try:
                    a_text = clean_text(answers_elem.get_text())
                    a_match = re.search(r'(\d+(?:,\d+)*)', a_text)
                    if a_match:
                        user_data['answers_given'] = int(a_match.group(1).replace(',', ''))
                except (ValueError, TypeError):
                    pass
        
        # Member since
        member_elem = soup.find('div', string=re.compile(r'member since', re.I)) or soup.find('span', {'class': 'cool'})
        if member_elem:
            member_text = clean_text(member_elem.get_text())
            # Try to extract date
            date_match = re.search(r'(\w+ \d{1,2}, \d{4})', member_text)
            if date_match:
                user_data['member_since'] = date_match.group(1)
        
        # Location
        location_elem = soup.find('div', {'class': 'fs-body2'}) or soup.find('span', {'class': 'adr'})
        if location_elem:
            location_text = clean_text(location_elem.get_text())
            if location_text and not any(word in location_text.lower() for word in ['reputation', 'badge', 'member']):
                user_data['location'] = location_text
        
        return user_data
    
    def _extract_post_user_info(self, post_elem) -> Dict[str, Any]:
        """Extract user information from a post element."""
        user_info = {}
        
        # Find user card/signature
        user_card = post_elem.find('div', {'class': 'user-details'}) or post_elem.find('div', {'class': 'post-signature'})
        
        if user_card:
            # User name
            name_elem = user_card.find('a') or user_card.find('div', {'class': 'user-action-time'})
            if name_elem:
                user_info['display_name'] = clean_text(name_elem.get_text())
                
                # User ID from profile link
                if name_elem.get('href'):
                    href = name_elem['href']
                    user_id_match = re.search(r'/users/(\d+)/', href)
                    if user_id_match:
                        user_info['user_id'] = user_id_match.group(1)
            
            # Reputation
            rep_elem = user_card.find('span', {'class': 'reputation-score'})
            if rep_elem:
                try:
                    rep_text = clean_text(rep_elem.get_text())
                    user_info['reputation'] = int(rep_text.replace(',', ''))
                except (ValueError, TypeError):
                    user_info['reputation'] = 0
        
        return user_info
    
    def _extract_post_timestamps(self, post_elem) -> Dict[str, Any]:
        """Extract timestamp information from a post element."""
        timestamps = {}
        
        # Find timestamp elements
        time_elements = post_elem.find_all('time') or post_elem.find_all('span', {'class': 'relativetime'})
        
        for time_elem in time_elements:
            # Get datetime attribute
            datetime_attr = time_elem.get('datetime') or time_elem.get('title')
            if datetime_attr:
                # Determine if it's creation or modification time based on context
                parent_text = clean_text(time_elem.parent.get_text().lower()) if time_elem.parent else ""
                
                if 'asked' in parent_text or 'answered' in parent_text:
                    timestamps['created_at'] = datetime_attr
                elif 'edited' in parent_text or 'modified' in parent_text:
                    timestamps['last_edited_at'] = datetime_attr
        
        return timestamps
    
    def _extract_comments(self, post_elem, max_comments: int) -> List[Dict[str, Any]]:
        """Extract comments from a post element."""
        comments = []
        
        # Find comments section
        comments_section = post_elem.find('div', {'class': 'comments'}) or post_elem.find_next_sibling('div', {'class': 'comments'})
        
        if not comments_section:
            return comments
        
        # Find individual comments
        comment_elements = comments_section.find_all('div', {'class': 'comment'}) or comments_section.find_all('tr', {'class': 'comment'})
        
        for comment_elem in comment_elements[:max_comments]:
            comment_data = {}
            
            # Comment text
            text_elem = comment_elem.find('span', {'class': 'comment-copy'}) or comment_elem.find('div', {'class': 'comment-text'})
            if text_elem:
                comment_data['text'] = clean_text(text_elem.get_text())
            
            # Comment author
            author_elem = comment_elem.find('a', {'class': 'comment-user'})
            if author_elem:
                comment_data['author'] = clean_text(author_elem.get_text())
                
                # Author user ID
                if author_elem.get('href'):
                    href = author_elem['href']
                    user_id_match = re.search(r'/users/(\d+)/', href)
                    if user_id_match:
                        comment_data['author_user_id'] = user_id_match.group(1)
            
            # Comment timestamp
            time_elem = comment_elem.find('span', {'class': 'comment-date'}) or comment_elem.find('time')
            if time_elem:
                datetime_attr = time_elem.get('datetime') or time_elem.get('title')
                if datetime_attr:
                    comment_data['created_at'] = datetime_attr
            
            # Vote count (if available)
            vote_elem = comment_elem.find('span', {'class': 'comment-score'})
            if vote_elem:
                try:
                    comment_data['vote_count'] = int(clean_text(vote_elem.get_text()))
                except (ValueError, TypeError):
                    comment_data['vote_count'] = 0
            
            comments.append(comment_data)
        
        return comments
    
    def scrape(self, url: str, options: Optional[ScrapingOptions] = None) -> Dict[str, Any]:
        """Main scrape method for compatibility with base class.
        
        Args:
            url: Stack Overflow URL to scrape
            options: Scraping options
            
        Returns:
            Scraped data
        """
        if options is None:
            options = ScrapingOptions()
        
        # Parse URL to determine what to scrape
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        if 'questions' in path_parts:
            # Extract question ID
            question_id_match = re.search(r'/questions/(\d+)', parsed_url.path)
            if question_id_match:
                question_id = question_id_match.group(1)
                return self.scrape_question(question_id, options)
        
        elif 'users' in path_parts:
            # Extract user ID
            user_id_match = re.search(r'/users/(\d+)', parsed_url.path)
            if user_id_match:
                user_id = user_id_match.group(1)
                return self.scrape_user_profile(user_id)
        
        # Fallback to generic web scraping
        return super().scrape(url)


def create_scraping_options_from_args(args) -> ScrapingOptions:
    """Create ScrapingOptions from command line arguments."""
    return ScrapingOptions(
        include_answers=not args.no_answers,
        include_comments=not args.no_comments,
        include_user_info=not args.no_user_info,
        include_tags=not args.no_tags,
        include_vote_counts=not args.no_votes,
        include_timestamps=not args.no_timestamps,
        
        max_questions=args.max_questions,
        max_answers_per_question=args.max_answers,
        max_comments_per_post=args.max_comments,
        
        output_format=args.format,
        output_file=args.output,
        verbose=args.verbose
    )


def print_scraping_summary(data: Union[Dict, List], scrape_type: str) -> None:
    """Print a summary of scraped data."""
    print(f"\n{'='*60}")
    print(f"STACK OVERFLOW SCRAPING SUMMARY: {scrape_type.upper()}")
    print(f"{'='*60}")
    
    if isinstance(data, list):
        print(f"Total items scraped: {len(data)}")
        
        if data and scrape_type == 'questions':
            # Analyze question data
            total_answers = sum(len(q.get('answers', [])) for q in data)
            total_comments = sum(len(q.get('comments', [])) for q in data)
            total_votes = sum(q.get('vote_count', 0) for q in data)
            
            print(f"Total answers: {total_answers}")
            print(f"Total comments: {total_comments}")
            print(f"Total votes: {total_votes}")
            
            # Top tags
            all_tags = []
            for q in data:
                all_tags.extend(q.get('tags', []))
            
            if all_tags:
                from collections import Counter
                top_tags = Counter(all_tags).most_common(5)
                print(f"Top tags: {', '.join([f'{tag}({count})' for tag, count in top_tags])}")
    
    elif isinstance(data, dict):
        if scrape_type == 'question':
            print(f"Question ID: {data.get('question_id', 'Unknown')}")
            print(f"Title: {data.get('title', 'Unknown')[:60]}...")
            print(f"Answers: {len(data.get('answers', []))}")
            print(f"Comments: {len(data.get('comments', []))}")
            print(f"Vote count: {data.get('vote_count', 0)}")
            print(f"Tags: {', '.join(data.get('tags', []))}")
        
        elif scrape_type == 'user':
            print(f"User: {data.get('display_name', 'Unknown')}")
            print(f"Reputation: {data.get('reputation', 0):,}")
            print(f"Questions asked: {data.get('questions_asked', 0)}")
            print(f"Answers given: {data.get('answers_given', 0)}")
            
            badges = data.get('badges', {})
            if badges:
                badge_summary = ', '.join([f"{k.replace('_', ' ')}: {v}" for k, v in badges.items()])
                print(f"Badges: {badge_summary}")
    
    print(f"{'='*60}")


def main():
    """Command-line interface for the Stack Overflow scraper."""
    parser = argparse.ArgumentParser(
        description='Stack Overflow Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
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
        """
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Scraping commands')
    
    # Question command
    question_parser = subparsers.add_parser('question', help='Scrape a single question')
    question_parser.add_argument('question_id', help='Stack Overflow question ID')
    
    # Tag command
    tag_parser = subparsers.add_parser('tag', help='Scrape questions by tag')
    tag_parser.add_argument('tag', help='Tag to filter by (e.g., python, javascript)')
    tag_parser.add_argument('--sort', choices=['newest', 'active', 'votes', 'frequent'], 
                           default='newest', help='Sort order')
    tag_parser.add_argument('--pages', type=int, default=5, help='Maximum pages to scrape')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search questions')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--sort', choices=['relevance', 'newest', 'votes', 'active'], 
                              default='relevance', help='Sort order')
    search_parser.add_argument('--pages', type=int, default=3, help='Maximum pages to scrape')
    
    # User command
    user_parser = subparsers.add_parser('user', help='Scrape user profile')
    user_parser.add_argument('user_id', help='Stack Overflow user ID')
    
    # URL command
    url_parser = subparsers.add_parser('url', help='Scrape from URL')
    url_parser.add_argument('url', help='Stack Overflow URL to scrape')
    
    # Common arguments for all commands
    for subparser in [question_parser, tag_parser, search_parser, url_parser]:
        # What to exclude
        subparser.add_argument('--no-answers', action='store_true', help='Skip answers')
        subparser.add_argument('--no-comments', action='store_true', help='Skip comments')
        subparser.add_argument('--no-user-info', action='store_true', help='Skip user information')
        subparser.add_argument('--no-tags', action='store_true', help='Skip tags')
        subparser.add_argument('--no-votes', action='store_true', help='Skip vote counts')
        subparser.add_argument('--no-timestamps', action='store_true', help='Skip timestamps')
        
        # Limits
        if subparser in [tag_parser, search_parser]:
            subparser.add_argument('--max-questions', type=int, default=100, 
                                 help='Maximum questions to scrape')
        
        subparser.add_argument('--max-answers', type=int, default=50, 
                             help='Maximum answers per question')
        subparser.add_argument('--max-comments', type=int, default=20, 
                             help='Maximum comments per post')
        
        # Output options
        subparser.add_argument('--output', '-o', help='Output file path')
        subparser.add_argument('--format', choices=['json', 'csv'], default='json', 
                             help='Output format')
        subparser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    logger = setup_logging(level=log_level)
    
    # Create scraper
    config = Config()
    scraper = StackOverflowScraper(config)
    
    try:
        # Execute command
        if args.command == 'question':
            options = create_scraping_options_from_args(args)
            data = scraper.scrape_question(args.question_id, options)
            scrape_type = 'question'
            
        elif args.command == 'tag':
            options = create_scraping_options_from_args(args)
            data = scraper.scrape_questions_by_tag(
                args.tag, options, args.sort, args.pages
            )
            scrape_type = 'questions'
            
        elif args.command == 'search':
            options = create_scraping_options_from_args(args)
            data = scraper.search_questions(
                args.query, options, args.sort, args.pages
            )
            scrape_type = 'questions'
            
        elif args.command == 'user':
            data = scraper.scrape_user_profile(args.user_id)
            scrape_type = 'user'
            
        elif args.command == 'url':
            options = create_scraping_options_from_args(args)
            data = scraper.scrape(args.url, options)
            scrape_type = 'url'
        
        # Determine output file
        if args.output:
            output_file = Path(args.output)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if args.command == 'question':
                filename = f"stackoverflow_question_{args.question_id}_{timestamp}"
            elif args.command == 'tag':
                filename = f"stackoverflow_tag_{args.tag}_{timestamp}"
            elif args.command == 'search':
                safe_query = re.sub(r'[^\w\s-]', '', args.query).strip()[:20]
                filename = f"stackoverflow_search_{safe_query}_{timestamp}"
            elif args.command == 'user':
                filename = f"stackoverflow_user_{args.user_id}_{timestamp}"
            else:
                filename = f"stackoverflow_data_{timestamp}"
            
            output_file = Path(f"{filename}.{args.format}")
        
        # Save data
        if args.format == 'json':
            save_to_json(data, output_file)
        elif args.format == 'csv':
            # For CSV, we need to flatten the data
            import pandas as pd
            
            if isinstance(data, list):
                # Flatten each item in the list
                flattened_data = []
                for item in data:
                    flattened_item = {}
                    
                    def flatten_dict(d, parent_key='', sep='_'):
                        items = []
                        for k, v in d.items():
                            new_key = f"{parent_key}{sep}{k}" if parent_key else k
                            if isinstance(v, dict):
                                items.extend(flatten_dict(v, new_key, sep=sep).items())
                            elif isinstance(v, list):
                                # Convert lists to strings for CSV
                                items.append((new_key, '; '.join(map(str, v))))
                            else:
                                items.append((new_key, v))
                        return dict(items)
                    
                    flattened_item = flatten_dict(item)
                    flattened_data.append(flattened_item)
                
                df = pd.DataFrame(flattened_data)
            else:
                # Single item
                def flatten_dict(d, parent_key='', sep='_'):
                    items = []
                    for k, v in d.items():
                        new_key = f"{parent_key}{sep}{k}" if parent_key else k
                        if isinstance(v, dict):
                            items.extend(flatten_dict(v, new_key, sep=sep).items())
                        elif isinstance(v, list):
                            items.append((new_key, '; '.join(map(str, v))))
                        else:
                            items.append((new_key, v))
                    return dict(items)
                
                flattened_data = flatten_dict(data)
                df = pd.DataFrame([flattened_data])
            
            df.to_csv(output_file, index=False)
        
        print(f"✓ Data saved to {output_file}")
        
        # Print summary
        print_scraping_summary(data, scrape_type)
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        scraper.close()


if __name__ == '__main__':
    main()