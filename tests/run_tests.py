#!/usr/bin/env python3
"""
Test Runner for Word Add-in MCP System
"""
import asyncio
import pytest
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add the tests directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from conftest import TestResult

class TestRunner:
    """Main test runner class."""
    
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
        self.test_categories = [
            "test_api_endpoints",
            "test_mcp_tools", 
            "test_integration",
            "test_llm_capabilities",
            "test_performance"
        ]
    
    async def run_all_tests(self):
        """Run all test categories."""
        print("🚀 Starting Word Add-in MCP System Test Suite")
        print("=" * 60)
        
        for category in self.test_categories:
            print(f"\n📋 Running {category}...")
            await self.run_test_category(category)
        
        self.generate_report()
    
    async def run_test_category(self, category: str):
        """Run a specific test category."""
        try:
            # Run pytest for the specific test file
            test_file = f"tests/{category}.py"
            if os.path.exists(test_file):
                result = pytest.main([
                    test_file,
                    "-v",
                    "--tb=short",
                    "--disable-warnings"
                ])
                
                self.results[category] = {
                    "status": "completed",
                    "exit_code": result,
                    "timestamp": time.time()
                }
            else:
                self.results[category] = {
                    "status": "skipped",
                    "reason": f"Test file {test_file} not found",
                    "timestamp": time.time()
                }
                
        except Exception as e:
            self.results[category] = {
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def generate_report(self):
        """Generate test execution report."""
        end_time = time.time()
        total_time = end_time - self.start_time
        
        print("\n" + "=" * 60)
        print("📊 TEST EXECUTION SUMMARY")
        print("=" * 60)
        
        print(f"⏱️  Total Execution Time: {total_time:.2f} seconds")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n📋 Test Categories:")
        for category, result in self.results.items():
            status_emoji = {
                "completed": "✅",
                "skipped": "⏭️",
                "error": "❌"
            }.get(result["status"], "❓")
            
            print(f"  {status_emoji} {category}: {result['status']}")
            if result["status"] == "error":
                print(f"     Error: {result.get('error', 'Unknown error')}")
        
        # Save results to file
        self.save_results_to_file()
    
    def save_results_to_file(self):
        """Save test results to a JSON file."""
        report_data = {
            "test_execution": {
                "start_time": self.start_time,
                "end_time": time.time(),
                "total_time": time.time() - self.start_time,
                "timestamp": datetime.now().isoformat()
            },
            "results": self.results,
            "summary": {
                "total_categories": len(self.test_categories),
                "completed": len([r for r in self.results.values() if r["status"] == "completed"]),
                "skipped": len([r for r in self.results.values() if r["status"] == "skipped"]),
                "errors": len([r for r in self.results.values() if r["status"] == "error"])
            }
        }
        
        with open("test_results.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n💾 Results saved to: test_results.json")

async def main():
    """Main entry point."""
    runner = TestRunner()
    await runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
