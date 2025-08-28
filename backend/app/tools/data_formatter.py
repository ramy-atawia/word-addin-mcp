"""
Enhanced Data Formatter Tool for Word Add-in MCP Project.

This tool implements the MCP tool interface for data formatting with real data processing.
"""

import json
import csv
import re
from typing import Dict, Any, List, Union
from io import StringIO
import structlog

from backend.app.core.mcp_tool_interface import (
    BaseMCPTool,
    ToolMetadata,
    ToolExecutionContext,
    ToolExecutionResult,
    ToolExecutionStatus,
    ToolErrorCode
)

logger = structlog.get_logger()


class DataFormatterTool(BaseMCPTool):
    """MCP tool for data formatting."""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="data_formatter",
            description="Format data into various output formats",
            version="1.0.0",
            author="Word Add-in MCP Project",
            tags=["data", "formatting", "conversion"],
            category="data_processing",
            input_schema={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "Data to format (text, JSON, CSV, or structured data)"},
                    "output_format": {"type": "string", "enum": ["json", "csv", "xml", "yaml", "table", "markdown"], "default": "json"},
                    "data_type": {"type": "string", "enum": ["text", "json", "csv", "list", "auto"], "default": "auto", "description": "Input data type for better parsing"},
                    "indent": {"type": "integer", "description": "JSON indentation (2 or 4 spaces)", "default": 2},
                    "include_metadata": {"type": "boolean", "description": "Include formatting metadata", "default": true}
                },
                "required": ["data"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "output_format": {"type": "string"},
                    "formatted_data": {"type": "string"},
                    "input_length": {"type": "integer"},
                    "output_length": {"type": "integer"}
                }
            }
        )
        super().__init__(metadata)
    
    async def execute(self, context: ToolExecutionContext) -> ToolExecutionResult:
        """Execute enhanced data formatting."""
        try:
            data = context.parameters.get("data", "")
            output_format = context.parameters.get("output_format", "json")
            data_type = context.parameters.get("data_type", "auto")
            indent = context.parameters.get("indent", 2)
            include_metadata = context.parameters.get("include_metadata", True)
            
            if not data:
                return ToolExecutionResult(
                    status=ToolExecutionStatus.FAILED,
                    error_code=ToolErrorCode.INVALID_PARAMETERS,
                    error_message="Data input is required"
                )
            
            # Auto-detect data type if not specified
            if data_type == "auto":
                data_type = self._detect_data_type(data)
            
            # Parse data based on detected type
            parsed_data = self._parse_data(data, data_type)
            
            # Format data based on output format
            if output_format == "json":
                formatted_data = self._format_as_json(parsed_data, indent, include_metadata)
            elif output_format == "csv":
                formatted_data = self._format_as_csv(parsed_data, include_metadata)
            elif output_format == "xml":
                formatted_data = self._format_as_xml(parsed_data, include_metadata)
            elif output_format == "yaml":
                formatted_data = self._format_as_yaml(parsed_data, include_metadata)
            elif output_format == "table":
                formatted_data = self._format_as_table(parsed_data, include_metadata)
            elif output_format == "markdown":
                formatted_data = self._format_as_markdown(parsed_data, include_metadata)
            else:
                return ToolExecutionResult(
                    status=ToolExecutionStatus.FAILED,
                    error_code=ToolErrorCode.INVALID_PARAMETERS,
                    error_message=f"Unknown output format: {output_format}"
                )
            
            return ToolExecutionResult(
                status=ToolExecutionStatus.SUCCESS,
                data={
                    "output_format": output_format,
                    "formatted_data": formatted_data,
                    "input_length": len(data),
                    "output_length": len(formatted_data),
                    "data_type": data_type,
                    "parsing_success": parsed_data is not None
                }
            )
            
        except Exception as e:
            logger.error(f"Data formatting failed: {str(e)}")
            return ToolExecutionResult(
                status=ToolExecutionStatus.FAILED,
                error_code=ToolErrorCode.EXECUTION_FAILED,
                error_message=str(e)
            )
    
    def _detect_data_type(self, data: str) -> str:
        """Auto-detect the type of input data."""
        data = data.strip()
        
        # Check if it's JSON
        if data.startswith('{') and data.endswith('}') or data.startswith('[') and data.endswith(']'):
            try:
                json.loads(data)
                return "json"
            except:
                pass
        
        # Check if it's CSV-like
        if ',' in data and '\n' in data:
            lines = data.split('\n')
            if len(lines) > 1 and all(',' in line for line in lines[:2]):
                return "csv"
        
        # Check if it's a list (comma-separated or newline-separated)
        if ',' in data or '\n' in data:
            items = re.split(r'[,;\n]', data)
            if len(items) > 1 and all(item.strip() for item in items):
                return "list"
        
        # Default to text
        return "text"
    
    def _parse_data(self, data: str, data_type: str) -> Union[Dict, List, str]:
        """Parse data based on detected type."""
        try:
            if data_type == "json":
                return json.loads(data)
            elif data_type == "csv":
                return self._parse_csv(data)
            elif data_type == "list":
                return self._parse_list(data)
            else:
                return data
        except Exception as e:
            logger.warning(f"Failed to parse data as {data_type}: {str(e)}")
            return data
    
    def _parse_csv(self, data: str) -> List[Dict[str, str]]:
        """Parse CSV data into list of dictionaries."""
        try:
            csv_file = StringIO(data)
            reader = csv.DictReader(csv_file)
            return [dict(row) for row in reader]
        except Exception as e:
            logger.warning(f"CSV parsing failed: {str(e)}")
            # Fallback: split by lines and commas
            lines = data.strip().split('\n')
            if lines:
                headers = [h.strip() for h in lines[0].split(',')]
                result = []
                for line in lines[1:]:
                    values = [v.strip() for v in line.split(',')]
                    if len(values) == len(headers):
                        result.append(dict(zip(headers, values)))
                return result
            return []
    
    def _parse_list(self, data: str) -> List[str]:
        """Parse list data into list of strings."""
        items = re.split(r'[,;\n]', data)
        return [item.strip() for item in items if item.strip()]
    
    def _format_as_json(self, data: Union[Dict, List, str], indent: int = 2, include_metadata: bool = True) -> str:
        """Format data as JSON with proper indentation."""
        try:
            if include_metadata:
                formatted_data = {
                    "data": data,
                    "format": "json",
                    "metadata": {
                        "indentation": indent,
                        "formatted_at": "now"
                    }
                }
            else:
                formatted_data = data
            
            return json.dumps(formatted_data, indent=indent, ensure_ascii=False)
        except Exception as e:
            logger.error(f"JSON formatting failed: {str(e)}")
            return f'{{"error": "JSON formatting failed", "original_data": "{str(data)[:100]}..."}}'
    
    def _format_as_csv(self, data: Union[Dict, List, str], include_metadata: bool = True) -> str:
        """Format data as CSV."""
        try:
            if isinstance(data, list) and data and isinstance(data[0], dict):
                # List of dictionaries
                if not data:
                    return ""
                
                output = StringIO()
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
                csv_content = output.getvalue()
                output.close()
                
                if include_metadata:
                    return f"# CSV Export\n# Generated at: now\n# Records: {len(data)}\n\n{csv_content}"
                return csv_content
            else:
                # Single value or simple list
                if isinstance(data, list):
                    csv_content = '\n'.join(f'"{item}"' for item in data)
                else:
                    csv_content = f'"{data}"'
                
                if include_metadata:
                    return f"# CSV Export\n# Generated at: now\n# Type: {type(data).__name__}\n\n{csv_content}"
                return csv_content
        except Exception as e:
            logger.error(f"CSV formatting failed: {str(e)}")
            return f"Error: CSV formatting failed - {str(e)}"
    
    def _format_as_xml(self, data: Union[Dict, List, str], include_metadata: bool = True) -> str:
        """Format data as XML."""
        try:
            if isinstance(data, dict):
                xml_content = self._dict_to_xml(data, "data")
            elif isinstance(data, list):
                xml_content = f"<data>\n" + '\n'.join(f"  <item>{item}</item>" for item in data) + "\n</data>"
            else:
                xml_content = f"<data>{data}</data>"
            
            if include_metadata:
                return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- XML Export -->
<!-- Generated at: now -->
<!-- Type: {type(data).__name__} -->
{xml_content}"""
            return f"""<?xml version="1.0" encoding="UTF-8"?>
{xml_content}"""
        except Exception as e:
            logger.error(f"XML formatting failed: {str(e)}")
            return f"<error>XML formatting failed - {str(e)}</error>"
    
    def _dict_to_xml(self, data: Dict, root_name: str) -> str:
        """Convert dictionary to XML string."""
        xml_parts = [f"<{root_name}>"]
        for key, value in data.items():
            if isinstance(value, dict):
                xml_parts.append(self._dict_to_xml(value, key))
            elif isinstance(value, list):
                xml_parts.append(f"<{key}>")
                for item in value:
                    if isinstance(item, dict):
                        xml_parts.append(self._dict_to_xml(item, "item"))
                    else:
                        xml_parts.append(f"<item>{item}</item>")
                xml_parts.append(f"</{key}>")
            else:
                xml_parts.append(f"<{key}>{value}</{key}>")
        xml_parts.append(f"</{root_name}>")
        return '\n'.join(xml_parts)
    
    def _format_as_yaml(self, data: Union[Dict, List, str], include_metadata: bool = True) -> str:
        """Format data as YAML."""
        try:
            if include_metadata:
                yaml_content = f"""# YAML Export
# Generated at: now
# Type: {type(data).__name__}

data: {data}"""
            else:
                yaml_content = str(data)
            
            return yaml_content
        except Exception as e:
            logger.error(f"YAML formatting failed: {str(e)}")
            return f"# Error: YAML formatting failed - {str(e)}"
    
    def _format_as_table(self, data: Union[Dict, List, str], include_metadata: bool = True) -> str:
        """Format data as a formatted table."""
        try:
            if isinstance(data, list) and data and isinstance(data[0], dict):
                # List of dictionaries - create table
                if not data:
                    return "No data to display"
                
                headers = list(data[0].keys())
                table_lines = []
                
                if include_metadata:
                    table_lines.append(f"# Table Export - Generated at: now")
                    table_lines.append(f"# Records: {len(data)}")
                    table_lines.append("")
                
                # Header
                header_line = "| " + " | ".join(headers) + " |"
                separator_line = "| " + " | ".join("-" * len(h) for h in headers) + " |"
                table_lines.extend([header_line, separator_line])
                
                # Data rows
                for row in data:
                    row_line = "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |"
                    table_lines.append(row_line)
                
                return '\n'.join(table_lines)
            else:
                # Single value or simple list
                if isinstance(data, list):
                    table_content = '\n'.join(f"- {item}" for item in data)
                else:
                    table_content = str(data)
                
                if include_metadata:
                    return f"# Table Export\n# Generated at: now\n# Type: {type(data).__name__}\n\n{table_content}"
                return table_content
        except Exception as e:
            logger.error(f"Table formatting failed: {str(e)}")
            return f"Error: Table formatting failed - {str(e)}"
    
    def _format_as_markdown(self, data: Union[Dict, List, str], include_metadata: bool = True) -> str:
        """Format data as Markdown."""
        try:
            if include_metadata:
                markdown_content = f"""# Data Export

**Generated at:** now  
**Type:** {type(data).__name__}  
**Format:** Markdown

"""
            else:
                markdown_content = ""
            
            if isinstance(data, dict):
                markdown_content += self._dict_to_markdown(data)
            elif isinstance(data, list):
                markdown_content += "## Data List\n\n"
                for i, item in enumerate(data, 1):
                    markdown_content += f"{i}. {item}\n"
            else:
                markdown_content += f"## Content\n\n{data}"
            
            return markdown_content
        except Exception as e:
            logger.error(f"Markdown formatting failed: {str(e)}")
            return f"# Error\n\nMarkdown formatting failed: {str(e)}"
    
    def _dict_to_markdown(self, data: Dict, level: int = 0) -> str:
        """Convert dictionary to Markdown string."""
        markdown_content = ""
        indent = "  " * level
        
        for key, value in data.items():
            if isinstance(value, dict):
                markdown_content += f"{indent}- **{key}:**\n"
                markdown_content += self._dict_to_markdown(value, level + 1)
            elif isinstance(value, list):
                markdown_content += f"{indent}- **{key}:**\n"
                for item in value:
                    if isinstance(item, dict):
                        markdown_content += self._dict_to_markdown(item, level + 1)
                    else:
                        markdown_content += f"{indent}  - {item}\n"
            else:
                markdown_content += f"{indent}- **{key}:** {value}\n"
        
        return markdown_content
