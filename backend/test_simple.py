#!/usr/bin/env python3
"""
Simple test script to verify the backend can start
"""
import os
import sys
import json

# Add the app directory to the path
sys.path.insert(0, '/app')

def test_imports():
    """Test if we can import the main modules"""
    try:
        from app.main import app
        print("✅ Successfully imported app.main")
        return True
    except Exception as e:
        print(f"❌ Failed to import app.main: {e}")
        return False

def test_config():
    """Test if we can load configuration"""
    try:
        from app.core.config import Settings
        settings = Settings()
        print("✅ Successfully loaded configuration")
        print(f"   - ALLOWED_ORIGINS: {settings.allowed_origins}")
        print(f"   - PORT: {os.getenv('PORT', '9000')}")
        return True
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False

def test_environment():
    """Test environment variables"""
    print("🔍 Environment variables:")
    for key in ['PORT', 'ALLOWED_ORIGINS', 'ALLOWED_HOSTS', 'AZURE_OPENAI_API_KEY']:
        value = os.getenv(key, 'NOT_SET')
        if 'API_KEY' in key:
            value = value[:10] + '...' if len(value) > 10 else value
        print(f"   - {key}: {value}")

if __name__ == "__main__":
    print("🚀 Testing backend startup...")
    test_environment()
    
    if test_imports() and test_config():
        print("✅ All tests passed! Backend should start successfully.")
        sys.exit(0)
    else:
        print("❌ Tests failed! Backend will not start.")
        sys.exit(1)
