"""
Test Real Services Integration

Tests the integration of real web search, file system, and validation services.
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

from backend.app.services.web_search_service import web_search_service
from backend.app.services.file_system_service import file_system_service
from backend.app.services.validation_service import validation_service


class TestRealFileSystemService:
    """Test real file system service functionality."""
    
    def test_file_system_service_initialization(self):
        """Test file system service initialization."""
        assert file_system_service is not None
        assert hasattr(file_system_service, 'read_file')
        assert hasattr(file_system_service, 'supported_text_extensions')
        assert hasattr(file_system_service, 'supported_binary_extensions')
    
    def test_create_and_read_text_file(self):
        """Test creating and reading a real text file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            test_content = "This is a test file content for testing the file system service."
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            # Read the file using our service
            result = file_system_service.read_file(temp_file_path, 'utf-8')
            
            assert result['status'] == 'success'
            assert result['content'] == test_content
            assert result['content_type'] == 'text'
            assert result['encoding'] == 'utf-8'
            assert 'file_info' in result
            assert 'metrics' in result
            
            # Check file info
            file_info = result['file_info']
            assert file_info['name'] == os.path.basename(temp_file_path)
            assert file_info['size'] == len(test_content)
            
            # Check metrics
            metrics = result['metrics']
            assert metrics['characters'] == len(test_content)
            assert metrics['lines'] == 1
            assert metrics['words'] == len(test_content.split())
            
        finally:
            # Clean up
            os.unlink(temp_file_path)
    
    def test_create_and_read_json_file(self):
        """Test creating and reading a real JSON file."""
        test_data = {
            "name": "Test User",
            "age": 30,
            "skills": ["Python", "FastAPI", "Testing"],
            "metadata": {
                "created": "2024-01-01",
                "version": "1.0.0"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file_path = f.name
        
        try:
            # Read the file using our service
            result = file_system_service.read_file(temp_file_path, 'utf-8')
            
            assert result['status'] == 'success'
            assert result['content'] == test_data
            assert result['content_type'] == 'json'
            assert result['encoding'] == 'utf-8'
            
            # Check JSON metrics
            metrics = result['metrics']
            assert metrics['total_items'] > 0
            assert metrics['has_nested_objects'] == True
            assert 'dict' in metrics['data_types']
            assert 'list' in metrics['data_types']
            
        finally:
            # Clean up
            os.unlink(temp_file_path)
    
    def test_create_and_read_csv_file(self):
        """Test creating and reading a real CSV file."""
        csv_content = """name,age,city
John,25,New York
Jane,30,Los Angeles
Bob,35,Chicago"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file_path = f.name
        
        try:
            # Read the file using our service
            result = file_system_service.read_file(temp_file_path, 'utf-8')
            
            assert result['status'] == 'success'
            assert result['content_type'] == 'csv'
            assert result['encoding'] == 'utf-8'
            assert result['delimiter'] == ','
            
            # Check CSV metrics
            metrics = result['metrics']
            assert metrics['rows'] == 3
            assert metrics['columns'] == 3
            assert 'name' in metrics['column_names']
            assert 'age' in metrics['column_names']
            assert 'city' in metrics['column_names']
            
        finally:
            # Clean up
            os.unlink(temp_file_path)
    
    def test_file_validation_security(self):
        """Test file path validation for security."""
        # Test path traversal attempts
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "//etc/passwd",
            "\\\\windows\\system32\\config\\sam"
        ]
        
        for path in malicious_paths:
            result = file_system_service.read_file(path, 'utf-8')
            assert result['status'] == 'error'
            assert 'Invalid file path' in result['error_message']
    
    def test_file_size_limits(self):
        """Test file size limit enforcement."""
        # Create a file that exceeds reasonable limits
        large_content = "x" * (100 * 1024 * 1024 + 1)  # 100MB + 1 byte
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(large_content)
            temp_file_path = f.name
        
        try:
            # Try to read with a smaller max_size
            result = file_system_service.read_file(temp_file_path, 'utf-8', max_size=1024)
            
            assert result['status'] == 'error'
            assert 'exceeds maximum' in result['error_message']
            
        finally:
            # Clean up
            os.unlink(temp_file_path)


class TestRealWebSearchService:
    """Test real web search service functionality."""
    
    @pytest.mark.asyncio
    async def test_web_search_service_initialization(self):
        """Test web search service initialization."""
        assert web_search_service is not None
        assert hasattr(web_search_service, 'search_google')
        assert hasattr(web_search_service, 'search_arxiv')
        assert hasattr(web_search_service, 'fetch_web_content')
    
    @pytest.mark.asyncio
    async def test_mock_google_search_rmay_atawia(self):
        """Test mock Google search for 'rmay atawia'."""
        async with web_search_service:
            results = await web_search_service.search_google(
                "rmay atawia research publications",
                max_results=5,
                include_abstracts=True
            )
            
            assert len(results) > 0
            assert len(results) <= 5
            
            # Check first result structure
            first_result = results[0]
            assert 'title' in first_result
            assert 'url' in first_result
            assert 'snippet' in first_result
            assert 'source' in first_result
            assert 'relevance' in first_result
            assert 'abstract' in first_result
            
            # Check content relevance
            title_lower = first_result['title'].lower()
            snippet_lower = first_result['snippet'].lower()
            assert 'rmay' in title_lower or 'atawia' in title_lower or 'rmay' in snippet_lower or 'atawia' in snippet_lower
    
    @pytest.mark.asyncio
    async def test_mock_google_search_machine_learning(self):
        """Test mock Google search for 'machine learning'."""
        async with web_search_service:
            results = await web_search_service.search_google(
                "machine learning algorithms 2024",
                max_results=3,
                include_abstracts=False
            )
            
            assert len(results) > 0
            assert len(results) <= 3
            
            # Check that abstracts are not included
            for result in results:
                assert 'abstract' not in result
    
    @pytest.mark.asyncio
    async def test_arxiv_search(self):
        """Test arXiv search functionality."""
        async with web_search_service:
            results = await web_search_service.search_arxiv(
                "machine learning",
                max_results=3
            )
            
            # Note: This might fail if arXiv is not accessible
            # In that case, we expect an empty result or error
            if results:
                assert len(results) <= 3
                for result in results:
                    assert 'title' in result
                    assert 'url' in result
                    assert 'source' == 'arXiv'
    
    @pytest.mark.asyncio
    async def test_academic_databases_search(self):
        """Test multi-database academic search."""
        async with web_search_service:
            results = await web_search_service.search_academic_databases(
                "artificial intelligence",
                max_results=6,
                databases=["arxiv", "ieee", "acm"]
            )
            
            # Should get results from multiple databases
            assert len(results) > 0
            assert len(results) <= 6
            
            # Check sources
            sources = [result['source'] for result in results]
            assert any('arXiv' in source for source in sources)
            assert any('IEEE' in source for source in sources)
            assert any('ACM' in source for source in sources)


class TestRealValidationService:
    """Test real validation service functionality."""
    
    def test_validation_service_initialization(self):
        """Test validation service initialization."""
        assert validation_service is not None
        assert hasattr(validation_service, 'validate_file_reader_params')
        assert hasattr(validation_service, 'validate_web_content_fetcher_params')
        assert hasattr(validation_service, 'validate_text_processor_params')
    
    def test_file_reader_parameter_validation(self):
        """Test file reader parameter validation."""
        # Valid parameters
        valid_params = {
            'path': 'test.txt',
            'encoding': 'utf-8',
            'max_size': 1024
        }
        
        is_valid, error_message, sanitized_params = validation_service.validate_file_reader_params(valid_params)
        assert is_valid == True
        assert error_message is None
        assert sanitized_params['path'] == 'test.txt'
        assert sanitized_params['encoding'] == 'utf-8'
        assert sanitized_params['max_size'] == 1024
        
        # Invalid parameters - missing path
        invalid_params = {
            'encoding': 'utf-8',
            'max_size': 1024
        }
        
        is_valid, error_message, sanitized_params = validation_service.validate_file_reader_params(invalid_params)
        assert is_valid == False
        assert 'Missing required parameter: path' in error_message
        
        # Invalid parameters - invalid encoding
        invalid_params = {
            'path': 'test.txt',
            'encoding': 'invalid_encoding',
            'max_size': 1024
        }
        
        is_valid, error_message, sanitized_params = validation_service.validate_file_reader_params(invalid_params)
        assert is_valid == False
        assert 'Unsupported encoding' in error_message
    
    def test_web_content_fetcher_parameter_validation(self):
        """Test web content fetcher parameter validation."""
        # Valid search query parameters
        valid_search_params = {
            'query': 'test search',
            'max_results': 10,
            'search_engine': 'google',
            'include_abstracts': True
        }
        
        is_valid, error_message, sanitized_params = validation_service.validate_web_content_fetcher_params(valid_search_params)
        assert is_valid == True
        assert error_message is None
        assert sanitized_params['query'] == 'test search'
        assert sanitized_params['max_results'] == 10
        assert sanitized_params['search_engine'] == 'google'
        
        # Valid URL parameters
        valid_url_params = {
            'url': 'https://example.com',
            'extract_text': True,
            'max_content_length': 50000
        }
        
        is_valid, error_message, sanitized_params = validation_service.validate_web_content_fetcher_params(valid_url_params)
        assert is_valid == True
        assert error_message is None
        assert sanitized_params['url'] == 'https://example.com'
        
        # Invalid parameters - missing both query and URL
        invalid_params = {
            'max_results': 10
        }
        
        is_valid, error_message, sanitized_params = validation_service.validate_web_content_fetcher_params(invalid_params)
        assert is_valid == False
        assert 'Missing required parameter: either' in error_message
    
    def test_text_processor_parameter_validation(self):
        """Test text processor parameter validation."""
        # Valid parameters
        valid_params = {
            'text': 'This is a test text for processing.',
            'operation': 'summarize',
            'target_language': 'Spanish',
            'max_keywords': 15
        }
        
        is_valid, error_message, sanitized_params = validation_service.validate_text_processor_params(valid_params)
        assert is_valid == True
        assert error_message is None
        assert sanitized_params['text'] == 'This is a test text for processing.'
        assert sanitized_params['operation'] == 'summarize'
        
        # Invalid parameters - unsupported operation
        invalid_params = {
            'text': 'Test text',
            'operation': 'invalid_operation'
        }
        
        is_valid, error_message, sanitized_params = validation_service.validate_text_processor_params(invalid_params)
        assert is_valid == False
        assert 'Unsupported operation' in error_message
    
    def test_validation_error_creation(self):
        """Test validation error response creation."""
        error_response = validation_service.create_validation_error('test_field', 'Test error message')
        
        assert error_response['status'] == 'error'
        assert error_response['error_type'] == 'validation_error'
        assert error_response['field'] == 'test_field'
        assert error_response['message'] == 'Test error message'
        assert 'timestamp' in error_response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
