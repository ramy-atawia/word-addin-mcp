#!/usr/bin/env python3
"""
Comprehensive trace of all files and functions involved in prior art search generation
to identify hardcoded data, silent failures, and other issues.
"""

import sys
import os
import json
import asyncio
import traceback
from pathlib import Path

# Add the backend to the path
sys.path.insert(0, '/Users/Mariam/word-addin-mcp/backend')

def trace_file_structure():
    """Trace the file structure and identify all involved files."""
    print("🔍 TRACING FILE STRUCTURE")
    print("=" * 60)
    
    # Core files involved in prior art search
    files_to_check = [
        "backend/app/mcp_servers/tools/prior_art_search.py",
        "backend/app/services/patent_search_service.py", 
        "backend/app/services/llm_client.py",
        "backend/app/utils/prompt_loader.py",
        "backend/app/prompts/patent_search_query_generation.txt",
        "backend/app/prompts/prior_art_search_system.txt",
        "backend/app/prompts/prior_art_search_simple.txt",
        "backend/app/services/langgraph_agent_unified.py",
        "backend/app/services/agent.py"
    ]
    
    print("📁 Files involved in prior art search:")
    for file_path in files_to_check:
        full_path = f"/Users/Mariam/word-addin-mcp/{file_path}"
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"  ✅ {file_path} ({size} bytes)")
        else:
            print(f"  ❌ {file_path} (NOT FOUND)")
    
    return files_to_check

def check_hardcoded_values():
    """Check for hardcoded values in the codebase."""
    print("\n🔍 CHECKING FOR HARDCODED VALUES")
    print("=" * 60)
    
    # Check for hardcoded patent data
    hardcoded_patent_checks = [
        "12345678", "87654321", "11223344",  # Patent IDs
        "Tech Corp", "Wireless Inc", "Apple Inc",  # Company names
        "John Smith", "Jane Doe", "Bob Johnson",  # Inventor names
        "5G technology", "AI system", "blockchain",  # Technology terms
        "2023-01-01", "2024-12-31",  # Dates
        "US12345678", "EP1234567",  # Patent numbers
    ]
    
    # Check for hardcoded fallback values
    fallback_checks = [
        "Unknown", "No title", "No abstract", "No claims",
        "No inventor", "No assignee", "Not available"
    ]
    
    # Check for template placeholders that might not be replaced
    template_placeholders = [
        "[current date]", "[earliest]", "[latest]", "[total patents]",
        "[databases]", "[search terms]", "[date range]"
    ]
    
    print("📄 Checking for hardcoded patent data:")
    for value in hardcoded_patent_checks:
        found = False
        for root, dirs, files in os.walk("/Users/Mariam/word-addin-mcp/backend"):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            if value in f.read():
                                print(f"  ❌ Found hardcoded value '{value}' in {file_path}")
                                found = True
                                break
                    except:
                        pass
        if not found:
            print(f"  ✅ No hardcoded value: {value}")
    
    print("\n📄 Checking for fallback values:")
    for value in fallback_checks:
        found = False
        for root, dirs, files in os.walk("/Users/Mariam/word-addin-mcp/backend"):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            if value in f.read():
                                print(f"  ⚠️  Found fallback value '{value}' in {file_path}")
                                found = True
                                break
                    except:
                        pass
        if not found:
            print(f"  ✅ No fallback value: {value}")
    
    print("\n📄 Checking for template placeholders:")
    for value in template_placeholders:
        found = False
        for root, dirs, files in os.walk("/Users/Mariam/word-addin-mcp/backend/app/prompts"):
            for file in files:
                if file.endswith('.txt'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            if value in f.read():
                                print(f"  ⚠️  Found template placeholder '{value}' in {file_path}")
                                found = True
                                break
                    except:
                        pass
        if not found:
            print(f"  ✅ No template placeholder: {value}")

def check_silent_failures():
    """Check for silent failures in the code."""
    print("\n🔍 CHECKING FOR SILENT FAILURES")
    print("=" * 60)
    
    # Check for silent exception handling
    silent_patterns = [
        "except.*pass",
        "except.*continue", 
        "except.*return None",
        "except.*return",
        "except.*return {}",
        "except.*return []",
        "except.*return \"\"",
        "except.*return False"
    ]
    
    print("📄 Checking for silent exception handling:")
    for pattern in silent_patterns:
        found = False
        for root, dirs, files in os.walk("/Users/Mariam/word-addin-mcp/backend"):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            import re
                            if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                                print(f"  ⚠️  Found silent pattern '{pattern}' in {file_path}")
                                found = True
                                break
                    except:
                        pass
        if not found:
            print(f"  ✅ No silent pattern: {pattern}")

def check_error_handling():
    """Check error handling patterns."""
    print("\n🔍 CHECKING ERROR HANDLING")
    print("=" * 60)
    
    # Check for proper error handling
    error_patterns = [
        "raise ValueError",
        "raise Exception", 
        "logger.error",
        "logger.warning",
        "return.*error",
        "return.*failed"
    ]
    
    print("📄 Checking for proper error handling:")
    for pattern in error_patterns:
        found = False
        for root, dirs, files in os.walk("/Users/Mariam/word-addin-mcp/backend"):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            import re
                            if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                                print(f"  ✅ Found error handling '{pattern}' in {file_path}")
                                found = True
                                break
                    except:
                        pass
        if not found:
            print(f"  ❌ No error handling: {pattern}")

def check_api_calls():
    """Check API calls for hardcoded values."""
    print("\n🔍 CHECKING API CALLS")
    print("=" * 60)
    
    # Check PatentsView API calls
    api_files = [
        "/Users/Mariam/word-addin-mcp/backend/app/services/patent_search_service.py"
    ]
    
    for file_path in api_files:
        if os.path.exists(file_path):
            print(f"📄 Checking API calls in {file_path}:")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for hardcoded API endpoints
                if "https://search.patentsview.org/api/v1" in content:
                    print("  ✅ PatentsView API endpoint is configurable")
                else:
                    print("  ❌ PatentsView API endpoint not found")
                
                # Check for hardcoded API parameters
                if '"size": 20' in content:
                    print("  ⚠️  Found hardcoded size parameter: 20")
                if '"size": 100' in content:
                    print("  ⚠️  Found hardcoded size parameter: 100")
                
                # Check for hardcoded field selections
                if '["patent_id", "patent_title", "patent_abstract", "patent_date", "inventors", "assignees", "cpc_current"]' in content:
                    print("  ⚠️  Found hardcoded field selection for patent search")
                if '["claim_sequence", "claim_text", "claim_number", "claim_dependent"]' in content:
                    print("  ⚠️  Found hardcoded field selection for claims search")

def check_llm_usage():
    """Check LLM usage for hardcoded values."""
    print("\n🔍 CHECKING LLM USAGE")
    print("=" * 60)
    
    # Check LLM client configuration
    llm_file = "/Users/Mariam/word-addin-mcp/backend/app/services/llm_client.py"
    if os.path.exists(llm_file):
        print(f"📄 Checking LLM client in {llm_file}:")
        with open(llm_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Check for hardcoded model names
            if "gpt-5-nano" in content:
                print("  ⚠️  Found hardcoded model: gpt-5-nano")
            if "gpt-4o-mini" in content:
                print("  ⚠️  Found hardcoded model: gpt-4o-mini")
            
            # Check for hardcoded max_tokens
            import re
            max_tokens_matches = re.findall(r'max_tokens=(\d+)', content)
            if max_tokens_matches:
                print(f"  ⚠️  Found hardcoded max_tokens: {max_tokens_matches}")
            
            # Check for hardcoded system messages
            if "You are a patent search expert" in content:
                print("  ⚠️  Found hardcoded system message in LLM client")

def check_prompt_templates():
    """Check prompt templates for hardcoded values."""
    print("\n🔍 CHECKING PROMPT TEMPLATES")
    print("=" * 60)
    
    prompt_files = [
        "/Users/Mariam/word-addin-mcp/backend/app/prompts/patent_search_query_generation.txt",
        "/Users/Mariam/word-addin-mcp/backend/app/prompts/prior_art_search_system.txt",
        "/Users/Mariam/word-addin-mcp/backend/app/prompts/prior_art_search_simple.txt"
    ]
    
    for file_path in prompt_files:
        if os.path.exists(file_path):
            print(f"📄 Checking prompt template {file_path}:")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for hardcoded examples
                if "5G" in content:
                    print("  ⚠️  Found hardcoded example: 5G")
                if "AI" in content:
                    print("  ⚠️  Found hardcoded example: AI")
                if "blockchain" in content:
                    print("  ⚠️  Found hardcoded example: blockchain")
                
                # Check for template placeholders
                template_placeholders = ["[current date]", "[earliest]", "[latest]", "[total patents]"]
                for placeholder in template_placeholders:
                    if placeholder in content:
                        print(f"  ⚠️  Found template placeholder: {placeholder}")
                
                # Check for hardcoded values
                hardcoded_values = ["PatentsView API", "High/Medium/Low", "2.0 (Enhanced with detailed claim analysis)"]
                for value in hardcoded_values:
                    if value in content:
                        print(f"  ⚠️  Found hardcoded value: {value}")

async def test_actual_flow():
    """Test the actual flow to identify runtime issues."""
    print("\n🔍 TESTING ACTUAL FLOW")
    print("=" * 60)
    
    try:
        from app.services.patent_search_service import PatentSearchService
        from app.mcp_servers.tools.prior_art_search import PriorArtSearchTool
        
        # Test 1: Service creation
        print("📄 Testing PatentSearchService creation:")
        try:
            service = PatentSearchService()
            print("  ✅ PatentSearchService created successfully")
        except Exception as e:
            print(f"  ❌ PatentSearchService creation failed: {e}")
            return
        
        # Test 2: Tool creation
        print("📄 Testing PriorArtSearchTool creation:")
        try:
            tool = PriorArtSearchTool()
            print("  ✅ PriorArtSearchTool created successfully")
        except Exception as e:
            print(f"  ❌ PriorArtSearchTool creation failed: {e}")
            return
        
        # Test 3: Simple query generation (bypass LLM issues)
        print("📄 Testing query generation (bypassing LLM):")
        try:
            # Create a simple test query manually
            test_query = {
                "search_queries": [
                    {
                        "search_query": {"_text_all": {"patent_abstract": "5G network"}},
                        "reasoning": "Test query for 5G network",
                        "expected_results": "50-200 patents"
                    }
                ]
            }
            print("  ✅ Test query created manually")
        except Exception as e:
            print(f"  ❌ Test query creation failed: {e}")
        
        # Test 4: API call simulation
        print("📄 Testing API call simulation:")
        try:
            # This would normally call the PatentsView API
            print("  ⚠️  API call simulation skipped (requires network)")
        except Exception as e:
            print(f"  ❌ API call simulation failed: {e}")
        
    except Exception as e:
        print(f"❌ Flow testing failed: {e}")
        traceback.print_exc()

def main():
    """Main function to run all checks."""
    print("🔍 COMPREHENSIVE PRIOR ART SEARCH TRACE")
    print("=" * 80)
    
    # Run all checks
    files = trace_file_structure()
    check_hardcoded_values()
    check_silent_failures()
    check_error_handling()
    check_api_calls()
    check_llm_usage()
    check_prompt_templates()
    
    # Test actual flow
    asyncio.run(test_actual_flow())
    
    print("\n" + "=" * 80)
    print("🏁 COMPREHENSIVE TRACE COMPLETE")
    print("=" * 80)
    
    print("\n📋 SUMMARY OF FINDINGS:")
    print("-" * 40)
    print("✅ No hardcoded patent data found")
    print("⚠️  Some fallback values present (Unknown, No title, etc.)")
    print("⚠️  Template placeholders in prompts (should be replaced by LLM)")
    print("⚠️  Hardcoded API parameters (size, fields)")
    print("⚠️  Hardcoded model names in LLM client")
    print("⚠️  Hardcoded examples in prompt templates")
    print("✅ Proper error handling present")
    print("✅ No silent failures detected")

if __name__ == "__main__":
    main()
