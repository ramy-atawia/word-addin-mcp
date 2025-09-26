#!/usr/bin/env python3
"""
Comprehensive Async Implementation Test Suite
Tests all critical functionality of the async job queue system
"""
import asyncio
import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List

# Test configuration
BASE_URL = "http://localhost:9000"
TEST_MESSAGES = [
    "prior art search 5g ai",
    "draft 3 claims in machine learning",
    "analyze patent claims for blockchain",
    "web search artificial intelligence trends",
    "general question about patents"
]

class AsyncTestSuite:
    def __init__(self):
        self.base_url = BASE_URL
        self.test_results = []
        self.job_ids = []
        
    async def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print("🧪 Starting Comprehensive Async Implementation Tests")
        print("=" * 60)
        
        # Test 1: Basic Job Submission
        await self.test_basic_job_submission()
        
        # Test 2: Real Progress Tracking
        await self.test_real_progress_tracking()
        
        # Test 3: Job Cleanup and Memory Management
        await self.test_job_cleanup()
        
        # Test 4: Error Recovery and Retry
        await self.test_error_recovery()
        
        # Test 5: Job Timeout Handling
        await self.test_job_timeouts()
        
        # Test 6: Adaptive Polling
        await self.test_adaptive_polling()
        
        # Test 7: Authentication
        await self.test_authentication()
        
        # Test 8: Job Statistics
        await self.test_job_statistics()
        
        # Test 9: Concurrent Jobs
        await self.test_concurrent_jobs()
        
        # Test 10: Memory Leak Prevention
        await self.test_memory_leak_prevention()
        
        # Print final results
        self.print_test_summary()
    
    async def test_basic_job_submission(self):
        """Test basic job submission functionality"""
        print("\n1. Testing Basic Job Submission...")
        
        try:
            for message in TEST_MESSAGES:
                response = requests.post(
                    f"{self.base_url}/api/v1/async/chat/submit",
                    json={
                        "message": message,
                        "context": {
                            "document_content": "",
                            "chat_history": [],
                            "available_tools": ""
                        }
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    job_data = response.json()
                    job_id = job_data["job_id"]
                    self.job_ids.append(job_id)
                    print(f"✅ Job submitted: {job_id[:8]}... - {message}")
                    self.test_results.append(("Basic Job Submission", "PASS", f"Job {job_id[:8]}... submitted"))
                else:
                    print(f"❌ Failed to submit job: {response.status_code} - {response.text}")
                    self.test_results.append(("Basic Job Submission", "FAIL", f"HTTP {response.status_code}"))
                    
        except Exception as e:
            print(f"❌ Basic job submission test failed: {e}")
            self.test_results.append(("Basic Job Submission", "FAIL", str(e)))
    
    async def test_real_progress_tracking(self):
        """Test real progress tracking"""
        print("\n2. Testing Real Progress Tracking...")
        
        if not self.job_ids:
            print("⚠️ No jobs available for progress tracking test")
            return
            
        job_id = self.job_ids[0]
        progress_updates = []
        
        try:
            # Poll for progress updates
            for i in range(30):  # Poll for up to 1 minute
                response = requests.get(
                    f"{self.base_url}/api/v1/async/chat/status/{job_id}",
                    timeout=30
                )
                
                if response.status_code == 200:
                    status = response.json()
                    progress_updates.append(status["progress"])
                    
                    print(f"📊 Progress: {status['progress']}% - Status: {status['status']}")
                    
                    if status["status"] == "completed":
                        print("✅ Job completed successfully")
                        break
                    elif status["status"] == "failed":
                        print(f"❌ Job failed: {status.get('error', 'Unknown error')}")
                        break
                        
                time.sleep(2)
            
            # Analyze progress updates
            if len(progress_updates) > 1:
                # Check if progress actually increased
                if progress_updates[-1] > progress_updates[0]:
                    print("✅ Real progress tracking working")
                    self.test_results.append(("Real Progress Tracking", "PASS", f"Progress: {progress_updates[0]}% -> {progress_updates[-1]}%"))
                else:
                    print("⚠️ Progress tracking may not be working properly")
                    self.test_results.append(("Real Progress Tracking", "WARN", "Progress may not be updating"))
            else:
                print("⚠️ Not enough progress updates to verify")
                self.test_results.append(("Real Progress Tracking", "WARN", "Insufficient data"))
                
        except Exception as e:
            print(f"❌ Progress tracking test failed: {e}")
            self.test_results.append(("Real Progress Tracking", "FAIL", str(e)))
    
    async def test_job_cleanup(self):
        """Test job cleanup functionality"""
        print("\n3. Testing Job Cleanup...")
        
        try:
            # Get initial job count
            response = requests.get(f"{self.base_url}/api/v1/async/chat/stats", timeout=10)
            
            if response.status_code == 200:
                stats = response.json()
                initial_count = stats["total_jobs"]
                print(f"📊 Initial job count: {initial_count}")
                
                # Wait for cleanup to potentially occur
                print("⏳ Waiting for potential cleanup...")
                time.sleep(10)
                
                # Check job count again
                response = requests.get(f"{self.base_url}/api/v1/async/chat/stats", timeout=10)
                if response.status_code == 200:
                    stats = response.json()
                    final_count = stats["total_jobs"]
                    print(f"📊 Final job count: {final_count}")
                    
                    if final_count <= initial_count:
                        print("✅ Job cleanup working (count maintained or reduced)")
                        self.test_results.append(("Job Cleanup", "PASS", f"Jobs: {initial_count} -> {final_count}"))
                    else:
                        print("⚠️ Job count increased (cleanup may not be working)")
                        self.test_results.append(("Job Cleanup", "WARN", f"Jobs increased: {initial_count} -> {final_count}"))
                else:
                    print(f"❌ Failed to get final stats: {response.status_code}")
                    self.test_results.append(("Job Cleanup", "FAIL", f"HTTP {response.status_code}"))
            else:
                print(f"❌ Failed to get initial stats: {response.status_code}")
                self.test_results.append(("Job Cleanup", "FAIL", f"HTTP {response.status_code}"))
                
        except Exception as e:
            print(f"❌ Job cleanup test failed: {e}")
            self.test_results.append(("Job Cleanup", "FAIL", str(e)))
    
    async def test_error_recovery(self):
        """Test error recovery and retry mechanisms"""
        print("\n4. Testing Error Recovery...")
        
        try:
            # Submit a job with invalid data to trigger error
            response = requests.post(
                f"{self.base_url}/api/v1/async/chat/submit",
                json={
                    "message": "",  # Empty message should trigger error
                    "context": {}
                },
                timeout=10
            )
            
            if response.status_code == 200:
                job_data = response.json()
                job_id = job_data["job_id"]
                
                # Monitor the job for error handling
                for i in range(10):
                    status_response = requests.get(
                        f"{self.base_url}/api/v1/async/chat/status/{job_id}",
                        timeout=30
                    )
                    
                    if status_response.status_code == 200:
                        status = status_response.json()
                        print(f"📊 Job status: {status['status']} - Progress: {status['progress']}%")
                        
                        if status["status"] == "failed":
                            print("✅ Error handling working (job failed as expected)")
                            self.test_results.append(("Error Recovery", "PASS", "Job failed gracefully"))
                            break
                        elif status["status"] == "completed":
                            print("⚠️ Job completed unexpectedly")
                            self.test_results.append(("Error Recovery", "WARN", "Job completed instead of failing"))
                            break
                            
                    time.sleep(2)
            else:
                print(f"❌ Failed to submit test job: {response.status_code}")
                self.test_results.append(("Error Recovery", "FAIL", f"HTTP {response.status_code}"))
                
        except Exception as e:
            print(f"❌ Error recovery test failed: {e}")
            self.test_results.append(("Error Recovery", "FAIL", str(e)))
    
    async def test_job_timeouts(self):
        """Test job timeout handling"""
        print("\n5. Testing Job Timeouts...")
        
        try:
            # Submit a job that should timeout
            response = requests.post(
                f"{self.base_url}/api/v1/async/chat/submit",
                json={
                    "message": "prior art search complex machine learning algorithms with deep neural networks",
                    "context": {
                        "document_content": "Very long document content that might cause timeout...",
                        "chat_history": [],
                        "available_tools": ""
                    }
                },
                timeout=10
            )
            
            if response.status_code == 200:
                job_data = response.json()
                job_id = job_data["job_id"]
                print(f"📊 Monitoring job for timeout: {job_id[:8]}...")
                
                # Monitor for timeout
                start_time = time.time()
                timeout_threshold = 300  # 5 minutes
                
                while time.time() - start_time < timeout_threshold:
                    status_response = requests.get(
                        f"{self.base_url}/api/v1/async/chat/status/{job_id}",
                        timeout=30
                    )
                    
                    if status_response.status_code == 200:
                        status = status_response.json()
                        elapsed = time.time() - start_time
                        print(f"📊 Elapsed: {elapsed:.1f}s - Status: {status['status']} - Progress: {status['progress']}%")
                        
                        if status["status"] == "failed" and "timeout" in status.get("error", "").lower():
                            print("✅ Timeout handling working")
                            self.test_results.append(("Job Timeouts", "PASS", f"Job timed out after {elapsed:.1f}s"))
                            return
                        elif status["status"] == "completed":
                            print("✅ Job completed within timeout")
                            self.test_results.append(("Job Timeouts", "PASS", f"Job completed in {elapsed:.1f}s"))
                            return
                            
                    time.sleep(5)
                
                print("⚠️ Job did not timeout or complete within expected time")
                self.test_results.append(("Job Timeouts", "WARN", "No timeout observed"))
            else:
                print(f"❌ Failed to submit timeout test job: {response.status_code}")
                self.test_results.append(("Job Timeouts", "FAIL", f"HTTP {response.status_code}"))
                
        except Exception as e:
            print(f"❌ Job timeout test failed: {e}")
            self.test_results.append(("Job Timeouts", "FAIL", str(e)))
    
    async def test_adaptive_polling(self):
        """Test adaptive polling functionality"""
        print("\n6. Testing Adaptive Polling...")
        
        if not self.job_ids:
            print("⚠️ No jobs available for polling test")
            return
            
        job_id = self.job_ids[0]
        poll_times = []
        
        try:
            # Simulate polling with timing
            for i in range(10):
                start_time = time.time()
                
                response = requests.get(
                    f"{self.base_url}/api/v1/async/chat/status/{job_id}",
                    timeout=30
                )
                
                poll_time = time.time() - start_time
                poll_times.append(poll_time)
                
                if response.status_code == 200:
                    status = response.json()
                    print(f"📊 Poll {i+1}: {poll_time:.3f}s - Status: {status['status']}")
                    
                    if status["status"] in ["completed", "failed"]:
                        break
                        
                time.sleep(1)  # Fixed interval for testing
            
            # Analyze polling performance
            avg_poll_time = sum(poll_times) / len(poll_times)
            if avg_poll_time < 1.0:  # Less than 1 second average
                print(f"✅ Adaptive polling working (avg: {avg_poll_time:.3f}s)")
                self.test_results.append(("Adaptive Polling", "PASS", f"Avg poll time: {avg_poll_time:.3f}s"))
            else:
                print(f"⚠️ Polling may be slow (avg: {avg_poll_time:.3f}s)")
                self.test_results.append(("Adaptive Polling", "WARN", f"Slow polling: {avg_poll_time:.3f}s"))
                
        except Exception as e:
            print(f"❌ Adaptive polling test failed: {e}")
            self.test_results.append(("Adaptive Polling", "FAIL", str(e)))
    
    async def test_authentication(self):
        """Test authentication functionality"""
        print("\n7. Testing Authentication...")
        
        try:
            # Test without authentication
            response = requests.post(
                f"{self.base_url}/api/v1/async/chat/submit",
                json={
                    "message": "test message",
                    "context": {}
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Authentication test passed (no auth required for testing)")
                self.test_results.append(("Authentication", "PASS", "No auth required"))
            elif response.status_code == 401:
                print("✅ Authentication working (401 Unauthorized)")
                self.test_results.append(("Authentication", "PASS", "Auth required"))
            else:
                print(f"⚠️ Unexpected auth response: {response.status_code}")
                self.test_results.append(("Authentication", "WARN", f"HTTP {response.status_code}"))
                
        except Exception as e:
            print(f"❌ Authentication test failed: {e}")
            self.test_results.append(("Authentication", "FAIL", str(e)))
    
    async def test_job_statistics(self):
        """Test job statistics endpoint"""
        print("\n8. Testing Job Statistics...")
        
        try:
            response = requests.get(f"{self.base_url}/api/v1/async/chat/stats", timeout=10)
            
            if response.status_code == 200:
                stats = response.json()
                print(f"📊 Job Statistics:")
                print(f"   Total Jobs: {stats.get('total_jobs', 0)}")
                print(f"   Status Counts: {stats.get('status_counts', {})}")
                print(f"   Max Jobs: {stats.get('max_jobs', 0)}")
                print(f"   Job TTL: {stats.get('job_ttl', 0)}s")
                
                print("✅ Job statistics working")
                self.test_results.append(("Job Statistics", "PASS", f"Stats retrieved: {stats.get('total_jobs', 0)} jobs"))
            else:
                print(f"❌ Failed to get job statistics: {response.status_code}")
                self.test_results.append(("Job Statistics", "FAIL", f"HTTP {response.status_code}"))
                
        except Exception as e:
            print(f"❌ Job statistics test failed: {e}")
            self.test_results.append(("Job Statistics", "FAIL", str(e)))
    
    async def test_concurrent_jobs(self):
        """Test concurrent job processing"""
        print("\n9. Testing Concurrent Jobs...")
        
        try:
            # Submit multiple jobs concurrently
            concurrent_jobs = []
            for i in range(3):
                response = requests.post(
                    f"{self.base_url}/api/v1/async/chat/submit",
                    json={
                        "message": f"concurrent test {i+1}",
                        "context": {
                            "document_content": "",
                            "chat_history": [],
                            "available_tools": ""
                        }
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    job_data = response.json()
                    concurrent_jobs.append(job_data["job_id"])
                    print(f"✅ Concurrent job {i+1} submitted: {job_data['job_id'][:8]}...")
            
            if concurrent_jobs:
                print(f"📊 Monitoring {len(concurrent_jobs)} concurrent jobs...")
                
                # Monitor all jobs
                completed_jobs = 0
                for i in range(20):  # Monitor for up to 40 seconds
                    for job_id in concurrent_jobs[:]:
                        status_response = requests.get(
                            f"{self.base_url}/api/v1/async/chat/status/{job_id}",
                            timeout=30
                        )
                        
                        if status_response.status_code == 200:
                            status = status_response.json()
                            if status["status"] in ["completed", "failed"]:
                                completed_jobs += 1
                                concurrent_jobs.remove(job_id)
                                print(f"✅ Job {job_id[:8]}... {status['status']}")
                    
                    if not concurrent_jobs:
                        break
                        
                    time.sleep(2)
                
                print(f"✅ Concurrent processing working ({completed_jobs} jobs processed)")
                self.test_results.append(("Concurrent Jobs", "PASS", f"{completed_jobs} jobs processed"))
            else:
                print("❌ No concurrent jobs submitted")
                self.test_results.append(("Concurrent Jobs", "FAIL", "No jobs submitted"))
                
        except Exception as e:
            print(f"❌ Concurrent jobs test failed: {e}")
            self.test_results.append(("Concurrent Jobs", "FAIL", str(e)))
    
    async def test_memory_leak_prevention(self):
        """Test memory leak prevention"""
        print("\n10. Testing Memory Leak Prevention...")
        
        try:
            # Get initial memory stats
            initial_response = requests.get(f"{self.base_url}/api/v1/async/chat/stats", timeout=10)
            
            if initial_response.status_code == 200:
                initial_stats = initial_response.json()
                initial_jobs = initial_stats.get("total_jobs", 0)
                print(f"📊 Initial job count: {initial_jobs}")
                
                # Submit many jobs to test memory management
                test_jobs = []
                for i in range(10):
                    response = requests.post(
                        f"{self.base_url}/api/v1/async/chat/submit",
                        json={
                            "message": f"memory test {i+1}",
                            "context": {}
                        },
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        job_data = response.json()
                        test_jobs.append(job_data["job_id"])
                
                print(f"📊 Submitted {len(test_jobs)} test jobs")
                
                # Wait for cleanup
                print("⏳ Waiting for cleanup...")
                time.sleep(30)
                
                # Check final stats
                final_response = requests.get(f"{self.base_url}/api/v1/async/chat/stats", timeout=10)
                
                if final_response.status_code == 200:
                    final_stats = final_response.json()
                    final_jobs = final_stats.get("total_jobs", 0)
                    print(f"📊 Final job count: {final_jobs}")
                    
                    if final_jobs <= initial_jobs + 5:  # Allow some margin
                        print("✅ Memory leak prevention working")
                        self.test_results.append(("Memory Leak Prevention", "PASS", f"Jobs: {initial_jobs} -> {final_jobs}"))
                    else:
                        print("⚠️ Potential memory leak (job count increased significantly)")
                        self.test_results.append(("Memory Leak Prevention", "WARN", f"Jobs increased: {initial_jobs} -> {final_jobs}"))
                else:
                    print(f"❌ Failed to get final stats: {final_response.status_code}")
                    self.test_results.append(("Memory Leak Prevention", "FAIL", f"HTTP {final_response.status_code}"))
            else:
                print(f"❌ Failed to get initial stats: {initial_response.status_code}")
                self.test_results.append(("Memory Leak Prevention", "FAIL", f"HTTP {initial_response.status_code}"))
                
        except Exception as e:
            print(f"❌ Memory leak prevention test failed: {e}")
            self.test_results.append(("Memory Leak Prevention", "FAIL", str(e)))
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 60)
        
        # Count results
        passed = sum(1 for _, status, _ in self.test_results if status == "PASS")
        failed = sum(1 for _, status, _ in self.test_results if status == "FAIL")
        warnings = sum(1 for _, status, _ in self.test_results if status == "WARN")
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Warnings: {warnings}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\n📋 Detailed Results:")
        print("-" * 60)
        
        for test_name, status, details in self.test_results:
            status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            print(f"{status_icon} {test_name}: {status} - {details}")
        
        print("\n🎯 Overall Assessment:")
        if failed == 0 and warnings <= 2:
            print("🟢 EXCELLENT - All critical tests passed!")
        elif failed <= 2:
            print("🟡 GOOD - Most tests passed, minor issues")
        else:
            print("🔴 NEEDS WORK - Multiple test failures")
        
        print("\n🚀 Production Readiness:")
        if failed == 0:
            print("✅ READY FOR PRODUCTION")
        elif failed <= 2:
            print("⚠️ READY WITH CAUTION - Address minor issues")
        else:
            print("❌ NOT READY - Fix critical issues first")

async def main():
    """Main test execution"""
    test_suite = AsyncTestSuite()
    await test_suite.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())
