#!/usr/bin/env python3
"""
ArXiv Scraper Usage Examples

This file demonstrates various ways to use the ArXiv scraper for different
research workflows and use cases.

Author: Stephen Thompson
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path to import arxiv_scraper
sys.path.insert(0, str(Path(__file__).parent.parent))

from arxiv_scraper import ArxivScraper, ArxivSearchOptions, save_papers


def example_basic_search():
    """Basic search example."""
    print("=== Basic ArXiv Search ===")
    
    scraper = ArxivScraper()
    
    # Simple keyword search
    options = ArxivSearchOptions(
        query="machine learning",
        max_results=10
    )
    
    papers = scraper.search_papers(options)
    
    print(f"Found {len(papers)} papers")
    for i, paper in enumerate(papers[:3], 1):
        print(f"\n{i}. {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''}")
        print(f"   Categories: {', '.join(paper.categories)}")
        print(f"   Published: {paper.published[:10]}")
    
    return papers


def example_category_search():
    """Search by specific ArXiv categories."""
    print("\n=== Category-based Search ===")
    
    scraper = ArxivScraper()
    
    # Search AI and Machine Learning categories
    options = ArxivSearchOptions(
        categories=["cs.AI", "cs.LG"],
        max_results=20,
        sort_by="submittedDate",
        sort_order="descending"
    )
    
    papers = scraper.search_papers(options)
    
    print(f"Found {len(papers)} recent AI/ML papers")
    
    # Group by category
    by_category = {}
    for paper in papers:
        for cat in paper.categories:
            if cat in ["cs.AI", "cs.LG"]:
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(paper)
    
    for category, cat_papers in by_category.items():
        print(f"\n{category}: {len(cat_papers)} papers")
        for paper in cat_papers[:2]:
            print(f"  - {paper.title[:60]}...")
    
    return papers


def example_author_search():
    """Search papers by specific authors."""
    print("\n=== Author-based Search ===")
    
    scraper = ArxivScraper()
    
    # Search for papers by famous AI researchers
    options = ArxivSearchOptions(
        authors=["Geoffrey Hinton", "Yann LeCun", "Yoshua Bengio"],
        max_results=15,
        sort_by="submittedDate"
    )
    
    papers = scraper.search_papers(options)
    
    print(f"Found {len(papers)} papers by specified authors")
    
    # Group by first author
    by_author = {}
    for paper in papers:
        first_author = paper.authors[0] if paper.authors else "Unknown"
        if first_author not in by_author:
            by_author[first_author] = []
        by_author[first_author].append(paper)
    
    for author, auth_papers in by_author.items():
        print(f"\n{author}: {len(auth_papers)} papers")
        for paper in auth_papers[:2]:
            print(f"  - {paper.title[:50]}... ({paper.published[:4]})")
    
    return papers


def example_date_range_search():
    """Search papers within a specific date range."""
    print("\n=== Date Range Search ===")
    
    scraper = ArxivScraper()
    
    # Search for papers from the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    options = ArxivSearchOptions(
        query="deep learning",
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        max_results=25
    )
    
    papers = scraper.search_papers(options)
    
    print(f"Found {len(papers)} deep learning papers from last 30 days")
    
    # Group by week
    by_week = {}
    for paper in papers:
        try:
            pub_date = datetime.fromisoformat(paper.published.replace('Z', '+00:00'))
            week_start = pub_date - timedelta(days=pub_date.weekday())
            week_key = week_start.strftime("%Y-%m-%d")
            
            if week_key not in by_week:
                by_week[week_key] = []
            by_week[week_key].append(paper)
        except:
            continue
    
    for week, week_papers in sorted(by_week.items(), reverse=True):
        print(f"\nWeek of {week}: {len(week_papers)} papers")
    
    return papers


def example_full_content_extraction():
    """Example with PDF download and full-text extraction."""
    print("\n=== Full Content Extraction ===")
    
    scraper = ArxivScraper()
    
    # Search with full content extraction
    options = ArxivSearchOptions(
        query="transformer architecture",
        categories=["cs.AI", "cs.CL"],
        max_results=5,  # Small number for demo
        include_pdf=True,
        include_full_text=True,
        extract_references=True
    )
    
    print("Searching and downloading papers (this may take a while)...")
    papers = scraper.search_papers(options)
    
    print(f"Downloaded {len(papers)} papers with full content")
    
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper.title}")
        print(f"   PDF Size: {len(paper.pdf_content) if paper.pdf_content else 0} bytes")
        print(f"   Full Text: {len(paper.full_text) if paper.full_text else 0} characters")
        print(f"   References: {len(paper.references) if paper.references else 0}")
        print(f"   Success: {paper.scraping_success}")
        
        if paper.scraping_errors:
            print(f"   Errors: {', '.join(paper.scraping_errors)}")
    
    return papers


def example_specific_paper():
    """Get a specific paper by ArXiv ID."""
    print("\n=== Specific Paper Retrieval ===")
    
    scraper = ArxivScraper()
    
    # Get a famous paper (Attention Is All You Need)
    paper_id = "1706.03762"  # Transformer paper
    
    print(f"Fetching paper {paper_id}...")
    paper = scraper.get_paper_by_id(paper_id, include_content=True)
    
    if paper:
        print(f"Title: {paper.title}")
        print(f"Authors: {', '.join(paper.authors)}")
        print(f"Abstract: {paper.abstract[:200]}...")
        print(f"Categories: {', '.join(paper.categories)}")
        print(f"Published: {paper.published}")
        print(f"Citations in abstract: {'attention' in paper.abstract.lower()}")
        
        if paper.full_text:
            print(f"Full text length: {len(paper.full_text)} characters")
            # Count occurrences of key terms
            key_terms = ["attention", "transformer", "neural", "network"]
            for term in key_terms:
                count = paper.full_text.lower().count(term)
                print(f"  '{term}' appears {count} times")
    else:
        print("Paper not found!")
    
    return paper


def example_batch_download():
    """Batch download multiple specific papers."""
    print("\n=== Batch Paper Download ===")
    
    scraper = ArxivScraper()
    
    # List of important AI papers
    paper_ids = [
        "1706.03762",  # Attention Is All You Need
        "1512.03385",  # ResNet
        "1409.1556",   # Seq2Seq
        "1406.2661",   # GAN
        "1301.3781"    # Word2Vec
    ]
    
    print(f"Batch downloading {len(paper_ids)} papers...")
    papers = scraper.batch_download_papers(
        paper_ids, 
        include_content=False,  # Skip PDF for faster demo
        max_workers=2
    )
    
    print(f"Successfully downloaded {len(papers)} papers")
    
    for paper in papers:
        year = paper.published[:4] if paper.published else "Unknown"
        print(f"- {paper.title[:50]}... ({year})")
    
    return papers


def example_recent_papers():
    """Get recent papers in specific categories."""
    print("\n=== Recent Papers ===")
    
    scraper = ArxivScraper()
    
    # Get papers from last 7 days in AI categories
    papers = scraper.search_recent_papers(
        days=7,
        categories=["cs.AI", "cs.LG", "cs.CV"],
        max_results=30
    )
    
    print(f"Found {len(papers)} recent papers in AI categories")
    
    # Analyze by category
    category_counts = {}
    for paper in papers:
        for cat in paper.categories:
            if cat.startswith('cs.'):
                category_counts[cat] = category_counts.get(cat, 0) + 1
    
    print("\nPapers by category:")
    for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count}")
    
    # Show most recent
    print(f"\nMost recent papers:")
    sorted_papers = sorted(papers, key=lambda p: p.published, reverse=True)
    for paper in sorted_papers[:3]:
        print(f"  - {paper.title[:60]}... ({paper.published[:10]})")
    
    return papers


def example_literature_review():
    """Comprehensive literature review workflow."""
    print("\n=== Literature Review Workflow ===")
    
    scraper = ArxivScraper()
    
    # Multi-faceted search for a literature review
    topic = "graph neural networks"
    
    # Search different aspects
    searches = [
        ArxivSearchOptions(
            query=f"{topic}",
            max_results=20,
            sort_by="relevance"
        ),
        ArxivSearchOptions(
            query=f"{topic} survey",
            max_results=10,
            sort_by="submittedDate"
        ),
        ArxivSearchOptions(
            query=f"{topic} applications",
            max_results=15,
            sort_by="relevance"
        )
    ]
    
    all_papers = []
    for i, options in enumerate(searches, 1):
        print(f"Search {i}: {options.query}")
        papers = scraper.search_papers(options)
        all_papers.extend(papers)
        print(f"  Found {len(papers)} papers")
    
    # Remove duplicates based on ArXiv ID
    unique_papers = {}
    for paper in all_papers:
        unique_papers[paper.id] = paper
    
    final_papers = list(unique_papers.values())
    print(f"\nTotal unique papers: {len(final_papers)}")
    
    # Analyze publication years
    year_counts = {}
    for paper in final_papers:
        year = paper.published[:4] if paper.published else "Unknown"
        year_counts[year] = year_counts.get(year, 0) + 1
    
    print("\nPapers by year:")
    for year in sorted(year_counts.keys(), reverse=True):
        print(f"  {year}: {year_counts[year]}")
    
    return final_papers


def example_save_and_export():
    """Example of saving papers in different formats."""
    print("\n=== Save and Export ===")
    
    scraper = ArxivScraper()
    
    # Get some papers
    options = ArxivSearchOptions(
        query="computer vision",
        categories=["cs.CV"],
        max_results=10
    )
    
    papers = scraper.search_papers(options)
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Save in different formats
    formats = ["json", "csv", "xml"]
    
    for fmt in formats:
        filename = f"cv_papers.{fmt}"
        filepath = output_dir / filename
        
        print(f"Saving to {filepath}...")
        save_papers(papers, filepath, fmt)
        
        # Check file size
        if filepath.exists():
            size_kb = filepath.stat().st_size / 1024
            print(f"  Saved {len(papers)} papers ({size_kb:.1f} KB)")
    
    return papers


def example_advanced_filtering():
    """Advanced filtering and analysis example."""
    print("\n=== Advanced Filtering ===")
    
    scraper = ArxivScraper()
    
    # Get papers with specific criteria
    options = ArxivSearchOptions(
        query="neural network",
        categories=["cs.AI", "cs.LG"],
        max_results=50
    )
    
    papers = scraper.search_papers(options)
    
    print(f"Initial papers: {len(papers)}")
    
    # Filter by title keywords
    title_keywords = ["deep", "learning", "neural", "network"]
    filtered_papers = []
    
    for paper in papers:
        title_lower = paper.title.lower()
        if any(keyword in title_lower for keyword in title_keywords):
            filtered_papers.append(paper)
    
    print(f"After title filtering: {len(filtered_papers)}")
    
    # Filter by author count (collaborative papers)
    collaborative_papers = [p for p in filtered_papers if len(p.authors) >= 3]
    print(f"Collaborative papers (3+ authors): {len(collaborative_papers)}")
    
    # Filter by recent papers (last 2 years)
    recent_cutoff = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
    recent_papers = []
    
    for paper in collaborative_papers:
        if paper.published and paper.published[:10] >= recent_cutoff:
            recent_papers.append(paper)
    
    print(f"Recent collaborative papers: {len(recent_papers)}")
    
    # Show top papers by author count
    print("\nMost collaborative papers:")
    sorted_by_authors = sorted(recent_papers, key=lambda p: len(p.authors), reverse=True)
    
    for paper in sorted_by_authors[:5]:
        print(f"  - {paper.title[:50]}... ({len(paper.authors)} authors)")
    
    return recent_papers


def main():
    """Run all examples."""
    print("ArXiv Scraper Examples")
    print("=" * 50)
    
    examples = [
        example_basic_search,
        example_category_search,
        example_author_search,
        example_date_range_search,
        example_specific_paper,
        example_batch_download,
        example_recent_papers,
        example_literature_review,
        example_save_and_export,
        example_advanced_filtering,
    ]
    
    # Only run full content extraction if explicitly requested
    if "--include-pdf" in sys.argv:
        examples.insert(4, example_full_content_extraction)
    
    results = {}
    
    for example_func in examples:
        try:
            result = example_func()
            results[example_func.__name__] = result
            print(f"\n✓ {example_func.__name__} completed")
        except Exception as e:
            print(f"\n✗ {example_func.__name__} failed: {e}")
            if "--verbose" in sys.argv:
                import traceback
                traceback.print_exc()
    
    print(f"\n{'='*50}")
    print("Examples Summary:")
    for name, result in results.items():
        if isinstance(result, list):
            print(f"  {name}: {len(result)} papers")
        elif result:
            print(f"  {name}: 1 paper")
        else:
            print(f"  {name}: No results")
    
    print("\nAll examples completed!")
    print("\nTip: Use --include-pdf to run PDF extraction examples")
    print("     Use --verbose for detailed error messages")


if __name__ == "__main__":
    main()