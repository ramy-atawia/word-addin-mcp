#!/usr/bin/env python3
"""
Test script for async implementation
"""
import asyncio
import requests
import json
import time

# Test configuration
BASE_URL = "http://localhost:9000"
TEST_MESSAGE = "prior art search 5g ai"

async def test_async_implementation():
    """Test the async chat implementation"""
    print("🧪 Testing Async Chat Implementation")
    print("=" * 50)
    
    # Test 1: Submit async job
    print("\n1. Submitting async job...")
    submit_data = {
        "message": TEST_MESSAGE,
        "context": {
            "document_content": "",
            "chat_history": [],
            "available_tools": ""
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/async/chat/submit",
            json=submit_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data["job_id"]
            print(f"✅ Job submitted successfully: {job_id}")
        else:
            print(f"❌ Failed to submit job: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error submitting job: {e}")
        return
    
    # Test 2: Poll for status updates
    print(f"\n2. Polling job status for: {job_id}")
    max_attempts = 30  # 1 minute max
    attempt = 0
    
    while attempt < max_attempts:
        try:
            status_response = requests.get(
                f"{BASE_URL}/api/v1/async/chat/status/{job_id}",
                timeout=5
            )
            
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"📊 Status: {status['status']} - Progress: {status['progress']}%")
                
                if status["status"] == "completed":
                    print("✅ Job completed!")
                    break
                elif status["status"] == "failed":
                    print(f"❌ Job failed: {status.get('error', 'Unknown error')}")
                    return
                elif status["status"] == "cancelled":
                    print("⚠️ Job was cancelled")
                    return
            else:
                print(f"❌ Failed to get status: {status_response.status_code}")
                break
                
        except Exception as e:
            print(f"❌ Error getting status: {e}")
            break
        
        attempt += 1
        time.sleep(2)  # Wait 2 seconds between polls
    
    if attempt >= max_attempts:
        print("⏰ Timeout waiting for job completion")
        return
    
    # Test 3: Get job result
    print(f"\n3. Getting job result...")
    try:
        result_response = requests.get(
            f"{BASE_URL}/api/v1/async/chat/result/{job_id}",
            timeout=10
        )
        
        if result_response.status_code == 200:
            result = result_response.json()
            print("✅ Job result retrieved successfully")
            print(f"📄 Result type: {result.get('result', {}).get('type', 'unknown')}")
            print(f"📄 Result length: {len(str(result.get('result', {})))} characters")
        else:
            print(f"❌ Failed to get result: {result_response.status_code}")
    except Exception as e:
        print(f"❌ Error getting result: {e}")
    
    print("\n🎉 Async implementation test completed!")

if __name__ == "__main__":
    asyncio.run(test_async_implementation())
