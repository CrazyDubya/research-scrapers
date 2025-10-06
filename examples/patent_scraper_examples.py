#!/usr/bin/env python3
"""
Patent Scraper Examples

Demonstrates various use cases for the PatentScraper class including:
- Basic patent searches
- Advanced filtering by inventors, assignees, CPC codes
- Retrieving specific patents
- Batch patent retrieval
- Full-text and claims extraction
- Citation analysis

Author: Stephen Thompson
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.research_scrapers import PatentScraper, PatentSearchOptions, setup_logging


def example_basic_search():
    """Example 1: Basic keyword search"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Keyword Search")
    print("="*80)
    
    scraper = PatentScraper()
    
    # Search for patents related to machine learning
    options = PatentSearchOptions(
        keywords=["machine learning", "neural network"],
        max_results=10,
        sort_by='date',
        sort_order='descending'
    )
    
    patents = scraper.scrape(options)
    
    print(f"\nFound {len(patents)} patents related to machine learning")
    
    if patents:
        print("\nFirst 3 results:")
        for i, patent in enumerate(patents[:3], 1):
            print(f"\n{i}. {patent.patent_number}")
            print(f"   Title: {patent.title}")
            print(f"   Inventors: {', '.join(patent.inventors[:3])}")
            print(f"   Publication Date: {patent.publication_date}")


def example_search_by_inventor():
    """Example 2: Search patents by inventor"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Search by Inventor")
    print("="*80)
    
    scraper = PatentScraper()
    
    # Search patents by a specific inventor
    patents = scraper.search_by_inventor("John Smith", max_results=20)
    
    print(f"\nFound {len(patents)} patents by John Smith")
    
    if patents:
        # Analyze by year
        years = {}
        for patent in patents:
            year = patent.publication_date[:4] if patent.publication_date else "Unknown"
            years[year] = years.get(year, 0) + 1
        
        print("\nPatents by year:")
        for year, count in sorted(years.items(), reverse=True):
            print(f"  {year}: {count}")


def example_search_by_assignee():
    """Example 3: Search patents by company/assignee"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Search by Assignee/Company")
    print("="*80)
    
    scraper = PatentScraper()
    
    # Search patents assigned to a company
    patents = scraper.search_by_assignee("IBM", max_results=50)
    
    print(f"\nFound {len(patents)} patents assigned to IBM")
    
    if patents:
        # Analyze by CPC codes
        cpc_counts = {}
        for patent in patents:
            for code in patent.cpc_codes or []:
                # Get the main section (first character)
                section = code[0] if code else None
                if section:
                    cpc_counts[section] = cpc_counts.get(section, 0) + 1
        
        print("\nTop CPC sections:")
        for section, count in sorted(cpc_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {section}: {count}")


def example_search_by_cpc_code():
    """Example 4: Search patents by CPC classification"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Search by CPC Classification Code")
    print("="*80)
    
    scraper = PatentScraper()
    
    # Search patents in a specific technology area
    # G06F = Electric digital data processing (Computer Science)
    patents = scraper.search_by_cpc_code("G06F", max_results=30)
    
    print(f"\nFound {len(patents)} patents in CPC code G06F (Digital Data Processing)")
    
    if patents:
        print("\nSample patents:")
        for i, patent in enumerate(patents[:5], 1):
            print(f"\n{i}. {patent.patent_number} - {patent.title}")
            print(f"   Assignees: {', '.join(patent.assignees[:2])}")


def example_advanced_search():
    """Example 5: Advanced search with multiple filters"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Advanced Search with Multiple Filters")
    print("="*80)
    
    scraper = PatentScraper()
    
    # Complex search with multiple criteria
    options = PatentSearchOptions(
        keywords=["artificial intelligence"],
        assignees=["Google", "Microsoft"],
        cpc_codes=["G06N"],  # Computing arrangements based on specific computational models
        start_date="2020-01-01",
        end_date="2023-12-31",
        max_results=25,
        sort_by='date',
        sort_order='descending'
    )
    
    patents = scraper.scrape(options)
    
    print(f"\nFound {len(patents)} AI patents from Google/Microsoft (2020-2023)")
    
    if patents:
        # Group by assignee
        assignee_counts = {}
        for patent in patents:
            for assignee in patent.assignees:
                assignee_counts[assignee] = assignee_counts.get(assignee, 0) + 1
        
        print("\nPatents by assignee:")
        for assignee, count in sorted(assignee_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {assignee}: {count}")


def example_get_specific_patent():
    """Example 6: Get a specific patent by number"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Get Specific Patent by Number")
    print("="*80)
    
    scraper = PatentScraper()
    
    # Get a specific patent with full details
    patent_number = "US10123456B2"
    patent = scraper.get_patent_by_number(patent_number, include_content=True)
    
    if patent:
        print(f"\nPatent: {patent.patent_number}")
        print(f"Title: {patent.title}")
        print(f"Inventors: {', '.join(patent.inventors)}")
        print(f"Assignees: {', '.join(patent.assignees)}")
        print(f"Filing Date: {patent.filing_date}")
        print(f"Grant Date: {patent.grant_date}")
        print(f"\nAbstract:\n{patent.abstract[:300]}...")
        
        if patent.claims:
            print(f"\nNumber of claims: {len(patent.claims)}")
            print(f"Claim 1: {patent.claims[0][:200]}...")
    else:
        print(f"Patent {patent_number} not found")


def example_batch_retrieval():
    """Example 7: Batch retrieve multiple patents"""
    print("\n" + "="*80)
    print("EXAMPLE 7: Batch Patent Retrieval")
    print("="*80)
    
    scraper = PatentScraper()
    
    # List of patent numbers to retrieve
    patent_numbers = [
        "US10000001B2",
        "US10000002B2",
        "US10000003B2",
        "US10000004B2",
        "US10000005B2"
    ]
    
    print(f"Retrieving {len(patent_numbers)} patents in batch...")
    patents = scraper.batch_get_patents(patent_numbers, include_content=False, max_workers=3)
    
    print(f"\nSuccessfully retrieved {len(patents)} patents")
    
    for patent in patents:
        print(f"  {patent.patent_number}: {patent.title}")


def example_recent_patents():
    """Example 8: Find recently published patents"""
    print("\n" + "="*80)
    print("EXAMPLE 8: Recent Patents Search")
    print("="*80)
    
    scraper = PatentScraper()
    
    # Search for patents published in the last 30 days
    patents = scraper.search_recent_patents(
        days=30,
        keywords=["quantum computing"],
        max_results=20
    )
    
    print(f"\nFound {len(patents)} patents on quantum computing from the last 30 days")
    
    if patents:
        print("\nRecent patents:")
        for i, patent in enumerate(patents[:5], 1):
            print(f"\n{i}. {patent.patent_number}")
            print(f"   {patent.title}")
            print(f"   Published: {patent.publication_date}")


def example_with_full_text():
    """Example 9: Search with full text extraction"""
    print("\n" + "="*80)
    print("EXAMPLE 9: Search with Full Text and Claims Extraction")
    print("="*80)
    
    scraper = PatentScraper()
    
    options = PatentSearchOptions(
        keywords=["blockchain"],
        max_results=5,
        include_full_text=True,
        include_claims=True,
        include_citations=True
    )
    
    patents = scraper.scrape(options)
    
    print(f"\nFound {len(patents)} blockchain patents with full content")
    
    if patents:
        patent = patents[0]
        print(f"\nSample patent: {patent.patent_number}")
        print(f"Title: {patent.title}")
        
        if patent.claims:
            print(f"\nNumber of claims: {len(patent.claims)}")
        
        if patent.full_text:
            print(f"Full text length: {len(patent.full_text)} characters")
        
        if patent.cited_patents:
            print(f"Cited patents: {len(patent.cited_patents)}")
            print(f"Sample citations: {', '.join(patent.cited_patents[:5])}")


def example_save_results():
    """Example 10: Save patent search results to file"""
    print("\n" + "="*80)
    print("EXAMPLE 10: Save Patent Search Results")
    print("="*80)
    
    scraper = PatentScraper()
    
    # Search for patents
    options = PatentSearchOptions(
        keywords=["renewable energy"],
        cpc_codes=["H02S"],  # Solar energy generation
        max_results=30
    )
    
    patents = scraper.scrape(options)
    
    print(f"\nFound {len(patents)} patents on renewable energy")
    
    # Save in different formats
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Save as JSON
    json_file = output_dir / "renewable_energy_patents.json"
    scraper.save_patents(patents, json_file, format='json')
    print(f"Saved to JSON: {json_file}")
    
    # Save as CSV
    csv_file = output_dir / "renewable_energy_patents.csv"
    scraper.save_patents(patents, csv_file, format='csv')
    print(f"Saved to CSV: {csv_file}")
    
    # Save as XML
    xml_file = output_dir / "renewable_energy_patents.xml"
    scraper.save_patents(patents, xml_file, format='xml')
    print(f"Saved to XML: {xml_file}")


def example_citation_analysis():
    """Example 11: Patent citation analysis"""
    print("\n" + "="*80)
    print("EXAMPLE 11: Patent Citation Analysis")
    print("="*80)
    
    scraper = PatentScraper()
    
    # Get a patent with citations
    patent_number = "US10000001B2"
    patent = scraper.get_patent_by_number(patent_number, include_content=True)
    
    if patent and patent.cited_patents:
        print(f"\nPatent: {patent.patent_number}")
        print(f"Title: {patent.title}")
        print(f"\nThis patent cites {len(patent.cited_patents)} other patents")
        
        # Build citation network by retrieving cited patents
        print("\nRetrieving cited patents...")
        cited_patents = scraper.batch_get_patents(
            patent.cited_patents[:5],  # Get first 5 for demonstration
            include_content=False,
            max_workers=3
        )
        
        print(f"\nCited patents:")
        for cited in cited_patents:
            print(f"  {cited.patent_number}: {cited.title}")
    else:
        print(f"Patent {patent_number} not found or has no citations")


def main():
    """Run all examples"""
    # Setup logging
    setup_logging(level='INFO')
    
    print("\n" + "="*80)
    print("PATENT SCRAPER EXAMPLES")
    print("="*80)
    print("\nThese examples demonstrate various capabilities of the PatentScraper class")
    
    try:
        # Run examples
        example_basic_search()
        example_search_by_inventor()
        example_search_by_assignee()
        example_search_by_cpc_code()
        example_advanced_search()
        example_get_specific_patent()
        example_batch_retrieval()
        example_recent_patents()
        example_with_full_text()
        example_save_results()
        example_citation_analysis()
        
        print("\n" + "="*80)
        print("ALL EXAMPLES COMPLETED")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
    except Exception as e:
        print(f"\n\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
