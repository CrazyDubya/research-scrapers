"""Tests for utils module."""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from research_scrapers.utils import (
    clean_text,
    save_to_json,
    load_from_json,
    validate_url,
    extract_domain,
    batch_process,
    merge_dicts,
    rate_limit,
    retry_on_failure
)


class TestTextProcessing:
    """Test text processing utilities."""
    
    def test_clean_text_basic(self):
        """Test basic text cleaning."""
        text = "  Hello   World  \n\t  "
        result = clean_text(text)
        assert result == "Hello World"
    
    def test_clean_text_empty(self):
        """Test cleaning empty text."""
        assert clean_text("") == ""
        assert clean_text(None) == ""
    
    def test_clean_text_special_chars(self):
        """Test cleaning text with special characters."""
        text = "Hello\x00World\x08Test"
        result = clean_text(text)
        assert result == "HelloWorldTest"


class TestFileOperations:
    """Test file operation utilities."""
    
    def test_save_and_load_json(self):
        """Test saving and loading JSON data."""
        test_data = {
            "name": "test",
            "values": [1, 2, 3],
            "nested": {"key": "value"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Test saving
            save_to_json(test_data, temp_path)
            
            # Verify file exists and has content
            assert Path(temp_path).exists()
            
            # Test loading
            loaded_data = load_from_json(temp_path)
            assert loaded_data == test_data
        
        finally:
            # Clean up
            Path(temp_path).unlink(missing_ok=True)
    
    def test_save_json_creates_directory(self):
        """Test that save_to_json creates parent directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "subdir" / "test.json"
            test_data = {"test": "data"}
            
            save_to_json(test_data, file_path)
            
            assert file_path.exists()
            loaded_data = load_from_json(file_path)
            assert loaded_data == test_data


class TestUrlUtilities:
    """Test URL-related utilities."""
    
    def test_validate_url_valid(self):
        """Test URL validation with valid URLs."""
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://subdomain.example.com",
            "https://example.com/path",
            "https://example.com:8080",
            "http://localhost:3000",
            "https://192.168.1.1"
        ]
        
        for url in valid_urls:
            assert validate_url(url), f"URL should be valid: {url}"
    
    def test_validate_url_invalid(self):
        """Test URL validation with invalid URLs."""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",
            "example.com",
            "https://",
            "",
            "javascript:alert('xss')"
        ]
        
        for url in invalid_urls:
            assert not validate_url(url), f"URL should be invalid: {url}"
    
    def test_extract_domain(self):
        """Test domain extraction from URLs."""
        test_cases = [
            ("https://example.com/path", "example.com"),
            ("http://subdomain.example.com", "subdomain.example.com"),
            ("https://example.com:8080/path", "example.com:8080"),
            ("http://localhost:3000", "localhost:3000")
        ]
        
        for url, expected_domain in test_cases:
            assert extract_domain(url) == expected_domain


class TestDataUtilities:
    """Test data processing utilities."""
    
    def test_batch_process(self):
        """Test batch processing of lists."""
        items = list(range(25))
        batches = batch_process(items, batch_size=10)
        
        assert len(batches) == 3
        assert len(batches[0]) == 10
        assert len(batches[1]) == 10
        assert len(batches[2]) == 5
        
        # Verify all items are included
        flattened = [item for batch in batches for item in batch]
        assert flattened == items
    
    def test_batch_process_empty(self):
        """Test batch processing with empty list."""
        batches = batch_process([], batch_size=10)
        assert batches == []
    
    def test_merge_dicts(self):
        """Test dictionary merging."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"c": 3, "d": 4}
        dict3 = {"b": 5, "e": 6}  # 'b' should be overwritten
        
        result = merge_dicts(dict1, dict2, dict3)
        
        expected = {"a": 1, "b": 5, "c": 3, "d": 4, "e": 6}
        assert result == expected


class TestDecorators:
    """Test decorator utilities."""
    
    def test_rate_limit_decorator(self):
        """Test rate limiting decorator."""
        call_times = []
        
        @rate_limit(calls_per_second=2.0)  # 2 calls per second = 0.5 second interval
        def test_function():
            call_times.append(time.time())
            return "called"
        
        # Make multiple calls
        start_time = time.time()
        test_function()
        test_function()
        test_function()
        end_time = time.time()
        
        # Should take at least 1 second (2 intervals of 0.5 seconds)
        assert end_time - start_time >= 1.0
        assert len(call_times) == 3
    
    def test_retry_decorator_success(self):
        """Test retry decorator with successful function."""
        call_count = [0]
        
        @retry_on_failure(max_retries=3)
        def test_function():
            call_count[0] += 1
            return "success"
        
        result = test_function()
        assert result == "success"
        assert call_count[0] == 1
    
    def test_retry_decorator_failure_then_success(self):
        """Test retry decorator with initial failures then success."""
        call_count = [0]
        
        @retry_on_failure(max_retries=3, delay=0.1)
        def test_function():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        result = test_function()
        assert result == "success"
        assert call_count[0] == 3
    
    def test_retry_decorator_max_retries_exceeded(self):
        """Test retry decorator when max retries are exceeded."""
        call_count = [0]
        
        @retry_on_failure(max_retries=2, delay=0.1)
        def test_function():
            call_count[0] += 1
            raise ValueError("Persistent failure")
        
        with pytest.raises(ValueError, match="Persistent failure"):
            test_function()
        
        assert call_count[0] == 3  # Initial call + 2 retries
