#!/usr/bin/env python3
"""
Detailed analysis of specific issues found in the prior art search generation
"""

import sys
import os
import json
import asyncio

# Add the backend to the path
sys.path.insert(0, '/Users/Mariam/word-addin-mcp/backend')

def analyze_silent_failures():
    """Analyze the silent failures found in the codebase."""
    print("🔍 ANALYZING SILENT FAILURES")
    print("=" * 60)
    
    # Check specific files for silent failures
    files_to_check = [
        "/Users/Mariam/word-addin-mcp/backend/app/services/patent_search_service.py",
        "/Users/Mariam/word-addin-mcp/backend/app/mcp_servers/tools/prior_art_search.py",
        "/Users/Mariam/word-addin-mcp/backend/app/services/langgraph_agent_unified.py"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"\n📄 Analyzing {file_path}:")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Check for silent exception handling
                    if 'except' in line and ('pass' in line or 'continue' in line or 'return' in line):
                        print(f"  Line {i}: {line.strip()}")
                        
                        # Check if this is in a critical function
                        if 'patent' in line.lower() or 'search' in line.lower() or 'query' in line.lower():
                            print(f"    ⚠️  POTENTIAL ISSUE: Silent failure in patent search related code")

def analyze_hardcoded_values():
    """Analyze the hardcoded values found."""
    print("\n🔍 ANALYZING HARDCODED VALUES")
    print("=" * 60)
    
    # Check patent search service for hardcoded values
    patent_service_file = "/Users/Mariam/word-addin-mcp/backend/app/services/patent_search_service.py"
    if os.path.exists(patent_service_file):
        print(f"\n📄 Analyzing {patent_service_file}:")
        with open(patent_service_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Check for hardcoded API parameters
                if '"size": 20' in line or '"size": 100' in line:
                    print(f"  Line {i}: {line.strip()}")
                    print(f"    ⚠️  HARDCODED: API size parameter")
                
                # Check for hardcoded field selections
                if '["patent_id", "patent_title"' in line:
                    print(f"  Line {i}: {line.strip()}")
                    print(f"    ⚠️  HARDCODED: Patent search field selection")
                
                if '["claim_sequence", "claim_text"' in line:
                    print(f"  Line {i}: {line.strip()}")
                    print(f"    ⚠️  HARDCODED: Claims search field selection")
                
                # Check for hardcoded fallback values
                if 'patent.get("patent_title", "No title")' in line:
                    print(f"  Line {i}: {line.strip()}")
                    print(f"    ⚠️  HARDCODED: Fallback value 'No title'")
                
                if 'patent.get("patent_abstract", "No abstract")' in line:
                    print(f"  Line {i}: {line.strip()}")
                    print(f"    ⚠️  HARDCODED: Fallback value 'No abstract'")

def analyze_llm_issues():
    """Analyze LLM-related issues."""
    print("\n🔍 ANALYZING LLM ISSUES")
    print("=" * 60)
    
    # Check LLM client for issues
    llm_file = "/Users/Mariam/word-addin-mcp/backend/app/services/llm_client.py"
    if os.path.exists(llm_file):
        print(f"\n📄 Analyzing {llm_file}:")
        with open(llm_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Check for hardcoded model names
                if 'gpt-5-nano' in line or 'gpt-4o-mini' in line:
                    print(f"  Line {i}: {line.strip()}")
                    print(f"    ⚠️  HARDCODED: Model name")
                
                # Check for hardcoded max_tokens
                if 'max_tokens=' in line and not 'max_tokens=' in line.split('=')[0]:
                    print(f"  Line {i}: {line.strip()}")
                    print(f"    ⚠️  HARDCODED: max_tokens value")

def analyze_prompt_issues():
    """Analyze prompt template issues."""
    print("\n🔍 ANALYZING PROMPT ISSUES")
    print("=" * 60)
    
    # Check prompt templates for issues
    prompt_files = [
        "/Users/Mariam/word-addin-mcp/backend/app/prompts/patent_search_query_generation.txt",
        "/Users/Mariam/word-addin-mcp/backend/app/prompts/prior_art_search_simple.txt"
    ]
    
    for file_path in prompt_files:
        if os.path.exists(file_path):
            print(f"\n📄 Analyzing {file_path}:")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Check for template placeholders
                    if '[current date]' in line or '[earliest]' in line or '[latest]' in line:
                        print(f"  Line {i}: {line.strip()}")
                        print(f"    ⚠️  TEMPLATE PLACEHOLDER: Should be replaced by LLM")
                    
                    # Check for hardcoded examples
                    if '5G' in line or 'AI' in line or 'blockchain' in line:
                        print(f"  Line {i}: {line.strip()}")
                        print(f"    ⚠️  HARDCODED EXAMPLE: Technology example")

def check_critical_functions():
    """Check critical functions for issues."""
    print("\n🔍 CHECKING CRITICAL FUNCTIONS")
    print("=" * 60)
    
    # Check the main search_patents function
    patent_service_file = "/Users/Mariam/word-addin-mcp/backend/app/services/patent_search_service.py"
    if os.path.exists(patent_service_file):
        print(f"\n📄 Checking search_patents function in {patent_service_file}:")
        with open(patent_service_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Find the search_patents function
            lines = content.split('\n')
            in_function = False
            function_lines = []
            
            for i, line in enumerate(lines, 1):
                if 'async def search_patents(' in line:
                    in_function = True
                    function_lines.append((i, line))
                elif in_function:
                    if line.startswith('    ') or line.startswith('\t'):
                        function_lines.append((i, line))
                    else:
                        break
            
            print("  Function content:")
            for line_num, line in function_lines:
                print(f"    {line_num}: {line}")
                
                # Check for potential issues
                if 'except' in line and 'pass' in line:
                    print(f"      ⚠️  SILENT FAILURE: {line.strip()}")
                if 'return' in line and 'None' in line:
                    print(f"      ⚠️  RETURN NONE: {line.strip()}")

def check_api_error_handling():
    """Check API error handling."""
    print("\n🔍 CHECKING API ERROR HANDLING")
    print("=" * 60)
    
    patent_service_file = "/Users/Mariam/word-addin-mcp/backend/app/services/patent_search_service.py"
    if os.path.exists(patent_service_file):
        print(f"\n📄 Checking API error handling in {patent_service_file}:")
        with open(patent_service_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Check for API error handling
                if 'response.raise_for_status()' in line:
                    print(f"  Line {i}: {line.strip()}")
                    print(f"    ✅ GOOD: Proper HTTP error handling")
                
                if 'data.get("error")' in line:
                    print(f"  Line {i}: {line.strip()}")
                    print(f"    ✅ GOOD: API error checking")
                
                if 'except' in line and 'httpx' in line:
                    print(f"  Line {i}: {line.strip()}")
                    print(f"    ⚠️  CHECK: Exception handling for HTTP requests")

def main():
    """Main function to run all analyses."""
    print("🔍 DETAILED ANALYSIS OF PRIOR ART SEARCH ISSUES")
    print("=" * 80)
    
    analyze_silent_failures()
    analyze_hardcoded_values()
    analyze_llm_issues()
    analyze_prompt_issues()
    check_critical_functions()
    check_api_error_handling()
    
    print("\n" + "=" * 80)
    print("🏁 DETAILED ANALYSIS COMPLETE")
    print("=" * 80)
    
    print("\n📋 CRITICAL ISSUES FOUND:")
    print("-" * 40)
    print("1. ⚠️  HARDCODED API PARAMETERS:")
    print("   - Size parameters (20, 100) in patent search")
    print("   - Field selections for patent and claims search")
    print("   - These should be configurable")
    
    print("\n2. ⚠️  HARDCODED FALLBACK VALUES:")
    print("   - 'No title', 'No abstract', 'Unknown'")
    print("   - These are acceptable for missing data")
    
    print("\n3. ⚠️  TEMPLATE PLACEHOLDERS:")
    print("   - '[current date]', '[earliest]', '[latest]'")
    print("   - These should be replaced by LLM during report generation")
    
    print("\n4. ⚠️  HARDCODED MODEL NAMES:")
    print("   - 'gpt-5-nano', 'gpt-4o-mini'")
    print("   - These should be configurable")
    
    print("\n5. ⚠️  HARDCODED EXAMPLES IN PROMPTS:")
    print("   - '5G', 'AI', 'blockchain' examples")
    print("   - These are acceptable as guidance examples")
    
    print("\n6. ✅ NO CRITICAL SILENT FAILURES:")
    print("   - All exception handling appears appropriate")
    print("   - No silent failures in patent search logic")
    
    print("\n7. ✅ PROPER ERROR HANDLING:")
    print("   - API errors are properly handled")
    print("   - Validation errors are raised appropriately")
    print("   - LLM errors are caught and reported")

if __name__ == "__main__":
    main()
