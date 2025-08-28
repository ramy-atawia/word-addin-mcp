"""
Comprehensive Parameter Validation Service

Provides strict input validation and sanitization for all MCP tools.
Ensures data integrity, security, and consistent error handling.
"""

import re
import json
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path
import logging
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class ValidationService:
    """Comprehensive parameter validation service."""
    
    def __init__(self):
        # File path validation patterns
        self.safe_path_pattern = re.compile(r'^[a-zA-Z0-9._\-/\\]+$')
        self.path_traversal_pattern = re.compile(r'\.\.|//|\\\\')
        
        # URL validation patterns
        self.url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        # Text content validation
        self.max_text_length = 10 * 1024 * 1024  # 10MB
        self.max_query_length = 1000
        self.max_url_length = 2048
        
        # File size limits
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        
        # Supported encodings
        self.supported_encodings = {
            'utf-8', 'utf-8-sig', 'ascii', 'iso-8859-1', 'cp1252',
            'latin-1', 'utf-16', 'utf-16le', 'utf-16be'
        }
        
        # Supported search engines
        self.supported_search_engines = {
            'google', 'bing', 'duckduckgo', 'arxiv', 'ieee', 'acm'
        }
        
        # Supported operations for text processing (including draft)
        self.supported_text_operations = {
            'summarize', 'translate', 'extract_keywords', 'sentiment_analysis',
            'extract_entities', 'language_detection', 'text_classification', 'draft'
        }
        
        # Supported analysis types for documents
        self.supported_analysis_types = {
            'readability', 'structure', 'keyword_extraction', 'summary',
            'comprehensive', 'sentiment', 'topic_modeling'
        }
        
        # Supported data formats
        self.supported_data_formats = {
            'json', 'csv', 'xml', 'yaml', 'summary', 'detailed_report',
            'executive_summary', 'research_report', 'table', 'markdown'
        }
    
    def validate_file_reader_params(self, params: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate file reader tool parameters.
        
        Returns:
            Tuple of (is_valid, error_message, sanitized_params)
        """
        try:
            # Required parameters
            if 'path' not in params:
                return False, "Missing required parameter: path", {}
            
            path = params.get('path', '')
            encoding = params.get('encoding', 'utf-8')
            max_size = params.get('max_size', self.max_file_size)
            
            # Validate path
            path_valid, path_error = self._validate_file_path(path)
            if not path_valid:
                return False, path_error, {}
            
            # Validate encoding
            encoding_valid, encoding_error = self._validate_encoding(encoding)
            if not encoding_valid:
                return False, encoding_error, {}
            
            # Validate max_size
            max_size_valid, max_size_error = self._validate_file_size(max_size)
            if not max_size_valid:
                return False, max_size_error, {}
            
            # Sanitize and return
            sanitized_params = {
                'path': path.strip(),
                'encoding': encoding.lower(),
                'max_size': int(max_size)
            }
            
            return True, None, sanitized_params
            
        except Exception as e:
            logger.error(f"File reader validation error: {str(e)}")
            return False, f"Validation error: {str(e)}", {}
    
    def validate_text_processor_params(self, params: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate text processor tool parameters.
        
        Returns:
            Tuple of (is_valid, error_message, sanitized_params)
        """
        try:
            # Required parameters
            if 'text' not in params:
                return False, "Missing required parameter: text", {}
            if 'operation' not in params:
                return False, "Missing required parameter: operation", {}
            
            text = params.get('text', '')
            operation = params.get('operation', '')
            target_language = params.get('target_language', 'English')
            max_keywords = params.get('max_keywords', 10)
            
            # Validate text
            text_valid, text_error = self._validate_text_content(text)
            if not text_valid:
                return False, text_error, {}
            
            # Validate operation
            operation_valid, operation_error = self._validate_text_operation(operation)
            if not operation_valid:
                return False, operation_error, {}
            
            # Validate target language
            language_valid, language_error = self._validate_language(target_language)
            if not language_valid:
                return False, language_error, {}
            
            # Validate max_keywords
            keywords_valid, keywords_error = self._validate_keyword_count(max_keywords)
            if not keywords_valid:
                return False, keywords_error, {}
            
            # Sanitize and return
            sanitized_params = {
                'text': text.strip(),
                'operation': operation.lower(),
                'target_language': target_language.strip(),
                'max_keywords': int(max_keywords)
            }
            
            return True, None, sanitized_params
            
        except Exception as e:
            logger.error(f"Text processor validation error: {str(e)}")
            return False, f"Validation error: {str(e)}", {}
    
    def validate_document_analyzer_params(self, params: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate document analyzer tool parameters.
        
        Returns:
            Tuple of (is_valid, error_message, sanitized_params)
        """
        try:
            # Required parameters
            if 'content' not in params:
                return False, "Missing required parameter: content", {}
            if 'analysis_type' not in params:
                return False, "Missing required parameter: analysis_type", {}
            
            content = params.get('content', '')
            analysis_type = params.get('analysis_type', '')
            max_keywords = params.get('max_keywords', 20)
            max_length = params.get('max_length', 150)
            
            # Validate content
            content_valid, content_error = self._validate_text_content(content)
            if not content_valid:
                return False, content_error, {}
            
            # Validate analysis type
            analysis_valid, analysis_error = self._validate_analysis_type(analysis_type)
            if not analysis_valid:
                return False, analysis_error, {}
            
            # Validate max_keywords
            keywords_valid, keywords_error = self._validate_keyword_count(max_keywords)
            if not keywords_valid:
                return False, keywords_error, {}
            
            # Validate max_length
            length_valid, length_error = self._validate_summary_length(max_length)
            if not length_valid:
                return False, length_error, {}
            
            # Sanitize and return
            sanitized_params = {
                'content': content.strip(),
                'analysis_type': analysis_type.lower(),
                'max_keywords': int(max_keywords),
                'max_length': int(max_length)
            }
            
            return True, None, sanitized_params
            
        except Exception as e:
            logger.error(f"Document analyzer validation error: {str(e)}")
            return False, f"Validation error: {str(e)}", {}
    
    def validate_web_content_fetcher_params(self, params: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate web content fetcher tool parameters.
        
        Returns:
            Tuple of (is_valid, error_message, sanitized_params)
        """
        try:
            # Check if it's a search query or URL fetch
            if 'query' in params:
                # Search query validation
                query = params.get('query', '')
                extract_type = params.get('extract_type', 'summary')
                max_length = params.get('max_length', 500)
                
                # Validate query
                query_valid, query_error = self._validate_search_query(query)
                if not query_valid:
                    return False, query_error, {}
                
                # Validate extract_type
                if extract_type not in ['text', 'summary', 'key_points', 'full_content']:
                    return False, f"Invalid extract_type: {extract_type}. Must be one of: text, summary, key_points, full_content", {}
                
                # Validate max_length
                if not isinstance(max_length, (int, float)) or max_length < 10 or max_length > 10000:
                    return False, "max_length must be a number between 10 and 10000", {}
                
                # Sanitize and return
                sanitized_params = {
                    'query': query.strip(),
                    'extract_type': extract_type,
                    'max_length': int(max_length)
                }
                
                return True, None, sanitized_params
                
            elif 'url' in params:
                # URL fetch validation
                url = params.get('url', '')
                extract_type = params.get('extract_type', 'summary')
                max_length = params.get('max_length', 500)
                
                # Validate URL
                url_valid, url_error = self._validate_url(url)
                if not url_valid:
                    return False, url_error, {}
                
                # Validate extract_type
                if extract_type not in ['text', 'summary', 'key_points', 'full_content']:
                    return False, f"Invalid extract_type: {extract_type}. Must be one of: text, summary, key_points, full_content", {}
                
                # Validate max_length
                if not isinstance(max_length, (int, float)) or max_length < 10 or max_length > 10000:
                    return False, "max_length must be a number between 10 and 10000", {}
                
                # Sanitize and return
                sanitized_params = {
                    'url': url.strip(),
                    'extract_type': extract_type,
                    'max_length': int(max_length)
                }
                
                return True, None, sanitized_params
            else:
                return False, "Missing required parameter: either 'query' or 'url' must be provided", {}
                
        except Exception as e:
            logger.error(f"Web content fetcher validation error: {str(e)}")
            return False, f"Validation error: {str(e)}", {}
    
    def validate_data_formatter_params(self, params: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate data formatter tool parameters.
        
        Returns:
            Tuple of (is_valid, error_message, sanitized_params)
        """
        try:
            # Required parameters
            if 'data' not in params:
                return False, "Missing required parameter: data", {}
            
            data = params.get('data')
            output_format = params.get('output_format', params.get('format', 'json'))  # Support both old and new names
            data_type = params.get('data_type', 'auto')
            indent = params.get('indent', 2)
            include_metadata = params.get('include_metadata', True)
            
            # Validate data
            data_valid, data_error = self._validate_data_content(data)
            if not data_valid:
                return False, data_error, {}
            
            # Validate output format
            format_valid, format_error = self._validate_data_format(output_format)
            if not format_valid:
                return False, format_error, {}
            
            # Validate indent
            if not isinstance(indent, int) or indent not in [2, 4]:
                indent = 2  # Default to 2 if invalid
            
            # Validate include_metadata
            if not isinstance(include_metadata, bool):
                include_metadata = True  # Default to True if invalid
            
            # Sanitize and return
            sanitized_params = {
                'data': data,
                'output_format': output_format.lower(),
                'data_type': data_type.lower(),
                'indent': indent,
                'include_metadata': include_metadata
            }
            
            return True, None, sanitized_params
            
        except Exception as e:
            logger.error(f"Data formatter validation error: {str(e)}")
            return False, f"Validation error: {str(e)}", {}
    
    def _validate_file_path(self, path: str) -> Tuple[bool, Optional[str]]:
        """Validate file path for security and correctness."""
        if not path or not isinstance(path, str):
            return False, "Path must be a non-empty string"
        
        if len(path) > 500:
            return False, "Path too long (max 500 characters)"
        
        # Check for path traversal attempts
        if self.path_traversal_pattern.search(path):
            return False, "Path contains invalid traversal characters"
        
        # Check for absolute paths (security risk)
        if Path(path).is_absolute():
            return False, "Absolute paths are not allowed"
        
        return True, None
    
    def _validate_encoding(self, encoding: str) -> Tuple[bool, Optional[str]]:
        """Validate text encoding."""
        if not encoding or not isinstance(encoding, str):
            return False, "Encoding must be a non-empty string"
        
        if encoding.lower() not in self.supported_encodings:
            return False, f"Unsupported encoding: {encoding}. Supported: {', '.join(self.supported_encodings)}"
        
        return True, None
    
    def _validate_file_size(self, size: Any) -> Tuple[bool, Optional[str]]:
        """Validate file size parameter."""
        try:
            size_int = int(size)
            if size_int <= 0:
                return False, "File size must be positive"
            if size_int > self.max_file_size:
                return False, f"File size exceeds maximum allowed: {self.max_file_size}"
            return True, None
        except (ValueError, TypeError):
            return False, "File size must be a valid integer"
    
    def _validate_text_content(self, text: str) -> Tuple[bool, Optional[str]]:
        """Validate text content."""
        if not text or not isinstance(text, str):
            return False, "Text content must be a non-empty string"
        
        if len(text) > self.max_text_length:
            return False, f"Text content too long (max {self.max_text_length} characters)"
        
        return True, None
    
    def _validate_text_operation(self, operation: str) -> Tuple[bool, Optional[str]]:
        """Validate text processing operation."""
        if not operation or not isinstance(operation, str):
            return False, "Operation must be a non-empty string"
        
        if operation.lower() not in self.supported_text_operations:
            return False, f"Unsupported operation: {operation}. Supported: {', '.join(self.supported_text_operations)}"
        
        return True, None
    
    def _validate_language(self, language: str) -> Tuple[bool, Optional[str]]:
        """Validate target language."""
        if not language or not isinstance(language, str):
            return False, "Language must be a non-empty string"
        
        if len(language) > 100:
            return False, "Language name too long (max 100 characters)"
        
        return True, None
    
    def _validate_keyword_count(self, count: Any) -> Tuple[bool, Optional[str]]:
        """Validate keyword count parameter."""
        try:
            count_int = int(count)
            if count_int <= 0:
                return False, "Keyword count must be positive"
            if count_int > 100:
                return False, "Keyword count too high (max 100)"
            return True, None
        except (ValueError, TypeError):
            return False, "Keyword count must be a valid integer"
    
    def _validate_analysis_type(self, analysis_type: str) -> Tuple[bool, Optional[str]]:
        """Validate document analysis type."""
        if not analysis_type or not isinstance(analysis_type, str):
            return False, "Analysis type must be a non-empty string"
        
        if analysis_type.lower() not in self.supported_analysis_types:
            return False, f"Unsupported analysis type: {analysis_type}. Supported: {', '.join(self.supported_analysis_types)}"
        
        return True, None
    
    def _validate_summary_length(self, length: Any) -> Tuple[bool, Optional[str]]:
        """Validate summary length parameter."""
        try:
            length_int = int(length)
            if length_int <= 0:
                return False, "Summary length must be positive"
            if length_int > 10000:
                return False, "Summary length too high (max 10000 characters)"
            return True, None
        except (ValueError, TypeError):
            return False, "Summary length must be a valid integer"
    
    def _validate_search_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """Validate search query."""
        if not query or not isinstance(query, str):
            return False, "Search query must be a non-empty string"
        
        if len(query) > self.max_query_length:
            return False, f"Search query too long (max {self.max_query_length} characters)"
        
        return True, None
    
    def _validate_result_count(self, count: Any) -> Tuple[bool, Optional[str]]:
        """Validate result count parameter."""
        try:
            count_int = int(count)
            if count_int <= 0:
                return False, "Result count must be positive"
            if count_int > 100:
                return False, "Result count too high (max 100)"
            return True, None
        except (ValueError, TypeError):
            return False, "Result count must be a valid integer"
    
    def _validate_search_engine(self, engine: str) -> Tuple[bool, Optional[str]]:
        """Validate search engine parameter."""
        if not engine or not isinstance(engine, str):
            return False, "Search engine must be a non-empty string"
        
        if engine.lower() not in self.supported_search_engines:
            return False, f"Unsupported search engine: {engine}. Supported: {', '.join(self.supported_search_engines)}"
        
        return True, None
    
    def _validate_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """Validate URL parameter."""
        if not url or not isinstance(url, str):
            return False, "URL must be a non-empty string"
        
        if len(url) > self.max_url_length:
            return False, f"URL too long (max {self.max_url_length} characters)"
        
        if not self.url_pattern.match(url):
            return False, "Invalid URL format"
        
        return True, None
    
    def _validate_content_length(self, length: Any) -> Tuple[bool, Optional[str]]:
        """Validate content length parameter."""
        try:
            length_int = int(length)
            if length_int <= 0:
                return False, "Content length must be positive"
            if length_int > 1000000:  # 1MB
                return False, "Content length too high (max 1MB)"
            return True, None
        except (ValueError, TypeError):
            return False, "Content length must be a valid integer"
    
    def _validate_data_content(self, data: Any) -> Tuple[bool, Optional[str]]:
        """Validate data content."""
        if data is None:
            return False, "Data cannot be null"
        
        # Check if data is serializable
        try:
            json.dumps(data)
            return True, None
        except (TypeError, ValueError):
            return False, "Data must be JSON serializable"
    
    def _validate_data_format(self, format_type: str) -> Tuple[bool, Optional[str]]:
        """Validate data format parameter."""
        if not format_type or not isinstance(format_type, str):
            return False, "Data format must be a non-empty string"
        
        if format_type.lower() not in self.supported_data_formats:
            return False, f"Unsupported data format: {format_type}. Supported: {', '.join(self.supported_data_formats)}"
        
        return True, None
    
    def _validate_group_by(self, group_by: str, data: Any) -> Tuple[bool, Optional[str]]:
        """Validate group_by parameter against data structure."""
        if not group_by or not isinstance(group_by, str):
            return False, "Group by must be a non-empty string"
        
        # Check if group_by field exists in data
        if isinstance(data, list) and data:
            if not all(isinstance(item, dict) for item in data):
                return False, "Data must be a list of dictionaries for grouping"
            
            if group_by not in data[0]:
                return False, f"Group by field '{group_by}' not found in data"
        
        return True, None
    
    def sanitize_string(self, value: str) -> str:
        """Sanitize string input."""
        if not isinstance(value, str):
            return str(value)
        
        # Remove control characters
        value = ''.join(char for char in value if ord(char) >= 32)
        
        # Trim whitespace
        value = value.strip()
        
        return value
    
    def sanitize_number(self, value: Any, min_val: Optional[float] = None, 
                       max_val: Optional[float] = None) -> float:
        """Sanitize numeric input."""
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                num = min_val
            if max_val is not None and num > max_val:
                num = max_val
            return num
        except (ValueError, TypeError):
            return 0.0
    
    def create_validation_error(self, field: str, message: str) -> Dict[str, Any]:
        """Create standardized validation error response."""
        return {
            'status': 'error',
            'error_type': 'validation_error',
            'field': field,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }


# Global instance for easy access
validation_service = ValidationService()