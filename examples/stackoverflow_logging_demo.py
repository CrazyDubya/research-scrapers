#!/usr/bin/env python3
"""
Stack Overflow Scraper - Structured Logging Demonstration

This example demonstrates the comprehensive structured logging capabilities
of the Stack Overflow scraper with the new StructuredLogger system.

Features demonstrated:
- JSON structured logging with correlation IDs
- Performance metrics collection
- Request/response logging with sanitization
- Error tracking with full context
- Automatic log rotation
- Multiple log formats (text, JSON, error-only)

Author: Stephen Thompson
"""

import sys
import time
import tempfile
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from research_scrapers.structured_logging import StructuredLogger
from research_scrapers.stackoverflow_scraper import StackOverflowScraper, ScrapingOptions
from research_scrapers.config import Config


def demonstrate_json_structured_logging():
    """Demonstrate JSON structured logging output."""
    
    print("\n" + "="*80)
    print("1. JSON STRUCTURED LOGGING DEMONSTRATION")
    print("="*80)
    
    # Create logger with JSON output
    logger = StructuredLogger(
        name="stackoverflow_json_demo",
        log_dir="demo_logs",
        enable_json=True,
        enable_console=True
    )
    
    # Generate correlation ID for request tracking
    correlation_id = logger.new_correlation_id()
    print(f"🔗 Correlation ID: {correlation_id}")
    
    # Set context for all subsequent logs
    logger.set_context(
        user_id="demo_user_001",
        session_id="session_abc123",
        operation="stackoverflow_scraping",
        environment="demo"
    )
    
    # Log various message types with rich context
    logger.info("Starting Stack Overflow scraping session",
               target_tag="python",
               max_questions=50,
               include_answers=True)
    
    logger.debug("Scraper configuration loaded",
                config_version="2.1.0",
                rate_limit=10,
                timeout_seconds=30)
    
    logger.warning("Approaching rate limit",
                  current_requests=85,
                  limit=100,
                  reset_time="2024-01-15T10:30:00Z")
    
    # Demonstrate request logging with sanitization
    logger.log_request(
        method="GET",
        url="https://stackoverflow.com/questions/tagged/python?api_key=secret123&token=abc456",
        status_code=200,
        duration_ms=245.7,
        sanitize=True,
        response_size_bytes=15420
    )
    
    print("✅ JSON logs written to: demo_logs/stackoverflow_json_demo.json.log")
    
    # Show sample JSON output
    json_log_file = Path("demo_logs/stackoverflow_json_demo.json.log")
    if json_log_file.exists():
        print("\n📄 Sample JSON log entry:")
        with open(json_log_file, 'r') as f:
            import json
            first_line = f.readline().strip()
            if first_line:
                entry = json.loads(first_line)
                print(json.dumps(entry, indent=2, default=str))


def demonstrate_correlation_id_tracking():
    """Demonstrate correlation ID tracking across operations."""
    
    print("\n" + "="*80)
    print("2. CORRELATION ID TRACKING DEMONSTRATION")
    print("="*80)
    
    logger = StructuredLogger(
        name="stackoverflow_correlation_demo",
        log_dir="demo_logs",
        enable_console=True
    )
    
    # Start with specific correlation ID
    correlation_id = logger.new_correlation_id()
    print(f"🔗 Starting workflow with correlation ID: {correlation_id}")
    
    # Simulate multi-step scraping workflow
    workflow_steps = [
        ("initialize_scraper", "Initializing Stack Overflow scraper"),
        ("fetch_question_list", "Fetching questions for tag 'machine-learning'"),
        ("parse_questions", "Parsing 25 question summaries"),
        ("extract_details", "Extracting detailed question data"),
        ("process_answers", "Processing answers and comments"),
        ("save_results", "Saving scraped data to output file")
    ]
    
    for step_name, description in workflow_steps:
        logger.info(f"Workflow step: {description}",
                   workflow_step=step_name,
                   step_number=workflow_steps.index((step_name, description)) + 1,
                   total_steps=len(workflow_steps))
        time.sleep(0.1)  # Simulate processing time
    
    print(f"✅ All workflow steps logged with correlation ID: {correlation_id}")
    print("   This allows tracking the complete request flow across distributed systems")


def demonstrate_performance_metrics():
    """Demonstrate performance metrics collection."""
    
    print("\n" + "="*80)
    print("3. PERFORMANCE METRICS COLLECTION DEMONSTRATION")
    print("="*80)
    
    logger = StructuredLogger(
        name="stackoverflow_performance_demo",
        log_dir="demo_logs",
        enable_console=True
    )
    
    # Simulate realistic scraping operations with metrics
    operations = [
        {
            "name": "scrape_single_question",
            "duration": 0.15,
            "api_calls": 1,
            "items": 1,
            "description": "Scraping individual question #12345678"
        },
        {
            "name": "scrape_questions_by_tag",
            "duration": 2.3,
            "api_calls": 8,
            "items": 50,
            "description": "Bulk scraping questions tagged 'python'"
        },
        {
            "name": "scrape_user_profile",
            "duration": 0.08,
            "api_calls": 1,
            "items": 1,
            "description": "Scraping user profile data"
        },
        {
            "name": "extract_answer_threads",
            "duration": 1.2,
            "api_calls": 15,
            "items": 127,
            "description": "Extracting answers and comment threads"
        }
    ]
    
    print("🚀 Executing operations with performance tracking...")
    
    for op in operations:
        with logger.track_performance(op["name"]) as metrics:
            print(f"   ⏳ {op['description']}")
            time.sleep(op["duration"])
            
            # Set metrics
            metrics.api_calls = op["api_calls"]
            metrics.items_processed = op["items"]
            
            logger.info(f"Completed: {op['description']}",
                       operation=op["name"],
                       items_processed=op["items"],
                       api_calls_made=op["api_calls"])
    
    # Get and display metrics summary
    summary = logger.get_metrics_summary()
    
    print("\n📊 Performance Metrics Summary:")
    print(f"   Total operations: {summary['total_operations']}")
    print(f"   Success rate: {summary['success_rate']:.1f}%")
    print(f"   Average duration: {summary['avg_duration_ms']:.1f}ms")
    print(f"   Total API calls: {summary['total_api_calls']}")
    print(f"   Items processed: {summary['total_items_processed']}")
    print(f"   Min/Max duration: {summary['min_duration_ms']:.1f}ms / {summary['max_duration_ms']:.1f}ms")


def demonstrate_log_rotation():
    """Demonstrate automatic log rotation."""
    
    print("\n" + "="*80)
    print("4. AUTOMATIC LOG ROTATION DEMONSTRATION")
    print("="*80)
    
    # Create logger with small file size to trigger rotation
    logger = StructuredLogger(
        name="stackoverflow_rotation_demo",
        log_dir="demo_logs",
        max_file_size_mb=0.1,  # Very small for demo
        backup_count=3,
        enable_console=False  # Reduce console noise
    )
    
    print("📝 Generating log entries to trigger rotation...")
    
    # Generate enough log data to trigger rotation
    large_data = "x" * 500  # 500 bytes per log entry
    
    for i in range(300):  # Should generate ~150KB of logs
        logger.info(f"Log rotation test entry {i}",
                   entry_number=i,
                   large_field=large_data,
                   timestamp=datetime.now().isoformat())
        
        if i % 50 == 0:
            print(f"   Generated {i} log entries...")
    
    # Check for rotated files
    log_dir = Path("demo_logs")
    log_files = list(log_dir.glob("stackoverflow_rotation_demo.log*"))
    json_files = list(log_dir.glob("stackoverflow_rotation_demo.json.log*"))
    
    print(f"\n📁 Log files created:")
    print(f"   Text logs: {len(log_files)} files")
    for f in sorted(log_files):
        size_kb = f.stat().st_size / 1024
        print(f"     {f.name}: {size_kb:.1f} KB")
    
    print(f"   JSON logs: {len(json_files)} files")
    for f in sorted(json_files):
        size_kb = f.stat().st_size / 1024
        print(f"     {f.name}: {size_kb:.1f} KB")
    
    print("✅ Automatic log rotation working correctly!")


def demonstrate_error_tracking():
    """Demonstrate comprehensive error tracking."""
    
    print("\n" + "="*80)
    print("5. ERROR TRACKING WITH CONTEXT DEMONSTRATION")
    print("="*80)
    
    logger = StructuredLogger(
        name="stackoverflow_error_demo",
        log_dir="demo_logs",
        enable_console=True
    )
    
    # Set up rich context for error tracking
    logger.set_context(
        user_id="error_demo_user",
        session_id="error_session_789",
        scraping_batch="batch_20240115_001"
    )
    
    print("🚨 Simulating various error scenarios...")
    
    # Simulate different types of errors with context
    error_scenarios = [
        {
            "error": ConnectionError("Failed to connect to stackoverflow.com"),
            "context": {
                "url": "https://stackoverflow.com/questions/12345",
                "timeout_seconds": 30,
                "retry_attempt": 3,
                "network_status": "unstable"
            },
            "severity": "high"
        },
        {
            "error": ValueError("Invalid question ID format"),
            "context": {
                "question_id": "invalid_id_abc",
                "expected_format": "numeric",
                "user_input": "abc123def"
            },
            "severity": "medium"
        },
        {
            "error": RuntimeError("Rate limit exceeded"),
            "context": {
                "current_requests": 150,
                "rate_limit": 100,
                "reset_time": "2024-01-15T11:00:00Z",
                "api_endpoint": "/questions"
            },
            "severity": "high"
        }
    ]
    
    for i, scenario in enumerate(error_scenarios, 1):
        print(f"   {i}. {type(scenario['error']).__name__}: {scenario['error']}")
        
        logger.log_exception(
            scenario["error"],
            context=scenario["context"],
            severity=scenario["severity"],
            error_category=type(scenario["error"]).__name__,
            recovery_action="retry_with_backoff" if "rate limit" in str(scenario["error"]).lower() else "user_notification"
        )
    
    print("✅ All errors logged with full context and stack traces")
    print("   Error logs available in: demo_logs/stackoverflow_error_demo.error.log")


def demonstrate_scraper_integration():
    """Demonstrate integration with actual Stack Overflow scraper."""
    
    print("\n" + "="*80)
    print("6. STACK OVERFLOW SCRAPER INTEGRATION DEMONSTRATION")
    print("="*80)
    
    # Create scraper with structured logging
    config = Config()
    scraper = StackOverflowScraper(config)
    
    # Replace with our demo logger
    logger = StructuredLogger(
        name="stackoverflow_integration_demo",
        log_dir="demo_logs",
        enable_console=True,
        enable_json=True
    )
    scraper.logger = logger
    
    # Set up scraping context
    correlation_id = logger.new_correlation_id()
    logger.set_context(
        operation="demo_scraping",
        target="stackoverflow_integration"
    )
    
    print(f"🔗 Integration demo correlation ID: {correlation_id}")
    
    # Configure scraping options
    options = ScrapingOptions(
        include_answers=True,
        include_comments=True,
        max_questions=3,
        verbose=True
    )
    
    # Mock some scraping operations (to avoid actual network calls in demo)
    print("🕷️ Simulating Stack Overflow scraping operations...")
    
    with logger.track_performance("demo_question_scraping") as metrics:
        # Simulate scraping workflow
        logger.info("Starting question scraping", target_questions=3)
        
        for i in range(3):
            question_id = f"demo_question_{i+1}"
            
            logger.debug(f"Processing question {question_id}")
            
            # Simulate HTTP request
            logger.log_request(
                method="GET",
                url=f"https://stackoverflow.com/questions/{question_id}",
                status_code=200,
                duration_ms=150 + (i * 50)
            )
            
            time.sleep(0.1)  # Simulate processing
            
            logger.info(f"Successfully scraped question {question_id}",
                       question_id=question_id,
                       answers_found=2 + i,
                       vote_count=10 + (i * 5))
        
        metrics.items_processed = 3
        metrics.api_calls = 3
    
    # Log completion
    summary = logger.get_metrics_summary()
    logger.info("Demo scraping completed",
               total_questions=3,
               performance_summary=summary)
    
    print("✅ Scraper integration demo completed")
    print(f"   Performance metrics: {summary['total_operations']} operations")
    print(f"   Success rate: {summary['success_rate']}%")


def show_log_file_summary():
    """Show summary of all generated log files."""
    
    print("\n" + "="*80)
    print("LOG FILES SUMMARY")
    print("="*80)
    
    log_dir = Path("demo_logs")
    if not log_dir.exists():
        print("No log directory found.")
        return
    
    log_files = list(log_dir.glob("*.log*"))
    
    if not log_files:
        print("No log files found.")
        return
    
    print(f"📁 Log directory: {log_dir.absolute()}")
    print(f"📄 Total log files: {len(log_files)}")
    
    # Group files by type
    text_logs = [f for f in log_files if f.suffix == '.log']
    json_logs = [f for f in log_files if '.json.log' in f.name]
    error_logs = [f for f in log_files if '.error.log' in f.name]
    
    print(f"\n📋 File breakdown:")
    print(f"   Text logs: {len(text_logs)}")
    print(f"   JSON logs: {len(json_logs)}")
    print(f"   Error logs: {len(error_logs)}")
    
    print(f"\n📊 File details:")
    for log_file in sorted(log_files):
        size_kb = log_file.stat().st_size / 1024
        print(f"   {log_file.name}: {size_kb:.1f} KB")
    
    # Show sample from a JSON log
    sample_json_log = next((f for f in json_logs if f.stat().st_size > 0), None)
    if sample_json_log:
        print(f"\n📄 Sample JSON log entry from {sample_json_log.name}:")
        with open(sample_json_log, 'r') as f:
            import json
            first_line = f.readline().strip()
            if first_line:
                try:
                    entry = json.loads(first_line)
                    print(json.dumps(entry, indent=2, default=str))
                except json.JSONDecodeError:
                    print("   (Unable to parse JSON)")


def main():
    """Run the complete Stack Overflow scraper logging demonstration."""
    
    print("🕷️ STACK OVERFLOW SCRAPER - STRUCTURED LOGGING SYSTEM DEMO")
    print("=" * 100)
    print("This demonstration showcases the comprehensive structured logging")
    print("capabilities integrated with the Stack Overflow scraper.")
    print("=" * 100)
    
    # Create demo logs directory
    Path("demo_logs").mkdir(exist_ok=True)
    
    try:
        # Run all demonstrations
        demonstrate_json_structured_logging()
        demonstrate_correlation_id_tracking()
        demonstrate_performance_metrics()
        demonstrate_log_rotation()
        demonstrate_error_tracking()
        demonstrate_scraper_integration()
        
        # Show summary
        show_log_file_summary()
        
        print("\n" + "="*100)
        print("✅ DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("="*100)
        print("Key features demonstrated:")
        print("  ✓ JSON structured logging with rich context")
        print("  ✓ Correlation ID tracking across operations")
        print("  ✓ Performance metrics collection and analysis")
        print("  ✓ Automatic log rotation by size")
        print("  ✓ Comprehensive error tracking with context")
        print("  ✓ Request/response logging with sanitization")
        print("  ✓ Integration with Stack Overflow scraper")
        print("\nLog files are available in the 'demo_logs' directory for inspection.")
        print("="*100)
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()