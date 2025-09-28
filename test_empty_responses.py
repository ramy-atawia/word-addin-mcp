#!/usr/bin/env python3
"""
Test script to check for empty responses across 50 different inputs.
Tests the local Docker backend to detect empty response patterns.
"""

import requests
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Any

# Test inputs covering different types of requests
TEST_INPUTS = [
    # Simple greetings
    "Hello", "Hi there", "Good morning", "Good evening", "Hey",
    
    # Patent-related queries
    "web search ramy atawia", "prior art search 5g", "patent search AI",
    "Draft 3 system claims", "patent analysis machine learning",
    "web search mohamed salah", "prior art search blockchain",
    "patent search quantum computing", "Draft 5 method claims",
    
    # Technical questions
    "What is artificial intelligence?", "Explain machine learning",
    "How does blockchain work?", "What is quantum computing?",
    "Explain neural networks", "What is deep learning?",
    "How does 5G work?", "What is cloud computing?",
    
    # Document requests
    "Create a technical report", "Write a summary", "Generate documentation",
    "Draft a proposal", "Create a presentation", "Write an analysis",
    "Generate a report", "Create a document", "Write a brief",
    
    # Short inputs (potential empty response triggers)
    "?", "!", "...", "ok", "yes", "no", "test", "help", "info",
    
    # Edge cases
    "", "   ", "\n", "\t", "a", "1", "123", "abc", "xyz",
    
    # Complex queries
    "Analyze the patent landscape for autonomous vehicles and provide recommendations",
    "Create a comprehensive technical specification for a mobile application",
    "Generate a detailed market analysis report for renewable energy technologies",
    "Draft a patent application for a novel machine learning algorithm",
    "Write a technical white paper on quantum cryptography implementation",
    
    # Mixed content
    "Hello! Can you help me with patent research?", "Hi, I need technical writing assistance",
    "Good morning! Please analyze this data", "Hey there, create a report for me",
    "Hello, can you draft some claims?", "Hi, I need help with documentation"
]

def test_single_input(message: str, test_number: int) -> Dict[str, Any]:
    """Test a single input and return results."""
    print(f"Test {test_number:2d}/50: '{message[:30]}{'...' if len(message) > 30 else ''}'")
    
    try:
        # Submit the request
        response = requests.post(
            "http://localhost:9000/api/v1/async/chat/submit",
            json={
                "message": message,
                "context": {},
                "session_id": f"test-session-{test_number}"
            },
            timeout=10
        )
        
        if response.status_code != 200:
            return {
                "test_number": test_number,
                "input": message,
                "status": "error",
                "error": f"HTTP {response.status_code}",
                "response": None,
                "is_empty": True,
                "response_length": 0
            }
        
        job_data = response.json()
        job_id = job_data.get("job_id")
        
        if not job_id:
            return {
                "test_number": test_number,
                "input": message,
                "status": "error",
                "error": "No job ID returned",
                "response": None,
                "is_empty": True,
                "response_length": 0
            }
        
        # Wait for completion (max 30 seconds)
        max_wait = 30
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = requests.get(
                f"http://localhost:9000/api/v1/async/chat/status/{job_id}",
                timeout=5
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get("status")
                
                if status == "completed":
                    # Get the result
                    result_response = requests.get(
                        f"http://localhost:9000/api/v1/async/chat/result/{job_id}",
                        timeout=5
                    )
                    
                    if result_response.status_code == 200:
                        result_data = result_response.json()
                        response_text = result_data.get("response", "")
                        
                        # Check if response is empty
                        is_empty = not response_text or response_text.strip() == ""
                        response_length = len(response_text.strip()) if response_text else 0
                        
                        return {
                            "test_number": test_number,
                            "input": message,
                            "status": "completed",
                            "error": None,
                            "response": response_text,
                            "is_empty": is_empty,
                            "response_length": response_length,
                            "execution_time": result_data.get("execution_time", 0)
                        }
                    else:
                        return {
                            "test_number": test_number,
                            "input": message,
                            "status": "error",
                            "error": f"Failed to get result: HTTP {result_response.status_code}",
                            "response": None,
                            "is_empty": True,
                            "response_length": 0
                        }
                elif status == "failed":
                    return {
                        "test_number": test_number,
                        "input": message,
                        "status": "failed",
                        "error": status_data.get("error", "Unknown error"),
                        "response": None,
                        "is_empty": True,
                        "response_length": 0
                    }
            
            time.sleep(1)  # Wait 1 second before checking again
        
        # Timeout
        return {
            "test_number": test_number,
            "input": message,
            "status": "timeout",
            "error": "Request timed out",
            "response": None,
            "is_empty": True,
            "response_length": 0
        }
        
    except Exception as e:
        return {
            "test_number": test_number,
            "input": message,
            "status": "exception",
            "error": str(e),
            "response": None,
            "is_empty": True,
            "response_length": 0
        }

def main():
    """Run the comprehensive test."""
    print("🧪 Starting Empty Response Detection Test")
    print("=" * 60)
    print(f"Testing {len(TEST_INPUTS)} different inputs...")
    print(f"Backend URL: http://localhost:9000")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = []
    empty_responses = 0
    errors = 0
    
    for i, input_text in enumerate(TEST_INPUTS, 1):
        result = test_single_input(input_text, i)
        results.append(result)
        
        if result["is_empty"]:
            empty_responses += 1
            print(f"❌ EMPTY: '{result['input'][:30]}{'...' if len(result['input']) > 30 else ''}'")
        elif result["status"] == "completed":
            print(f"✅ OK: '{result['input'][:30]}{'...' if len(result['input']) > 30 else ''}' -> {result['response_length']} chars")
        else:
            errors += 1
            print(f"⚠️  ERROR: '{result['input'][:30]}{'...' if len(result['input']) > 30 else ''}' -> {result['error']}")
        
        # Small delay between requests
        time.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total tests: {len(TEST_INPUTS)}")
    print(f"Successful responses: {len(TEST_INPUTS) - empty_responses - errors}")
    print(f"Empty responses: {empty_responses}")
    print(f"Errors: {errors}")
    print(f"Empty response rate: {(empty_responses / len(TEST_INPUTS)) * 100:.1f}%")
    print(f"Success rate: {((len(TEST_INPUTS) - empty_responses - errors) / len(TEST_INPUTS)) * 100:.1f}%")
    
    # Detailed empty response analysis
    if empty_responses > 0:
        print("\n🔍 EMPTY RESPONSE ANALYSIS:")
        print("-" * 40)
        for result in results:
            if result["is_empty"]:
                print(f"Test {result['test_number']:2d}: '{result['input']}' -> {result['status']} ({result['error'] or 'No error'})")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"empty_response_test_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump({
            "test_summary": {
                "total_tests": len(TEST_INPUTS),
                "successful_responses": len(TEST_INPUTS) - empty_responses - errors,
                "empty_responses": empty_responses,
                "errors": errors,
                "empty_response_rate": (empty_responses / len(TEST_INPUTS)) * 100,
                "success_rate": ((len(TEST_INPUTS) - empty_responses - errors) / len(TEST_INPUTS)) * 100,
                "timestamp": datetime.now().isoformat()
            },
            "detailed_results": results
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {filename}")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
