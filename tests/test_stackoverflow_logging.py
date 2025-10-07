#!/usr/bin/env python3
"""
Comprehensive test suite for Stack Overflow scraper with StructuredLogger integration.

This test demonstrates and verifies:
- JSON structured logging output
- Correlation ID tracking across operations
- Automatic log rotation capabilities
- Performance metrics collection
- Request/response logging with sanitization
- Error tracking with full context
- Integration between StackOverflowScraper and StructuredLogger

Author: Stephen Thompson
"""

import pytest
import tempfile
import json
import time
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from research_scrapers.structured_logging import (
    StructuredLogger,
    LogContext,
    PerformanceMetrics,
    JSONFormatter
)
from research_scrapers.stackoverflow_scraper import (
    StackOverflowScraper,
    ScrapingOptions
)
from research_scrapers.config import Config


class TestStackOverflowScraperLogging:
    """Test Stack Overflow scraper with structured logging integration."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"
        
        # Create structured logger with all features enabled
        self.logger = StructuredLogger(
            name="stackoverflow_test",
            log_dir=str(self.log_dir),
            log_level="DEBUG",
            enable_json=True,
            enable_console=True,
            max_file_size_mb=1,  # Small for testing rotation
            backup_count=3
        )
        
        # Create scraper with mocked config
        self.config = Config()
        self.scraper = StackOverflowScraper(self.config)
        
        # Replace scraper's logger with our test logger
        self.scraper.logger = self.logger
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_json_structured_logging_output(self):
        """Test that JSON logs are properly structured and contain required fields."""
        
        # Generate some log entries
        correlation_id = self.logger.new_correlation_id()
        self.logger.set_context(
            user_id="test_user_123",
            session_id="session_456",
            operation="stackoverflow_scraping"
        )
        
        # Log various types of messages
        self.logger.info("Starting Stack Overflow scraping", 
                        target_tag="python", 
                        max_questions=10)
        
        self.logger.log_request(
            method="GET",
            url="https://stackoverflow.com/questions/tagged/python?api_key=secret123",
            status_code=200,
            duration_ms=245.7,
            sanitize=True
        )
        
        self.logger.warning("Rate limit approaching", 
                           remaining_requests=5,
                           reset_time="2024-01-15T10:30:00Z")
        
        try:
            raise ValueError("Mock scraping error for testing")
        except ValueError as e:
            self.logger.log_exception(
                e,
                context={
                    "question_id": "12345678",
                    "scraping_stage": "answer_extraction"
                }
            )
        
        # Verify JSON log file exists and contains structured data
        json_log_file = self.log_dir / "stackoverflow_test.json.log"
        assert json_log_file.exists(), "JSON log file should be created"
        
        # Read and parse JSON log entries
        log_entries = []
        with open(json_log_file, 'r') as f:
            for line in f:
                if line.strip():
                    log_entries.append(json.loads(line.strip()))
        
        assert len(log_entries) >= 4, "Should have at least 4 log entries"
        
        # Verify structure of first log entry (info message)
        info_entry = log_entries[0]
        required_fields = [
            'timestamp', 'level', 'logger', 'message', 
            'module', 'function', 'line', 'correlation_id'
        ]
        
        for field in required_fields:
            assert field in info_entry, f"Required field '{field}' missing from log entry"
        
        # Verify context fields
        assert info_entry['correlation_id'] == correlation_id
        assert info_entry['user_id'] == "test_user_123"
        assert info_entry['session_id'] == "session_456"
        assert info_entry['operation'] == "stackoverflow_scraping"
        assert info_entry['target_tag'] == "python"
        assert info_entry['max_questions'] == 10
        
        # Verify request log entry structure
        request_entry = next(e for e in log_entries if e.get('event') == 'http_request')
        assert request_entry['method'] == 'GET'
        assert request_entry['status_code'] == 200
        assert request_entry['duration_ms'] == 245.7
        # Verify URL sanitization
        assert 'secret123' not in request_entry['url']
        assert '***REDACTED***' in request_entry['url']
        
        # Verify exception log entry
        exception_entry = next(e for e in log_entries if e.get('event') == 'exception')
        assert exception_entry['exception_type'] == 'ValueError'
        assert 'Mock scraping error' in exception_entry['exception_message']
        assert 'question_id' in exception_entry['context']
        assert exception_entry['context']['question_id'] == "12345678"
        
        print("✓ JSON structured logging verification complete")
        self._print_sample_json_logs(log_entries[:2])
    
    def test_correlation_id_tracking(self):
        """Test correlation ID tracking across multiple operations."""
        
        # Start with a specific correlation ID
        correlation_id = self.logger.new_correlation_id()
        
        # Simulate scraping workflow with multiple operations
        operations = [
            ("fetch_question_list", "Fetching questions for tag 'python'"),
            ("parse_question_data", "Parsing question #12345678"),
            ("extract_answers", "Extracting 5 answers"),
            ("save_results", "Saving scraped data to file")
        ]
        
        for op_name, message in operations:
            with self.logger.track_performance(op_name) as metrics:
                self.logger.info(message, operation_step=op_name)
                time.sleep(0.01)  # Simulate work
                metrics.items_processed = 1
        
        # Verify all operations have the same correlation ID
        json_log_file = self.log_dir / "stackoverflow_test.json.log"
        log_entries = []
        with open(json_log_file, 'r') as f:
            for line in f:
                if line.strip():
                    log_entries.append(json.loads(line.strip()))
        
        # Filter entries for our operations
        operation_entries = [e for e in log_entries if e.get('operation_step')]
        
        assert len(operation_entries) == 4, "Should have 4 operation log entries"
        
        # All should have the same correlation ID
        for entry in operation_entries:
            assert entry['correlation_id'] == correlation_id, \
                f"Entry should have correlation ID {correlation_id}"
        
        print(f"✓ Correlation ID tracking verified: {correlation_id}")
        print(f"  Tracked across {len(operation_entries)} operations")
    
    def test_automatic_log_rotation(self):
        """Test automatic log rotation when file size limits are reached."""
        
        # Generate enough log data to trigger rotation
        # (We set max_file_size_mb=1 in setup, so this should rotate)
        
        large_data = "x" * 1000  # 1KB of data per log
        
        for i in range(1500):  # Should generate ~1.5MB of logs
            self.logger.info(f"Large log entry {i}", 
                           large_field=large_data,
                           iteration=i)
        
        # Check for rotated files
        log_files = list(self.log_dir.glob("stackoverflow_test.log*"))
        json_log_files = list(self.log_dir.glob("stackoverflow_test.json.log*"))
        
        # Should have main file plus rotated files
        assert len(log_files) > 1, "Should have rotated log files"
        assert len(json_log_files) > 1, "Should have rotated JSON log files"
        
        # Verify backup files exist
        backup_files = [f for f in log_files if f.name.endswith(('.1', '.2', '.3'))]
        json_backup_files = [f for f in json_log_files if f.name.endswith(('.1', '.2', '.3'))]
        
        assert len(backup_files) > 0, "Should have backup log files"
        assert len(json_backup_files) > 0, "Should have backup JSON log files"
        
        print("✓ Automatic log rotation verified")
        print(f"  Text log files: {len(log_files)}")
        print(f"  JSON log files: {len(json_log_files)}")
        print(f"  Backup files created: {len(backup_files)} text, {len(json_backup_files)} JSON")
    
    def test_performance_metrics_collection(self):
        """Test comprehensive performance metrics collection."""
        
        # Simulate realistic Stack Overflow scraping operations
        scraping_scenarios = [
            {
                "operation": "scrape_question_by_id",
                "duration": 0.15,
                "api_calls": 1,
                "items": 1,
                "success": True
            },
            {
                "operation": "scrape_questions_by_tag", 
                "duration": 2.3,
                "api_calls": 5,
                "items": 25,
                "success": True
            },
            {
                "operation": "scrape_user_profile",
                "duration": 0.08,
                "api_calls": 1,
                "items": 1,
                "success": True
            },
            {
                "operation": "scrape_question_with_error",
                "duration": 0.5,
                "api_calls": 2,
                "items": 0,
                "success": False
            }
        ]
        
        # Execute operations and collect metrics
        for scenario in scraping_scenarios:
            with self.logger.track_performance(scenario["operation"]) as metrics:
                time.sleep(scenario["duration"])
                metrics.api_calls = scenario["api_calls"]
                metrics.items_processed = scenario["items"]
                
                if not scenario["success"]:
                    raise Exception("Simulated scraping error")
        
        # Get metrics summary
        summary = self.logger.get_metrics_summary()
        
        # Verify metrics
        assert summary['total_operations'] == 4
        assert summary['successful'] == 3
        assert summary['failed'] == 1
        assert summary['success_rate'] == 75.0
        assert summary['total_api_calls'] == 9  # 1+5+1+2
        assert summary['total_items_processed'] == 27  # 1+25+1+0
        assert summary['avg_duration_ms'] > 0
        
        # Verify individual metrics
        metrics = self.logger.metrics
        assert len(metrics) == 4
        
        # Check successful operation
        successful_ops = [m for m in metrics if m.success]
        assert len(successful_ops) == 3
        
        # Check failed operation
        failed_ops = [m for m in metrics if not m.success]
        assert len(failed_ops) == 1
        assert "Simulated scraping error" in failed_ops[0].error
        
        print("✓ Performance metrics collection verified")
        print(f"  Operations tracked: {summary['total_operations']}")
        print(f"  Success rate: {summary['success_rate']}%")
        print(f"  Total API calls: {summary['total_api_calls']}")
        print(f"  Items processed: {summary['total_items_processed']}")
        print(f"  Avg duration: {summary['avg_duration_ms']:.1f}ms")
    
    @patch('requests.Session.get')
    def test_request_response_logging_with_sanitization(self, mock_get):
        """Test HTTP request/response logging with sensitive data sanitization."""
        
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Mock Stack Overflow content</body></html>"
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_get.return_value = mock_response
        
        # Configure scraper options
        options = ScrapingOptions(
            max_questions=1,
            include_answers=True,
            verbose=True
        )
        
        # Simulate scraping with sensitive URLs
        sensitive_urls = [
            "https://stackoverflow.com/questions/12345?api_key=secret123",
            "https://api.stackexchange.com/2.3/questions?token=abc123def456",
            "https://stackoverflow.com/users/789?password=mypassword"
        ]
        
        for url in sensitive_urls:
            start_time = time.time()
            
            try:
                response = self.scraper.get_page(url)
                duration = (time.time() - start_time) * 1000
                
                self.logger.log_request(
                    method="GET",
                    url=url,
                    status_code=response.status_code,
                    duration_ms=duration,
                    sanitize=True,
                    user_agent=self.scraper.session.headers.get('User-Agent'),
                    content_type=response.headers.get('Content-Type')
                )
                
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                self.logger.log_request(
                    method="GET",
                    url=url,
                    status_code=None,
                    duration_ms=duration,
                    sanitize=True,
                    error=str(e)
                )
        
        # Verify request logging and sanitization
        json_log_file = self.log_dir / "stackoverflow_test.json.log"
        log_entries = []
        with open(json_log_file, 'r') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line.strip())
                    if entry.get('event') == 'http_request':
                        log_entries.append(entry)
        
        assert len(log_entries) == 3, "Should have 3 request log entries"
        
        # Verify sanitization
        for entry in log_entries:
            url = entry['url']
            
            # Sensitive data should be redacted
            assert 'secret123' not in url, "API key should be sanitized"
            assert 'abc123def456' not in url, "Token should be sanitized"
            assert 'mypassword' not in url, "Password should be sanitized"
            
            # Redaction markers should be present
            if 'api_key' in entry['url'] or 'token' in entry['url'] or 'password' in entry['url']:
                assert '***REDACTED***' in url, "Should contain redaction marker"
            
            # Other fields should be present
            assert entry['method'] == 'GET'
            assert 'duration_ms' in entry
            assert entry['status_code'] == 200
        
        print("✓ Request/response logging with sanitization verified")
        print("  Sensitive parameters properly redacted:")
        for entry in log_entries:
            print(f"    {entry['url']}")
    
    def test_error_tracking_with_context(self):
        """Test comprehensive error tracking with full context."""
        
        # Set up rich context
        self.logger.set_context(
            user_id="user_789",
            session_id="session_abc123",
            scraping_batch_id="batch_20240115_001"
        )
        
        # Simulate various error scenarios
        error_scenarios = [
            {
                "error_type": "NetworkError",
                "message": "Connection timeout to stackoverflow.com",
                "context": {
                    "url": "https://stackoverflow.com/questions/12345",
                    "timeout_seconds": 30,
                    "retry_attempt": 3
                }
            },
            {
                "error_type": "ParseError", 
                "message": "Failed to extract question data",
                "context": {
                    "question_id": "67890",
                    "html_length": 15420,
                    "missing_elements": ["title", "vote_count"]
                }
            },
            {
                "error_type": "RateLimitError",
                "message": "API rate limit exceeded",
                "context": {
                    "rate_limit": 100,
                    "requests_made": 150,
                    "reset_time": "2024-01-15T11:00:00Z"
                }
            }
        ]
        
        for scenario in error_scenarios:
            try:
                # Create appropriate exception type
                if scenario["error_type"] == "NetworkError":
                    raise ConnectionError(scenario["message"])
                elif scenario["error_type"] == "ParseError":
                    raise ValueError(scenario["message"])
                else:
                    raise RuntimeError(scenario["message"])
                    
            except Exception as e:
                self.logger.log_exception(
                    e,
                    context=scenario["context"],
                    error_category=scenario["error_type"],
                    severity="high" if "rate limit" in scenario["message"].lower() else "medium"
                )
        
        # Verify error logging
        json_log_file = self.log_dir / "stackoverflow_test.json.log"
        error_entries = []
        with open(json_log_file, 'r') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line.strip())
                    if entry.get('event') == 'exception':
                        error_entries.append(entry)
        
        assert len(error_entries) == 3, "Should have 3 error log entries"
        
        # Verify error entry structure and context
        for i, entry in enumerate(error_entries):
            scenario = error_scenarios[i]
            
            # Basic exception info
            assert entry['exception_message'] == scenario["message"]
            assert 'traceback' in entry
            assert 'context' in entry
            
            # Context preservation
            for key, value in scenario["context"].items():
                assert entry['context'][key] == value
            
            # Additional fields
            assert entry['error_category'] == scenario["error_type"]
            assert 'severity' in entry
            
            # Global context should be preserved
            assert entry['user_id'] == "user_789"
            assert entry['session_id'] == "session_abc123"
            assert entry['scraping_batch_id'] == "batch_20240115_001"
        
        print("✓ Error tracking with context verified")
        print(f"  Errors logged: {len(error_entries)}")
        print("  Context preserved for each error:")
        for entry in error_entries:
            print(f"    {entry['exception_type']}: {entry['exception_message']}")
    
    def test_integration_with_stackoverflow_scraper(self):
        """Test full integration between StackOverflowScraper and StructuredLogger."""
        
        # Mock the HTTP requests to avoid actual network calls
        with patch('requests.Session.get') as mock_get:
            # Mock question page response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = """
            <html>
                <body>
                    <div class="question" data-questionid="12345">
                        <h1 class="fs-headline1">How to use Python logging?</h1>
                        <div class="s-prose">
                            <p>I need help with Python logging configuration...</p>
                        </div>
                        <div class="js-vote-count">42</div>
                        <a class="post-tag">python</a>
                        <a class="post-tag">logging</a>
                    </div>
                    <div class="answer" data-answerid="67890">
                        <div class="s-prose">
                            <p>You can configure logging like this...</p>
                        </div>
                        <div class="js-vote-count">15</div>
                    </div>
                </body>
            </html>
            """
            mock_get.return_value = mock_response
            
            # Configure scraping options
            options = ScrapingOptions(
                include_answers=True,
                include_comments=True,
                max_questions=1,
                verbose=True
            )
            
            # Perform scraping with logging
            correlation_id = self.logger.new_correlation_id()
            self.logger.set_context(
                operation="integration_test",
                target="question_12345"
            )
            
            with self.logger.track_performance("scrape_stackoverflow_question") as metrics:
                try:
                    result = self.scraper.scrape_question("12345", options)
                    metrics.items_processed = 1
                    metrics.api_calls = 1
                    
                    self.logger.info("Scraping completed successfully",
                                   question_id="12345",
                                   title=result.get('title', 'Unknown'),
                                   answers_found=len(result.get('answers', [])),
                                   vote_count=result.get('vote_count', 0))
                    
                except Exception as e:
                    self.logger.log_exception(e, context={"question_id": "12345"})
                    raise
        
        # Verify integration logging
        json_log_file = self.log_dir / "stackoverflow_test.json.log"
        log_entries = []
        with open(json_log_file, 'r') as f:
            for line in f:
                if line.strip():
                    log_entries.append(json.loads(line.strip()))
        
        # Should have various types of log entries
        info_entries = [e for e in log_entries if e['level'] == 'INFO']
        performance_entries = [e for e in log_entries if 'operation' in e and e.get('duration_ms')]
        
        assert len(info_entries) > 0, "Should have info log entries"
        
        # Verify performance tracking worked
        assert len(self.logger.metrics) > 0, "Should have performance metrics"
        scrape_metrics = [m for m in self.logger.metrics if m.operation == "scrape_stackoverflow_question"]
        assert len(scrape_metrics) == 1, "Should have scraping performance metrics"
        
        metrics = scrape_metrics[0]
        assert metrics.success == True
        assert metrics.items_processed == 1
        assert metrics.api_calls == 1
        
        print("✓ StackOverflowScraper integration verified")
        print(f"  Log entries generated: {len(log_entries)}")
        print(f"  Performance metrics: {len(self.logger.metrics)}")
        print(f"  Correlation ID: {correlation_id}")
    
    def _print_sample_json_logs(self, entries):
        """Print sample JSON log entries for demonstration."""
        print("\n" + "="*80)
        print("SAMPLE JSON STRUCTURED LOG ENTRIES")
        print("="*80)
        
        for i, entry in enumerate(entries, 1):
            print(f"\n--- Log Entry {i} ---")
            print(json.dumps(entry, indent=2, default=str))
        
        print("="*80)
    
    def test_log_file_structure(self):
        """Test that all expected log files are created with proper structure."""
        
        # Generate some log activity
        self.logger.info("Test message")
        self.logger.error("Test error")
        
        # Check file structure
        expected_files = [
            "stackoverflow_test.log",          # Main text log
            "stackoverflow_test.json.log",     # JSON structured log  
            "stackoverflow_test.error.log"     # Error-only log
        ]
        
        for filename in expected_files:
            file_path = self.log_dir / filename
            assert file_path.exists(), f"Expected log file {filename} should exist"
            assert file_path.stat().st_size > 0, f"Log file {filename} should not be empty"
        
        print("✓ Log file structure verified")
        print(f"  Log directory: {self.log_dir}")
        for filename in expected_files:
            file_path = self.log_dir / filename
            size = file_path.stat().st_size
            print(f"    {filename}: {size} bytes")


def run_comprehensive_logging_demo():
    """Run a comprehensive demonstration of the logging system."""
    
    print("\n" + "="*100)
    print("STACK OVERFLOW SCRAPER - STRUCTURED LOGGING DEMONSTRATION")
    print("="*100)
    
    # Create temporary directory for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        log_dir = Path(temp_dir) / "demo_logs"
        
        # Initialize structured logger
        logger = StructuredLogger(
            name="stackoverflow_demo",
            log_dir=str(log_dir),
            log_level="DEBUG",
            enable_json=True,
            enable_console=True,
            max_file_size_mb=5,
            backup_count=3
        )
        
        print(f"\n📁 Log files will be created in: {log_dir}")
        
        # Demonstrate correlation ID tracking
        correlation_id = logger.new_correlation_id()
        print(f"🔗 Generated correlation ID: {correlation_id}")
        
        # Set up context
        logger.set_context(
            user_id="demo_user_123",
            session_id="demo_session_456",
            operation="stackoverflow_demo"
        )
        
        # Demonstrate various logging features
        print("\n🚀 Starting demonstration...")
        
        # 1. Basic logging with context
        logger.info("Demo started", demo_version="1.0", environment="test")
        
        # 2. Performance tracking
        with logger.track_performance("demo_scraping_simulation") as metrics:
            time.sleep(0.1)
            metrics.api_calls = 3
            metrics.items_processed = 15
            logger.info("Simulated scraping 15 Stack Overflow questions")
        
        # 3. Request logging with sanitization
        logger.log_request(
            method="GET",
            url="https://stackoverflow.com/api/questions?key=secret123&token=abc456",
            status_code=200,
            duration_ms=234.5,
            sanitize=True
        )
        
        # 4. Error logging
        try:
            raise ValueError("Demo error for logging showcase")
        except ValueError as e:
            logger.log_exception(e, context={"demo_stage": "error_demonstration"})
        
        # 5. Get metrics summary
        summary = logger.get_metrics_summary()
        logger.info("Demo completed", metrics_summary=summary)
        
        print("✅ Demonstration completed!")
        
        # Show log files created
        print(f"\n📋 Log files created:")
        for log_file in sorted(log_dir.glob("*.log*")):
            size = log_file.stat().st_size
            print(f"   {log_file.name}: {size} bytes")
        
        # Show sample JSON log content
        json_log = log_dir / "stackoverflow_demo.json.log"
        if json_log.exists():
            print(f"\n📄 Sample JSON log entries from {json_log.name}:")
            with open(json_log, 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines[:3], 1):
                    if line.strip():
                        entry = json.loads(line.strip())
                        print(f"\n--- Entry {i} ---")
                        print(json.dumps(entry, indent=2, default=str))
        
        print(f"\n📊 Performance Metrics Summary:")
        for key, value in summary.items():
            print(f"   {key}: {value}")


if __name__ == '__main__':
    # Run the comprehensive demo
    run_comprehensive_logging_demo()
    
    # Run the test suite
    print("\n" + "="*100)
    print("RUNNING TEST SUITE")
    print("="*100)
    pytest.main([__file__, '-v', '-s'])