"""
Tool mapping configuration for LangGraph agent.

This module provides configurable tool mappings and keywords
for intent detection and workflow planning.
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class ToolMapping:
    """Configuration for a tool mapping."""
    name: str
    keywords: List[str]
    description_keywords: List[str]
    default_parameters: Dict[str, Any]
    context_requirements: List[str] = None


# Default tool mappings configuration
DEFAULT_TOOL_MAPPINGS = {
    "prior_art_search_tool": ToolMapping(
        name="prior_art_search_tool",
        keywords=[
            "prior art", "patent search", "patent", "patents", 
            "prior art search", "patent lookup", "patent database"
        ],
        description_keywords=["search", "patent", "prior art", "patents"],
        default_parameters={"query": "{user_input}"},
        context_requirements=[]
    ),
    
    "web_search_tool": ToolMapping(
        name="web_search_tool",
        keywords=[
            "web search", "internet search", "search", "find", 
            "lookup", "google", "web lookup", "online search"
        ],
        description_keywords=["search", "web", "internet", "online"],
        default_parameters={"query": "{user_input}"},
        context_requirements=[]
    ),
    
    "claim_drafting_tool": ToolMapping(
        name="claim_drafting_tool",
        keywords=[
            "draft", "claims", "claim drafting", "write claims", 
            "create claims", "generate claims", "patent claims"
        ],
        description_keywords=["draft", "claim", "write", "create", "generate"],
        default_parameters={"user_query": "{user_input}"},
        context_requirements=["search_results", "prior_art_results"]
    ),
    
    "claim_analysis_tool": ToolMapping(
        name="claim_analysis_tool",
        keywords=[
            "analyze", "analysis", "evaluate", "assess", 
            "review", "examine", "analyze claims"
        ],
        description_keywords=["analyze", "analysis", "evaluate", "assess"],
        default_parameters={"user_query": "{user_input}"},
        context_requirements=["claim_results", "draft_results"]
    )
}


def get_tool_mapping(tool_name: str) -> ToolMapping:
    """Get tool mapping configuration for a specific tool."""
    return DEFAULT_TOOL_MAPPINGS.get(tool_name, ToolMapping(
        name=tool_name,
        keywords=[],
        description_keywords=[],
        default_parameters={"user_query": "{user_input}"}
    ))


def get_all_tool_mappings() -> Dict[str, ToolMapping]:
    """Get all tool mapping configurations."""
    return DEFAULT_TOOL_MAPPINGS.copy()


def create_dynamic_tool_mapping(available_tools: List[Dict[str, Any]]) -> Dict[str, ToolMapping]:
    """Create dynamic tool mapping based on available tools."""
    dynamic_mappings = {}
    
    for tool in available_tools:
        tool_name = tool.get("name", "")
        description = tool.get("description", "").lower()
        
        # Check if we have a predefined mapping
        if tool_name in DEFAULT_TOOL_MAPPINGS:
            dynamic_mappings[tool_name] = DEFAULT_TOOL_MAPPINGS[tool_name]
        else:
            # Create dynamic mapping based on tool name and description
            keywords = _extract_keywords_from_tool(tool_name, description)
            description_keywords = _extract_description_keywords(description)
            
            dynamic_mappings[tool_name] = ToolMapping(
                name=tool_name,
                keywords=keywords,
                description_keywords=description_keywords,
                default_parameters=_get_default_parameters_for_tool(tool_name),
                context_requirements=[]
            )
    
    return dynamic_mappings


def _extract_keywords_from_tool(tool_name: str, description: str) -> List[str]:
    """Extract keywords from tool name and description."""
    keywords = []
    tool_name_lower = tool_name.lower()
    
    # Extract from tool name
    if "search" in tool_name_lower:
        keywords.extend(["search", "find", "lookup", "query"])
    if "prior" in tool_name_lower or "art" in tool_name_lower:
        keywords.extend(["prior art", "patent", "patents"])
    if "web" in tool_name_lower:
        keywords.extend(["web search", "internet search", "web lookup"])
    if "draft" in tool_name_lower or "claim" in tool_name_lower:
        keywords.extend(["draft", "claims", "claim drafting", "write claims"])
    if "analyze" in tool_name_lower or "analysis" in tool_name_lower:
        keywords.extend(["analyze", "analysis", "evaluate", "assess"])
    
    # Extract from description
    if "search" in description:
        keywords.extend(["search", "find"])
    if "patent" in description:
        keywords.extend(["patent", "patents"])
    if "draft" in description:
        keywords.extend(["draft", "write", "create"])
    if "analyze" in description:
        keywords.extend(["analyze", "evaluate"])
    
    # Remove duplicates and empty strings
    return list(set([k for k in keywords if k]))


def _extract_description_keywords(description: str) -> List[str]:
    """Extract keywords from tool description."""
    keywords = []
    
    if "search" in description:
        keywords.append("search")
    if "patent" in description:
        keywords.append("patent")
    if "draft" in description:
        keywords.append("draft")
    if "analyze" in description:
        keywords.append("analyze")
    if "web" in description:
        keywords.append("web")
    if "prior art" in description:
        keywords.append("prior art")
    
    return keywords


def _get_default_parameters_for_tool(tool_name: str) -> Dict[str, Any]:
    """Get default parameters for a tool based on its name."""
    tool_name_lower = tool_name.lower()
    
    if "search" in tool_name_lower:
        return {"query": "{user_input}"}
    elif "draft" in tool_name_lower or "claim" in tool_name_lower:
        return {"user_query": "{user_input}"}
    elif "analyze" in tool_name_lower:
        return {"user_query": "{user_input}"}
    else:
        return {"user_query": "{user_input}"}


# Multi-step workflow patterns
MULTI_STEP_PATTERNS = [
    {
        "name": "search_and_draft",
        "description": "Search for information then draft claims",
        "pattern": ["search", "draft"],
        "tools": ["search_tool", "claim_drafting_tool"],
        "context_mapping": {
            "claim_drafting_tool": "search_results"
        }
    },
    {
        "name": "prior_art_and_draft",
        "description": "Search prior art then draft claims",
        "pattern": ["prior_art", "draft"],
        "tools": ["prior_art_search_tool", "claim_drafting_tool"],
        "context_mapping": {
            "claim_drafting_tool": "prior_art_results"
        }
    },
    {
        "name": "draft_and_analyze",
        "description": "Draft claims then analyze them",
        "pattern": ["draft", "analyze"],
        "tools": ["claim_drafting_tool", "claim_analysis_tool"],
        "context_mapping": {
            "claim_analysis_tool": "draft_results"
        }
    }
]


def detect_multi_step_pattern(user_input: str, available_tools: List[str]) -> Dict[str, Any]:
    """Detect multi-step workflow pattern from user input."""
    user_input_lower = user_input.lower()
    
    for pattern in MULTI_STEP_PATTERNS:
        pattern_keywords = pattern["pattern"]
        if all(keyword in user_input_lower for keyword in pattern_keywords):
            # Check if required tools are available
            required_tools = pattern["tools"]
            available_tool_names = [tool.get("name", "") if isinstance(tool, dict) else tool for tool in available_tools]
            
            if all(any(req_tool in avail_tool for avail_tool in available_tool_names) for req_tool in required_tools):
                return pattern
    
    return None
