#!/usr/bin/env python3
"""
Test runner for Patent Search Integration Tests.

This script runs the comprehensive patent search integration tests
with the three validated test cases:
1. 5G handover using AI
2. 5G dynamic spectrum sharing
3. Financial AI auditing

Usage:
    python tests/run_patent_search_tests.py
    python tests/run_patent_search_tests.py --verbose
    python tests/run_patent_search_tests.py --specific test_claims_text_inclusion
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_patent_search_tests(verbose=False, specific_test=None, markers=None):
    """Run patent search integration tests."""
    
    # Base pytest command
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/backend/test_patent_search_integration.py",
        "-v" if verbose else "-q"
    ]
    
    # Add specific test if requested
    if specific_test:
        cmd.extend(["-k", specific_test])
    
    # Add markers if specified
    if markers:
        cmd.extend(["-m", markers])
    
    # Add additional options
    cmd.extend([
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker checking
        "--disable-warnings",  # Disable warnings for cleaner output
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, cwd=project_root, check=True)
        print("=" * 60)
        print("✅ All patent search integration tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print("=" * 60)
        print(f"❌ Tests failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_specific_test_cases():
    """Run specific test cases to validate the three main scenarios."""
    
    test_cases = [
        {
            "name": "5G Handover AI Test",
            "test": "test_patent_search_tool_execution",
            "description": "Tests patent search for 5G handover using AI"
        },
        {
            "name": "5G Dynamic Spectrum Sharing Test", 
            "test": "test_claims_text_inclusion",
            "description": "Tests claims text inclusion in reports"
        },
        {
            "name": "Financial AI Auditing Test",
            "test": "test_report_quality_standards", 
            "description": "Tests professional report quality standards"
        }
    ]
    
    print("🧪 Running Specific Patent Search Test Cases")
    print("=" * 60)
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n🔍 {test_case['name']}")
        print(f"   {test_case['description']}")
        print("-" * 40)
        
        success = run_patent_search_tests(
            verbose=True,
            specific_test=test_case['test']
        )
        
        if success:
            print(f"✅ {test_case['name']} - PASSED")
        else:
            print(f"❌ {test_case['name']} - FAILED")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All specific test cases passed!")
    else:
        print("💥 Some test cases failed!")
    
    return all_passed

def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="Run Patent Search Integration Tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_patent_search_tests.py
  python tests/run_patent_search_tests.py --verbose
  python tests/run_patent_search_tests.py --specific test_claims_text_inclusion
  python tests/run_patent_search_tests.py --markers "integration and patent_search"
  python tests/run_patent_search_tests.py --specific-cases
        """
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Run tests in verbose mode"
    )
    
    parser.add_argument(
        "--specific", "-s",
        type=str,
        help="Run a specific test by name pattern"
    )
    
    parser.add_argument(
        "--markers", "-m",
        type=str,
        help="Run tests with specific markers (e.g., 'integration and patent_search')"
    )
    
    parser.add_argument(
        "--specific-cases",
        action="store_true",
        help="Run the three main test cases individually"
    )
    
    args = parser.parse_args()
    
    print("🔬 Patent Search Integration Test Runner")
    print("=" * 60)
    
    if args.specific_cases:
        success = run_specific_test_cases()
    else:
        success = run_patent_search_tests(
            verbose=args.verbose,
            specific_test=args.specific,
            markers=args.markers
        )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
