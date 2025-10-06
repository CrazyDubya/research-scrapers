#!/usr/bin/env python3
"""
Stack Overflow Scraper Example

This example demonstrates various ways to use the Stack Overflow scraper
for research and data collection purposes.

Author: Stephen Thompson
"""

import sys
import json
from pathlib import Path
from collections import Counter
from datetime import datetime

# Add src to path to import the package
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from research_scrapers import StackOverflowScraper, Config
from research_scrapers.stackoverflow_scraper import ScrapingOptions


def example_1_basic_question_scraping():
    """Example 1: Basic question scraping"""
    print("=" * 60)
    print("EXAMPLE 1: Basic Question Scraping")
    print("=" * 60)
    
    # Initialize scraper
    config = Config()
    scraper = StackOverflowScraper(config)
    
    try:
        # Scrape a well-known question (adjust ID as needed)
        question_id = "11227809"  # "Why is processing a sorted array faster than processing an unsorted array?"
        
        print(f"Scraping question {question_id}...")
        question_data = scraper.scrape_question(question_id)
        
        # Display results
        print(f"Title: {question_data.get('title', 'N/A')}")
        print(f"Vote count: {question_data.get('vote_count', 0)}")
        print(f"View count: {question_data.get('view_count', 0)}")
        print(f"Tags: {', '.join(question_data.get('tags', []))}")
        print(f"Answers: {len(question_data.get('answers', []))}")
        print(f"Comments: {len(question_data.get('comments', []))}")
        
        # Save to file
        output_file = Path("output") / f"question_{question_id}.json"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(question_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Data saved to {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.close()


def example_2_tag_based_research():
    """Example 2: Tag-based research"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Tag-based Research")
    print("=" * 60)
    
    config = Config()
    scraper = StackOverflowScraper(config)
    
    try:
        # Research Python questions
        tag = "python"
        options = ScrapingOptions(
            max_questions=20,  # Limit for demo
            include_answers=True,
            include_comments=False,  # Skip comments for faster scraping
            max_answers_per_question=5
        )
        
        print(f"Researching '{tag}' questions...")
        questions = scraper.scrape_questions_by_tag(tag, options, sort_by='votes')
        
        # Analyze the data
        print(f"\nAnalysis of {len(questions)} {tag} questions:")
        
        # Vote statistics
        votes = [q.get('vote_count', 0) for q in questions]
        print(f"Vote range: {min(votes)} - {max(votes)}")
        print(f"Average votes: {sum(votes) / len(votes):.1f}")
        
        # View statistics
        views = [q.get('view_count', 0) for q in questions if q.get('view_count')]
        if views:
            print(f"View range: {min(views):,} - {max(views):,}")
            print(f"Average views: {sum(views) / len(views):,.0f}")
        
        # Answer statistics
        answer_counts = [len(q.get('answers', [])) for q in questions]
        print(f"Answer range: {min(answer_counts)} - {max(answer_counts)}")
        print(f"Average answers: {sum(answer_counts) / len(answer_counts):.1f}")
        
        # Tag co-occurrence analysis
        all_tags = []
        for q in questions:
            all_tags.extend(q.get('tags', []))
        
        tag_counter = Counter(all_tags)
        print(f"\nTop co-occurring tags:")
        for tag_name, count in tag_counter.most_common(10):
            print(f"  {tag_name}: {count}")
        
        # Save results
        output_file = Path("output") / f"{tag}_research.json"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'tag': tag,
                    'scraped_at': datetime.now().isoformat(),
                    'question_count': len(questions)
                },
                'statistics': {
                    'votes': {'min': min(votes), 'max': max(votes), 'avg': sum(votes) / len(votes)},
                    'views': {'min': min(views) if views else 0, 'max': max(views) if views else 0, 'avg': sum(views) / len(views) if views else 0},
                    'answers': {'min': min(answer_counts), 'max': max(answer_counts), 'avg': sum(answer_counts) / len(answer_counts)}
                },
                'top_tags': tag_counter.most_common(20),
                'questions': questions
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Research data saved to {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.close()


def example_3_user_analysis():
    """Example 3: User profile analysis"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: User Profile Analysis")
    print("=" * 60)
    
    config = Config()
    scraper = StackOverflowScraper(config)
    
    try:
        # Analyze some well-known Stack Overflow users (adjust IDs as needed)
        user_ids = [
            "22656",   # Jon Skeet
            "157882",  # Gordon Linoff
            "1144035", # Martijn Pieters
        ]
        
        user_profiles = []
        
        for user_id in user_ids:
            try:
                print(f"Scraping user profile {user_id}...")
                profile = scraper.scrape_user_profile(user_id)
                user_profiles.append(profile)
                
                print(f"  Name: {profile.get('display_name', 'N/A')}")
                print(f"  Reputation: {profile.get('reputation', 0):,}")
                print(f"  Questions: {profile.get('questions_asked', 0)}")
                print(f"  Answers: {profile.get('answers_given', 0)}")
                
                badges = profile.get('badges', {})
                if badges:
                    print(f"  Badges: Gold={badges.get('gold_badges', 0)}, Silver={badges.get('silver_badges', 0)}, Bronze={badges.get('bronze_badges', 0)}")
                
            except Exception as e:
                print(f"  Error scraping user {user_id}: {e}")
        
        # Analyze user data
        if user_profiles:
            print(f"\nUser Analysis Summary:")
            
            reputations = [p.get('reputation', 0) for p in user_profiles]
            questions = [p.get('questions_asked', 0) for p in user_profiles]
            answers = [p.get('answers_given', 0) for p in user_profiles]
            
            print(f"Reputation range: {min(reputations):,} - {max(reputations):,}")
            print(f"Questions range: {min(questions)} - {max(questions)}")
            print(f"Answers range: {min(answers)} - {max(answers)}")
            
            # Calculate answer-to-question ratios
            ratios = []
            for p in user_profiles:
                q_count = p.get('questions_asked', 0)
                a_count = p.get('answers_given', 0)
                if q_count > 0:
                    ratio = a_count / q_count
                    ratios.append(ratio)
                    print(f"  {p.get('display_name', 'Unknown')}: {ratio:.1f} answers per question")
            
            # Save analysis
            output_file = Path("output") / "user_analysis.json"
            output_file.parent.mkdir(exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': {
                        'scraped_at': datetime.now().isoformat(),
                        'user_count': len(user_profiles)
                    },
                    'statistics': {
                        'reputation': {'min': min(reputations), 'max': max(reputations), 'avg': sum(reputations) / len(reputations)},
                        'questions': {'min': min(questions), 'max': max(questions), 'avg': sum(questions) / len(questions)},
                        'answers': {'min': min(answers), 'max': max(answers), 'avg': sum(answers) / len(answers)}
                    },
                    'users': user_profiles
                }, f, indent=2, ensure_ascii=False)
            
            print(f"✓ User analysis saved to {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.close()


def example_4_search_and_trend_analysis():
    """Example 4: Search and trend analysis"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Search and Trend Analysis")
    print("=" * 60)
    
    config = Config()
    scraper = StackOverflowScraper(config)
    
    try:
        # Search for trending topics
        search_queries = [
            "machine learning",
            "artificial intelligence",
            "deep learning",
            "neural networks"
        ]
        
        all_results = {}
        
        for query in search_queries:
            print(f"Searching for '{query}'...")
            
            options = ScrapingOptions(
                max_questions=15,  # Limit for demo
                include_answers=False,  # Just get question metadata
                include_comments=False
            )
            
            try:
                results = scraper.search_questions(query, options, sort_by='votes')
                all_results[query] = results
                
                if results:
                    votes = [q.get('vote_count', 0) for q in results]
                    views = [q.get('view_count', 0) for q in results if q.get('view_count')]
                    
                    print(f"  Found {len(results)} questions")
                    print(f"  Vote range: {min(votes)} - {max(votes)}")
                    if views:
                        print(f"  View range: {min(views):,} - {max(views):,}")
                    
                    # Extract common tags
                    tags = []
                    for q in results:
                        tags.extend(q.get('tags', []))
                    
                    if tags:
                        top_tags = Counter(tags).most_common(5)
                        print(f"  Top tags: {', '.join([f'{tag}({count})' for tag, count in top_tags])}")
                
            except Exception as e:
                print(f"  Error searching for '{query}': {e}")
        
        # Compare search results
        print(f"\nSearch Comparison:")
        for query, results in all_results.items():
            if results:
                avg_votes = sum(q.get('vote_count', 0) for q in results) / len(results)
                avg_views = sum(q.get('view_count', 0) for q in results if q.get('view_count'))
                avg_views = avg_views / len([q for q in results if q.get('view_count')]) if avg_views else 0
                
                print(f"  {query}: {len(results)} questions, {avg_votes:.1f} avg votes, {avg_views:,.0f} avg views")
        
        # Save search results
        output_file = Path("output") / "search_analysis.json"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'scraped_at': datetime.now().isoformat(),
                    'search_queries': search_queries
                },
                'results': all_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Search analysis saved to {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.close()


def example_5_comprehensive_topic_research():
    """Example 5: Comprehensive topic research"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Comprehensive Topic Research")
    print("=" * 60)
    
    config = Config()
    scraper = StackOverflowScraper(config)
    
    try:
        # Research a specific programming topic comprehensively
        topic = "pandas"  # Change this to any topic you're interested in
        
        print(f"Conducting comprehensive research on '{topic}'...")
        
        # Step 1: Get questions by tag
        print("Step 1: Getting questions by tag...")
        options = ScrapingOptions(
            max_questions=10,  # Limit for demo
            include_answers=True,
            include_comments=True,
            max_answers_per_question=3,
            max_comments_per_post=5
        )
        
        tag_questions = scraper.scrape_questions_by_tag(topic, options, sort_by='votes')
        
        # Step 2: Search for related questions
        print("Step 2: Searching for related questions...")
        search_questions = scraper.search_questions(f"{topic} tutorial", options, sort_by='votes')
        
        # Step 3: Analyze contributors
        print("Step 3: Analyzing top contributors...")
        contributor_ids = set()
        
        for questions in [tag_questions, search_questions]:
            for q in questions:
                if q.get('author', {}).get('user_id'):
                    contributor_ids.add(q['author']['user_id'])
                
                for answer in q.get('answers', []):
                    if answer.get('author', {}).get('user_id'):
                        contributor_ids.add(answer['author']['user_id'])
        
        # Get profiles of top contributors (limit to avoid too many requests)
        contributor_profiles = []
        for user_id in list(contributor_ids)[:5]:
            try:
                profile = scraper.scrape_user_profile(user_id)
                contributor_profiles.append(profile)
            except Exception as e:
                print(f"  Failed to get profile for user {user_id}: {e}")
        
        # Step 4: Compile comprehensive report
        print("Step 4: Compiling comprehensive report...")
        
        all_questions = tag_questions + search_questions
        
        # Remove duplicates based on question_id
        seen_ids = set()
        unique_questions = []
        for q in all_questions:
            qid = q.get('question_id')
            if qid and qid not in seen_ids:
                seen_ids.add(qid)
                unique_questions.append(q)
        
        # Statistics
        total_votes = sum(q.get('vote_count', 0) for q in unique_questions)
        total_views = sum(q.get('view_count', 0) for q in unique_questions if q.get('view_count'))
        total_answers = sum(len(q.get('answers', [])) for q in unique_questions)
        total_comments = sum(len(q.get('comments', [])) for q in unique_questions)
        
        # Tag analysis
        all_tags = []
        for q in unique_questions:
            all_tags.extend(q.get('tags', []))
        
        tag_analysis = Counter(all_tags).most_common(15)
        
        # Create comprehensive report
        report = {
            'metadata': {
                'topic': topic,
                'scraped_at': datetime.now().isoformat(),
                'research_scope': 'comprehensive'
            },
            'summary': {
                'total_questions': len(unique_questions),
                'total_votes': total_votes,
                'total_views': total_views,
                'total_answers': total_answers,
                'total_comments': total_comments,
                'contributors_analyzed': len(contributor_profiles)
            },
            'tag_analysis': tag_analysis,
            'top_contributors': contributor_profiles,
            'questions': unique_questions
        }
        
        # Display summary
        print(f"\nComprehensive Research Summary for '{topic}':")
        print(f"  Questions analyzed: {len(unique_questions)}")
        print(f"  Total votes: {total_votes:,}")
        print(f"  Total views: {total_views:,}")
        print(f"  Total answers: {total_answers}")
        print(f"  Total comments: {total_comments}")
        print(f"  Contributors analyzed: {len(contributor_profiles)}")
        
        print(f"\nTop related tags:")
        for tag, count in tag_analysis[:10]:
            print(f"    {tag}: {count}")
        
        print(f"\nTop contributors:")
        for contributor in contributor_profiles:
            name = contributor.get('display_name', 'Unknown')
            rep = contributor.get('reputation', 0)
            print(f"    {name}: {rep:,} reputation")
        
        # Save comprehensive report
        output_file = Path("output") / f"{topic}_comprehensive_research.json"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Comprehensive research report saved to {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.close()


def main():
    """Run all examples"""
    print("Stack Overflow Scraper Examples")
    print("===============================")
    print("This script demonstrates various use cases for the Stack Overflow scraper.")
    print("Note: Examples use limited data for demonstration purposes.")
    print()
    
    # Create output directory
    Path("output").mkdir(exist_ok=True)
    
    # Run examples
    try:
        example_1_basic_question_scraping()
        example_2_tag_based_research()
        example_3_user_analysis()
        example_4_search_and_trend_analysis()
        example_5_comprehensive_topic_research()
        
        print("\n" + "=" * 60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("Check the 'output' directory for generated files.")
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
    except Exception as e:
        print(f"\nError running examples: {e}")


if __name__ == '__main__':
    main()