#!/bin/bash

# Check .env file for required API keys
echo "🔍 Checking .env file for required API keys..."

if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create a .env file with your API keys."
    exit 1
fi

# Load .env file
export $(grep -v '^#' .env | xargs)

# Check required keys
missing_keys=()

if [ -z "$AZURE_OPENAI_API_KEY" ]; then
    missing_keys+=("AZURE_OPENAI_API_KEY")
fi

if [ -z "$AZURE_OPENAI_ENDPOINT" ]; then
    missing_keys+=("AZURE_OPENAI_ENDPOINT")
fi

if [ -z "$AZURE_OPENAI_DEPLOYMENT_NAME" ]; then
    missing_keys+=("AZURE_OPENAI_DEPLOYMENT_NAME")
fi

if [ -z "$GOOGLE_API_KEY" ]; then
    missing_keys+=("GOOGLE_API_KEY")
fi

if [ -z "$GOOGLE_CSE_ID" ]; then
    missing_keys+=("GOOGLE_CSE_ID")
fi

if [ -z "$PATENTSVIEW_API_KEY" ]; then
    missing_keys+=("PATENTSVIEW_API_KEY")
fi

# Report results
if [ ${#missing_keys[@]} -eq 0 ]; then
    echo "✅ All required API keys found in .env file!"
    echo ""
    echo "📋 Found keys:"
    echo "   - AZURE_OPENAI_API_KEY: ${AZURE_OPENAI_API_KEY:0:10}..."
    echo "   - AZURE_OPENAI_ENDPOINT: $AZURE_OPENAI_ENDPOINT"
    echo "   - AZURE_OPENAI_DEPLOYMENT_NAME: $AZURE_OPENAI_DEPLOYMENT_NAME"
    echo "   - GOOGLE_API_KEY: ${GOOGLE_API_KEY:0:10}..."
    echo "   - GOOGLE_CSE_ID: $GOOGLE_CSE_ID"
    echo "   - PATENTSVIEW_API_KEY: ${PATENTSVIEW_API_KEY:0:10}..."
    echo ""
    echo "🚀 Ready to deploy to Azure!"
else
    echo "❌ Missing required API keys:"
    for key in "${missing_keys[@]}"; do
        echo "   - $key"
    done
    echo ""
    echo "Please add these keys to your .env file and try again."
    exit 1
fi
