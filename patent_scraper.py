#!/usr/bin/env python3
"""Standalone Patent scraper script.

This is a convenience wrapper that imports and uses the main Patent scraper
from the research_scrapers package.

For full documentation and features, see src/research_scrapers/patent_scraper.py
and docs/PATENT_SCRAPER_GUIDE.md

Author: Stephen Thompson
"""

import sys
import argparse
from pathlib import Path

# Add src to path to import the package
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

try:
    from research_scrapers.patent_scraper import (
        PatentScraper,
        PatentSearchOptions,
        Patent,
        print_patent_summary,
        print_search_summary,
        CPC_SECTIONS,
        IPC_SECTIONS
    )
    from research_scrapers.config import Config
    from research_scrapers.utils import setup_logging
except ImportError as e:
    print(f"Error importing Patent scraper: {e}")
    print("Please ensure the research_scrapers package is installed.")
    print("Run: pip install -e .")
    sys.exit(1)


def main():
    """Command-line interface for the Patent scraper."""
    parser = argparse.ArgumentParser(
        description='Comprehensive Patent Database Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for patents by keyword
  python patent_scraper.py --keywords "machine learning" --max-results 20
  
  # Search by inventor
  python patent_scraper.py --inventors "John Smith" "Jane Doe" --max-results 50
  
  # Search by assignee/company
  python patent_scraper.py --assignees "Google" --max-results 100
  
  # Search by CPC classification code
  python patent_scraper.py --cpc-codes "G06F" "H04L" --max-results 50
  
  # Get specific patent by number
  python patent_scraper.py --patent-number US10123456B2 --include-full-text
  
  # Batch retrieve patents
  python patent_scraper.py --patent-numbers US10123456 US10234567 --include-claims
  
  # Search recent patents
  python patent_scraper.py --recent-days 30 --keywords "quantum computing" --max-results 50
  
  # Search with date range
  python patent_scraper.py --keywords "neural network" --start-date 2023-01-01 --end-date 2023-12-31
  
  # Export to different formats
  python patent_scraper.py --keywords "blockchain" --format csv --output patents.csv
  
  # Show CPC sections
  python patent_scraper.py --show-cpc-sections
        """
    )
    
    # Search options
    search_group = parser.add_argument_group('Search Options')
    search_group.add_argument('--query', help='General search query')
    search_group.add_argument('--keywords', nargs='+', help='Keywords to search for')
    search_group.add_argument('--inventors', nargs='+', help='Inventor names')
    search_group.add_argument('--assignees', nargs='+', help='Assignee/company names')
    search_group.add_argument('--cpc-codes', nargs='+', help='CPC classification codes')
    search_group.add_argument('--ipc-codes', nargs='+', help='IPC classification codes')
    
    # Date filtering
    date_group = parser.add_argument_group('Date Filtering')
    date_group.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    date_group.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    date_group.add_argument('--recent-days', type=int, help='Search patents from last N days')
    date_group.add_argument('--date-type', choices=['publication', 'filing', 'priority'], 
                           default='publication', help='Type of date to filter by')
    
    # Specific patent options
    patent_group = parser.add_argument_group('Specific Patents')
    patent_group.add_argument('--patent-number', help='Get specific patent by number')
    patent_group.add_argument('--patent-numbers', nargs='+', help='Batch retrieve patents by numbers')
    
    # Content options
    content_group = parser.add_argument_group('Content Options')
    content_group.add_argument('--include-full-text', action='store_true', 
                              help='Include full patent text')
    content_group.add_argument('--include-claims', action='store_true', 
                              help='Include patent claims')
    content_group.add_argument('--include-citations', action='store_true', 
                              help='Include patent citations')
    content_group.add_argument('--include-family', action='store_true', 
                              help='Include patent family information')
    
    # Result options
    result_group = parser.add_argument_group('Result Options')
    result_group.add_argument('--max-results', type=int, default=100, 
                             help='Maximum number of results (default: 100)')
    result_group.add_argument('--start-index', type=int, default=0, 
                             help='Starting index for results (default: 0)')
    result_group.add_argument('--sort-by', choices=['relevance', 'date', 'patent_number'], 
                             default='relevance', help='Sort results by (default: relevance)')
    result_group.add_argument('--sort-order', choices=['ascending', 'descending'], 
                             default='descending', help='Sort order (default: descending)')
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument('--output', '-o', help='Output file path')
    output_group.add_argument('--format', choices=['json', 'csv', 'xml'], 
                             default='json', help='Output format (default: json)')
    output_group.add_argument('--verbose', '-v', action='store_true', 
                             help='Verbose output')
    output_group.add_argument('--show-cpc-sections', action='store_true', 
                             help='Show CPC classification sections')
    output_group.add_argument('--show-ipc-sections', action='store_true', 
                             help='Show IPC classification sections')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    setup_logging(level=log_level)
    
    # Show classification sections if requested
    if args.show_cpc_sections:
        print("CPC Classification Sections:")
        print("=" * 70)
        for code, description in sorted(CPC_SECTIONS.items()):
            print(f"{code}: {description}")
        return
    
    if args.show_ipc_sections:
        print("IPC Classification Sections:")
        print("=" * 70)
        for code, description in sorted(IPC_SECTIONS.items()):
            print(f"{code}: {description}")
        return
    
    # Validate arguments
    if not any([args.query, args.keywords, args.inventors, args.assignees, 
                args.cpc_codes, args.ipc_codes, args.patent_number, 
                args.patent_numbers, args.recent_days]):
        parser.error("Must specify at least one search criterion")
    
    # Create scraper
    config = Config()
    scraper = PatentScraper(config)
    patents = []
    
    try:
        # Handle specific patent number
        if args.patent_number:
            print(f"Fetching patent: {args.patent_number}")
            patent = scraper.get_patent_by_number(
                args.patent_number,
                include_content=(args.include_full_text or args.include_claims or args.include_citations)
            )
            if patent:
                patents = [patent]
                print_patent_summary(patent)
            else:
                print(f"Patent not found: {args.patent_number}")
                sys.exit(1)
        
        # Handle batch patent numbers
        elif args.patent_numbers:
            print(f"Batch retrieving {len(args.patent_numbers)} patents...")
            patents = scraper.batch_get_patents(
                args.patent_numbers,
                include_content=(args.include_full_text or args.include_claims or args.include_citations)
            )
        
        # Handle recent patents search
        elif args.recent_days:
            print(f"Searching patents from last {args.recent_days} days...")
            patents = scraper.search_recent_patents(
                days=args.recent_days,
                keywords=args.keywords,
                max_results=args.max_results
            )
        
        # Handle general search
        else:
            # Create search options
            options = PatentSearchOptions(
                query=args.query,
                keywords=args.keywords,
                inventors=args.inventors,
                assignees=args.assignees,
                cpc_codes=args.cpc_codes,
                ipc_codes=args.ipc_codes,
                start_date=args.start_date,
                end_date=args.end_date,
                date_type=args.date_type,
                max_results=args.max_results,
                start_index=args.start_index,
                sort_by=args.sort_by,
                sort_order=args.sort_order,
                include_full_text=args.include_full_text,
                include_claims=args.include_claims,
                include_citations=args.include_citations,
                include_family=args.include_family,
                output_format=args.format,
                verbose=args.verbose
            )
            
            # Perform search
            print("Searching patents...")
            patents = scraper.scrape(options)
            print_search_summary(patents, options)
        
        # Save results if patents found
        if patents:
            # Determine output file
            if args.output:
                output_file = Path(args.output)
            else:
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"patents_{timestamp}.{args.format}"
                output_file = Path('output') / filename
                output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save patents
            scraper.save_patents(patents, output_file, args.format)
            print(f"\n✓ Saved {len(patents)} patents to {output_file}")
            
            # Print sample if verbose
            if args.verbose and patents:
                print(f"\nSample patent:")
                print_patent_summary(patents[0])
        else:
            print("No patents found matching the search criteria.")
    
    except KeyboardInterrupt:
        print("\nSearch interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during search: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        scraper.close()


if __name__ == '__main__':
    main()
