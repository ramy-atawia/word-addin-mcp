"""
Real File System Service

Provides actual file reading capabilities with proper error handling,
file type detection, and content processing.
"""

import os
import json
import csv
import io
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import logging
import mimetypes
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)


class FileSystemService:
    """Real file system service with comprehensive file handling."""
    
    def __init__(self):
        self.supported_text_extensions = {
            '.txt', '.md', '.rst', '.tex', '.log', '.ini', '.cfg', '.conf',
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp',
            '.html', '.htm', '.xml', '.json', '.csv', '.tsv', '.sql'
        }
        
        self.supported_binary_extensions = {
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.tar', '.gz', '.rar', '.7z', '.exe', '.dll', '.so',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg'
        }
        
        # Maximum file sizes for different operations
        self.max_file_sizes = {
            'text': 10 * 1024 * 1024,  # 10MB for text files
            'binary': 100 * 1024 * 1024,  # 100MB for binary files
            'image': 50 * 1024 * 1024,  # 50MB for images
        }
    
    def read_file(self, file_path: str, encoding: str = 'utf-8', 
                  max_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Read a file with comprehensive error handling and content processing.
        
        Args:
            file_path: Path to the file to read
            encoding: Text encoding for text files
            max_size: Maximum file size in bytes
            
        Returns:
            Dictionary containing file content and metadata
        """
        try:
            # Validate file path
            if not self._is_valid_file_path(file_path):
                return self._create_error_result("Invalid file path")
            
            # Check if file exists
            if not os.path.exists(file_path):
                return self._create_error_result("File not found")
            
            # Check if it's a file (not directory)
            if not os.path.isfile(file_path):
                return self._create_error_result("Path is not a file")
            
            # Get file info
            file_info = self._get_file_info(file_path)
            
            # Check file size
            if max_size and file_info['size'] > max_size:
                return self._create_error_result(f"File size {file_info['size']} exceeds maximum {max_size}")
            
            # Determine file type and read accordingly
            file_type = self._detect_file_type(file_path)
            
            if file_type == 'text':
                return self._read_text_file(file_path, encoding, file_info)
            elif file_type == 'json':
                return self._read_json_file(file_path, encoding, file_info)
            elif file_type == 'csv':
                return self._read_csv_file(file_path, encoding, file_info)
            elif file_type == 'binary':
                return self._read_binary_file(file_path, file_info)
            else:
                return self._create_error_result(f"Unsupported file type: {file_type}")
                
        except PermissionError:
            return self._create_error_result("Permission denied")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return self._create_error_result(f"Read error: {str(e)}")
    
    def _is_valid_file_path(self, file_path: str) -> bool:
        """Validate file path for security and correctness."""
        if not file_path or not isinstance(file_path, str):
            return False
        
        # Check for path traversal attempts
        if '..' in file_path:
            return False
        
        # For testing purposes, allow absolute paths in development
        # In production, you might want to restrict this
        # if file_path.startswith('/'):
        #     return False
        
        # Check for reasonable length
        if len(file_path) > 500:
            return False
        
        return True
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive file information."""
        stat = os.stat(file_path)
        
        return {
            'name': os.path.basename(file_path),
            'path': file_path,
            'size': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'permissions': oct(stat.st_mode)[-3:],
            'owner': stat.st_uid,
            'group': stat.st_gid
        }
    
    def _detect_file_type(self, file_path: str) -> str:
        """Detect file type based on extension and content."""
        ext = Path(file_path).suffix.lower()
        
        if ext in {'.json'}:
            return 'json'
        elif ext in {'.csv', '.tsv'}:
            return 'csv'
        elif ext in self.supported_text_extensions:
            return 'text'
        elif ext in self.supported_binary_extensions:
            return 'binary'
        else:
            # Try to detect by content
            return self._detect_by_content(file_path)
    
    def _detect_by_content(self, file_path: str) -> str:
        """Detect file type by examining file content."""
        try:
            with open(file_path, 'rb') as f:
                # Read first 1024 bytes to detect content
                header = f.read(1024)
                
                # Check for common file signatures
                if header.startswith(b'%PDF'):
                    return 'binary'  # PDF
                elif header.startswith(b'PK'):
                    return 'binary'  # ZIP
                elif header.startswith(b'\x89PNG'):
                    return 'binary'  # PNG
                elif header.startswith(b'\xff\xd8\xff'):
                    return 'binary'  # JPEG
                elif header.startswith(b'{') or header.startswith(b'['):
                    return 'json'
                else:
                    # Try to decode as text
                    try:
                        header.decode('utf-8')
                        return 'text'
                    except UnicodeDecodeError:
                        return 'binary'
        except Exception:
            return 'binary'  # Default to binary if detection fails
    
    def _read_text_file(self, file_path: str, encoding: str, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Read and process text file content."""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # Calculate content metrics
            content_metrics = self._analyze_text_content(content)
            
            return {
                'status': 'success',
                'file_info': file_info,
                'content': content,
                'content_type': 'text',
                'encoding': encoding,
                'metrics': content_metrics,
                'read_time': datetime.now().isoformat()
            }
            
        except UnicodeDecodeError:
            # Try alternative encodings
            return self._try_alternative_encodings(file_path, file_info)
    
    def _read_json_file(self, file_path: str, encoding: str, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Read and validate JSON file content."""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # Parse JSON to validate
            json_data = json.loads(content)
            
            # Analyze JSON structure
            json_metrics = self._analyze_json_content(json_data)
            
            return {
                'status': 'success',
                'file_info': file_info,
                'content': json_data,
                'content_type': 'json',
                'encoding': encoding,
                'metrics': json_metrics,
                'read_time': datetime.now().isoformat()
            }
            
        except json.JSONDecodeError as e:
            return self._create_error_result(f"Invalid JSON: {str(e)}")
        except Exception as e:
            return self._create_error_result(f"JSON read error: {str(e)}")
    
    def _read_csv_file(self, file_path: str, encoding: str, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Read and parse CSV file content."""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                # Try to detect delimiter
                sample = f.read(1024)
                f.seek(0)
                
                # Detect delimiter
                delimiter = self._detect_csv_delimiter(sample)
                
                # Read CSV
                reader = csv.DictReader(f, delimiter=delimiter)
                rows = list(reader)
                
                # Analyze CSV structure
                csv_metrics = self._analyze_csv_content(rows)
                
                return {
                    'status': 'success',
                    'file_info': file_info,
                    'content': rows,
                    'content_type': 'csv',
                    'encoding': encoding,
                    'delimiter': delimiter,
                    'metrics': csv_metrics,
                    'read_time': datetime.now().isoformat()
                }
                
        except Exception as e:
            return self._create_error_result(f"CSV read error: {str(e)}")
    
    def _read_binary_file(self, file_path: str, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Read binary file with metadata only."""
        try:
            # For binary files, we don't read the content but provide metadata
            # In production, you might want to extract text from PDFs, etc.
            
            return {
                'status': 'success',
                'file_info': file_info,
                'content': f"Binary file: {file_info['name']} ({file_info['size']} bytes)",
                'content_type': 'binary',
                'metrics': {
                    'file_size': file_info['size'],
                    'is_binary': True,
                    'can_extract_text': self._can_extract_text_from_binary(file_path)
                },
                'read_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            return self._create_error_result(f"Binary file read error: {str(e)}")
    
    def _try_alternative_encodings(self, file_path: str, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Try alternative encodings if the primary encoding fails."""
        encodings = ['utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                
                content_metrics = self._analyze_text_content(content)
                
                return {
                    'status': 'success',
                    'file_info': file_info,
                    'content': content,
                    'content_type': 'text',
                    'encoding': encoding,
                    'metrics': content_metrics,
                    'read_time': datetime.now().isoformat(),
                    'note': f'Used alternative encoding: {encoding}'
                }
                
            except UnicodeDecodeError:
                continue
        
        return self._create_error_result("Unable to decode file with any supported encoding")
    
    def _detect_csv_delimiter(self, sample: str) -> str:
        """Detect CSV delimiter from sample content."""
        delimiters = [',', ';', '\t', '|']
        max_fields = 0
        best_delimiter = ','
        
        for delimiter in delimiters:
            fields = sample.split(delimiter)
            if len(fields) > max_fields:
                max_fields = len(fields)
                best_delimiter = delimiter
        
        return best_delimiter
    
    def _analyze_text_content(self, content: str) -> Dict[str, Any]:
        """Analyze text content and provide metrics."""
        lines = content.splitlines()
        words = content.split()
        
        return {
            'characters': len(content),
            'lines': len(lines),
            'words': len(words),
            'paragraphs': len([l for l in lines if l.strip()]),
            'avg_line_length': sum(len(line) for line in lines) / max(len(lines), 1),
            'avg_word_length': sum(len(word) for word in words) / max(len(words), 1),
            'has_unicode': any(ord(char) > 127 for char in content),
            'encoding_confidence': 'high' if content.isprintable() else 'low'
        }
    
    def _analyze_json_content(self, json_data: Any) -> Dict[str, Any]:
        """Analyze JSON content structure."""
        def count_items(obj):
            if isinstance(obj, dict):
                return 1 + sum(count_items(v) for v in obj.values())
            elif isinstance(obj, list):
                return 1 + sum(count_items(item) for item in obj)
            else:
                return 1
        
        return {
            'total_items': count_items(json_data),
            'depth': self._get_json_depth(json_data),
            'has_nested_objects': self._has_nested_objects(json_data),
            'data_types': self._get_json_data_types(json_data)
        }
    
    def _analyze_csv_content(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze CSV content structure."""
        if not rows:
            return {'rows': 0, 'columns': 0}
        
        columns = list(rows[0].keys()) if rows else []
        
        return {
            'rows': len(rows),
            'columns': len(columns),
            'column_names': columns,
            'sample_data': rows[:3] if rows else []
        }
    
    def _get_json_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Calculate maximum depth of JSON structure."""
        if isinstance(obj, dict):
            return max(self._get_json_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            return max(self._get_json_depth(item, current_depth + 1) for item in obj)
        else:
            return current_depth
    
    def _has_nested_objects(self, obj: Any) -> bool:
        """Check if JSON has nested objects."""
        if isinstance(obj, dict):
            return any(isinstance(v, (dict, list)) for v in obj.values())
        elif isinstance(obj, list):
            return any(isinstance(item, (dict, list)) for item in obj)
        return False
    
    def _get_json_data_types(self, obj: Any) -> Dict[str, int]:
        """Get count of different data types in JSON."""
        type_counts = {}
        
        def count_types(item):
            item_type = type(item).__name__
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
            
            if isinstance(item, dict):
                for v in item.values():
                    count_types(v)
            elif isinstance(item, list):
                for item in item:
                    count_types(item)
        
        count_types(obj)
        return type_counts
    
    def _can_extract_text_from_binary(self, file_path: str) -> bool:
        """Check if text can be extracted from binary file."""
        ext = Path(file_path).suffix.lower()
        return ext in {'.pdf', '.doc', '.docx', '.txt', '.rtf'}
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error result."""
        return {
            'status': 'error',
            'error_message': error_message,
            'read_time': datetime.now().isoformat()
        }


# Global instance for easy access
file_system_service = FileSystemService()
