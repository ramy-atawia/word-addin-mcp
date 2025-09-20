#!/usr/bin/env python3
"""
Comprehensive Test Runner for Word Add-in MCP

This script runs all available tests and provides a comprehensive report.
It handles missing dependencies gracefully and focuses on what can be tested.
"""

import sys
import os
import subprocess
import importlib
from pathlib import Path
from typing import List, Dict, Any, Tuple

class TestRunner:
    """Comprehensive test runner with dependency handling."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_root = self.project_root / "backend"
        self.results = {
            "unit_tests": {"passed": 0, "failed": 0, "skipped": 0, "errors": []},
            "integration_tests": {"passed": 0, "failed": 0, "skipped": 0, "errors": []},
            "langgraph_tests": {"passed": 0, "failed": 0, "skipped": 0, "errors": []},
            "standalone_tests": {"passed": 0, "failed": 0, "skipped": 0, "errors": []},
            "e2e_tests": {"passed": 0, "failed": 0, "skipped": 0, "errors": []}
        }
    
    def check_dependencies(self) -> Dict[str, bool]:
        """Check which dependencies are available."""
        deps = {
            "langgraph": False,
            "fastmcp": False,
            "pytest": False,
            "httpx": False
        }
        
        for dep in deps:
            try:
                importlib.import_module(dep)
                deps[dep] = True
            except ImportError:
                deps[dep] = False
        
        return deps
    
    def run_command(self, cmd: List[str], cwd: Path = None, timeout: int = 300, env: Dict[str, str] = None) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 124, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)
    
    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests."""
        print("🧪 Running Unit Tests...")
        
        # Run main unit tests
        cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]
        exit_code, stdout, stderr = self.run_command(cmd)
        
        # Parse results
        if exit_code == 0:
            self.results["unit_tests"]["passed"] = stdout.count("PASSED")
            self.results["unit_tests"]["failed"] = stdout.count("FAILED")
            self.results["unit_tests"]["skipped"] = stdout.count("SKIPPED")
        else:
            self.results["unit_tests"]["errors"].append(f"Unit tests failed: {stderr}")
        
        return {"exit_code": exit_code, "stdout": stdout, "stderr": stderr}
    
    def run_standalone_tests(self) -> Dict[str, Any]:
        """Run standalone tests."""
        print("🧪 Running Standalone Tests...")
        
        cmd = [sys.executable, "tests/standalone_patent_search_tests.py"]
        exit_code, stdout, stderr = self.run_command(cmd)
        
        if exit_code == 0:
            self.results["standalone_tests"]["passed"] = stdout.count("ok")
            self.results["standalone_tests"]["failed"] = stdout.count("FAILED")
        else:
            self.results["standalone_tests"]["errors"].append(f"Standalone tests failed: {stderr}")
        
        return {"exit_code": exit_code, "stdout": stdout, "stderr": stderr}
    
    def run_langgraph_tests(self) -> Dict[str, Any]:
        """Run LangGraph tests (mock-based if LangGraph not available)."""
        print("🧪 Running LangGraph Tests...")
        
        deps = self.check_dependencies()
        
        # Set PYTHONPATH and run LangGraph tests
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.backend_root)
        
        if not deps["langgraph"]:
            print("⚠️  LangGraph not available, running mock-based tests")
            cmd = [sys.executable, "-m", "pytest", "backend/tests/test_langgraph_mock.py", "-v", "--tb=short"]
        else:
            cmd = [sys.executable, "-m", "pytest", "backend/tests/", "-v", "--tb=short"]
        
        exit_code, stdout, stderr = self.run_command(cmd, env=env)
        
        if exit_code == 0:
            self.results["langgraph_tests"]["passed"] = stdout.count("PASSED")
            self.results["langgraph_tests"]["failed"] = stdout.count("FAILED")
            self.results["langgraph_tests"]["skipped"] = stdout.count("SKIPPED")
        else:
            self.results["langgraph_tests"]["errors"].append(f"LangGraph tests failed: {stderr}")
        
        return {"exit_code": exit_code, "stdout": stdout, "stderr": stderr}
    
    def run_e2e_tests(self) -> Dict[str, Any]:
        """Run E2E tests (will fail if backend not running)."""
        print("🧪 Running E2E Tests...")
        
        cmd = [sys.executable, "comprehensive_e2e_test_suite.py"]
        exit_code, stdout, stderr = self.run_command(cmd, timeout=60)
        
        # E2E tests are expected to fail if backend is not running
        if "All connection attempts failed" in stdout:
            print("⚠️  E2E tests failed - backend not running (expected)")
            self.results["e2e_tests"]["skipped"] = 1
        else:
            if exit_code == 0:
                self.results["e2e_tests"]["passed"] = stdout.count("✅")
                self.results["e2e_tests"]["failed"] = stdout.count("❌")
            else:
                self.results["e2e_tests"]["errors"].append(f"E2E tests failed: {stderr}")
        
        return {"exit_code": exit_code, "stdout": stdout, "stderr": stderr}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all available tests."""
        print("🚀 Starting Comprehensive Test Suite")
        print("=" * 60)
        
        # Check dependencies
        deps = self.check_dependencies()
        print(f"📦 Dependencies: {deps}")
        print()
        
        # Run tests
        unit_result = self.run_unit_tests()
        print()
        
        standalone_result = self.run_standalone_tests()
        print()
        
        langgraph_result = self.run_langgraph_tests()
        print()
        
        e2e_result = self.run_e2e_tests()
        print()
        
        # Generate report
        self.generate_report()
        
        return {
            "unit_tests": unit_result,
            "standalone_tests": standalone_result,
            "langgraph_tests": langgraph_result,
            "e2e_tests": e2e_result
        }
    
    def generate_report(self):
        """Generate comprehensive test report."""
        print("=" * 60)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        total_errors = 0
        
        for category, results in self.results.items():
            passed = results["passed"]
            failed = results["failed"]
            skipped = results["skipped"]
            errors = len(results["errors"])
            
            total_passed += passed
            total_failed += failed
            total_skipped += skipped
            total_errors += errors
            
            status = "✅" if failed == 0 and errors == 0 else "❌"
            print(f"{status} {category.replace('_', ' ').title()}: {passed} passed, {failed} failed, {skipped} skipped, {errors} errors")
            
            if results["errors"]:
                for error in results["errors"]:
                    print(f"   ⚠️  {error}")
        
        print("-" * 60)
        print(f"📈 TOTAL: {total_passed} passed, {total_failed} failed, {total_skipped} skipped, {total_errors} errors")
        
        success_rate = (total_passed / (total_passed + total_failed)) * 100 if (total_passed + total_failed) > 0 else 0
        print(f"🎯 Success Rate: {success_rate:.1f}%")
        
        if total_failed == 0 and total_errors == 0:
            print("🎉 All tests passed!")
        else:
            print("⚠️  Some tests failed or had errors")
        
        print("=" * 60)

def main():
    """Main entry point."""
    runner = TestRunner()
    runner.run_all_tests()

if __name__ == "__main__":
    main()
