#!/usr/bin/env python3
"""
Test script to verify backend authentication is working correctly.
"""

import requests
import json
import time

def test_backend_auth():
    """Test backend authentication endpoints."""
    
    base_url = "http://localhost:9000"
    
    print("🔍 Testing Backend Authentication...")
    print("=" * 50)
    
    # Test 1: Health endpoint (should work without auth)
    print("\n1. Testing health endpoint (no auth required)...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Health endpoint accessible")
        else:
            print("   ❌ Health endpoint failed")
    except Exception as e:
        print(f"   ❌ Health endpoint error: {e}")
    
    # Test 2: Root endpoint (should work without auth)
    print("\n2. Testing root endpoint (no auth required)...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Root endpoint accessible")
        else:
            print("   ❌ Root endpoint failed")
    except Exception as e:
        print(f"   ❌ Root endpoint error: {e}")
    
    # Test 3: MCP tools endpoint (should require auth now)
    print("\n3. Testing MCP tools endpoint (auth required)...")
    try:
        response = requests.get(f"{base_url}/api/v1/mcp/tools", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ MCP tools endpoint properly protected (401 Unauthorized)")
        elif response.status_code == 200:
            print("   ❌ MCP tools endpoint should require auth but returned 200")
        else:
            print(f"   ⚠️  MCP tools endpoint returned unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ MCP tools endpoint error: {e}")
    
    # Test 4: Agent chat endpoint (should require auth now)
    print("\n4. Testing agent chat endpoint (auth required)...")
    try:
        response = requests.post(
            f"{base_url}/api/v1/mcp/agent/chat",
            json={"message": "test", "context": {}},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Agent chat endpoint properly protected (401 Unauthorized)")
        elif response.status_code == 200:
            print("   ❌ Agent chat endpoint should require auth but returned 200")
        else:
            print(f"   ⚠️  Agent chat endpoint returned unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Agent chat endpoint error: {e}")
    
    # Test 5: Agent chat streaming endpoint (should require auth now)
    print("\n5. Testing agent chat streaming endpoint (auth required)...")
    try:
        response = requests.post(
            f"{base_url}/api/v1/mcp/agent/chat/stream",
            json={"message": "test", "context": {}},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Agent chat streaming endpoint properly protected (401 Unauthorized)")
        elif response.status_code == 200:
            print("   ❌ Agent chat streaming endpoint should require auth but returned 200")
        else:
            print(f"   ⚠️  Agent chat streaming endpoint returned unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Agent chat streaming endpoint error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Authentication Test Summary:")
    print("   - Health endpoints should be accessible (200)")
    print("   - Core endpoints should require authentication (401)")
    print("   - This verifies the security fix is working correctly")

if __name__ == "__main__":
    test_backend_auth()
