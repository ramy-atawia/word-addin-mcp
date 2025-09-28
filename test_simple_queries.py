#!/usr/bin/env python3
"""
Focused test for simple queries to measure empty response rate accurately.
Tests only basic conversational inputs that should work.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Simple test inputs that should work
SIMPLE_INPUTS = [
    "Hello", "Hi there", "Good morning", "Good evening", "Hey",
    "How are you?", "What's up?", "Nice to meet you", "Thank you", "You're welcome",
    "Yes", "No", "Maybe", "Sure", "Of course",
    "Help me", "Can you help?", "I need assistance", "What can you do?", "Tell me about yourself",
    "What is AI?", "Explain technology", "How does this work?", "What should I know?", "Give me advice",
    "Write a sentence", "Create a list", "Make a summary", "Generate text", "Produce content",
    "Hello world", "Test message", "Sample input", "Basic query", "Simple request",
    "Tell me a joke", "Share a fact", "Give an example", "Show me something", "Demonstrate this",
    "I'm confused", "I don't understand", "Can you clarify?", "What do you mean?", "Please explain",
    "That's interesting", "I agree", "I disagree", "Good point", "Well said",
    "Keep going", "Continue", "More please", "Tell me more", "Elaborate",
    "Stop", "Enough", "That's all", "No more", "Thank you"
]

def test_single_input(message: str, test_number: int) -> Dict[str, Any]:
    """Test a single input and return results."""
    print(f"Test {test_number:2d}/50: '{message}'")
    
    try:
        # Submit the request
        response = requests.post(
            "http://localhost:9000/api/v1/async/chat/submit",
            json={
                "message": message,
                "context": {},
                "session_id": f"simple-test-{test_number}"
            },
            timeout=15
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
    """Run the focused simple query test."""
    print("🧪 Starting Simple Query Empty Response Test")
    print("=" * 60)
    print(f"Testing {len(SIMPLE_INPUTS)} simple conversational inputs...")
    print(f"Backend URL: http://localhost:9000")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = []
    empty_responses = 0
    errors = 0
    successful_responses = 0
    
    for i, input_text in enumerate(SIMPLE_INPUTS, 1):
        result = test_single_input(input_text, i)
        results.append(result)
        
        if result["is_empty"]:
            empty_responses += 1
            print(f"❌ EMPTY: '{result['input']}' -> {result['status']} ({result['error'] or 'No error'})")
        elif result["status"] == "completed":
            successful_responses += 1
            print(f"✅ OK: '{result['input']}' -> {result['response_length']} chars")
        else:
            errors += 1
            print(f"⚠️  ERROR: '{result['input']}' -> {result['error']}")
        
        # Small delay between requests
        time.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SIMPLE QUERY TEST RESULTS")
    print("=" * 60)
    print(f"Total tests: {len(SIMPLE_INPUTS)}")
    print(f"Successful responses: {successful_responses}")
    print(f"Empty responses: {empty_responses}")
    print(f"Errors: {errors}")
    print(f"Empty response rate: {(empty_responses / len(SIMPLE_INPUTS)) * 100:.1f}%")
    print(f"Success rate: {(successful_responses / len(SIMPLE_INPUTS)) * 100:.1f}%")
    
    # Detailed empty response analysis
    if empty_responses > 0:
        print("\n🔍 EMPTY RESPONSE ANALYSIS:")
        print("-" * 40)
        for result in results:
            if result["is_empty"]:
                print(f"Test {result['test_number']:2d}: '{result['input']}' -> {result['status']} ({result['error'] or 'No error'})")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"simple_query_test_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump({
            "test_summary": {
                "total_tests": len(SIMPLE_INPUTS),
                "successful_responses": successful_responses,
                "empty_responses": empty_responses,
                "errors": errors,
                "empty_response_rate": (empty_responses / len(SIMPLE_INPUTS)) * 100,
                "success_rate": (successful_responses / len(SIMPLE_INPUTS)) * 100,
                "timestamp": datetime.now().isoformat()
            },
            "detailed_results": results
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {filename}")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
