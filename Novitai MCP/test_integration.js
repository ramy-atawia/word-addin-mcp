#!/usr/bin/env node

/**
 * Simple test script to verify backend integration
 * Run this to test if the backend endpoints are working
 */

const axios = require('axios');

const BASE_URL = 'https://localhost:9000';

async function testBackendIntegration() {
  console.log('🧪 Testing Backend Integration...\n');

  try {
    // Test 1: Health Check
    console.log('1️⃣ Testing Health Check...');
    const healthResponse = await axios.get(`${BASE_URL}/health/`);
    console.log('✅ Health Check:', healthResponse.status, healthResponse.data);
    console.log('');

    // Test 2: MCP Tools
    console.log('2️⃣ Testing MCP Tools...');
    const toolsResponse = await axios.get(`${BASE_URL}/api/v1/mcp/tools`);
    console.log('✅ MCP Tools:', toolsResponse.status, `Found ${toolsResponse.data.tools?.length || 0} tools`);
    console.log('');

    // Test 3: Conversation API
    console.log('3️⃣ Testing Conversation API...');
    const conversationResponse = await axios.post(`${BASE_URL}/api/v1/mcp/conversation`, {
      message: 'Hello, how are you?',
      context: 'general',
      session_id: 'test-session-123',
      user_id: 'test-user-456'
    });
    console.log('✅ Conversation API:', conversationResponse.status);
    console.log('   Response:', conversationResponse.data.response?.substring(0, 100) + '...');
    console.log('');

    // Test 4: Agent Intent Detection
    console.log('4️⃣ Testing Agent Intent Detection...');
    const intentResponse = await axios.post(`${BASE_URL}/api/v1/mcp/agent/intent`, {
      message: 'Help me analyze a document',
      conversation_history: [],
      document_content: '',
      available_tools: ['document_analyzer', 'text_processor']
    });
    console.log('✅ Agent Intent:', intentResponse.status);
    console.log('   Intent Type:', intentResponse.data.intent_type);
    console.log('   Routing Decision:', intentResponse.data.routing_decision);
    console.log('');

    console.log('🎉 All tests passed! Backend integration is working correctly.');
    console.log('');
    console.log('Next steps:');
    console.log('1. Start the frontend development server: npm run dev-server');
    console.log('2. Sideload the Word Add-in: npm start');
    console.log('3. Test the chat interface in Word');

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    
    if (error.response) {
      console.error('   Status:', error.response.status);
      console.error('   Data:', error.response.data);
    }
    
    console.log('');
    console.log('🔧 Troubleshooting:');
    console.log('1. Make sure the backend server is running on https://localhost:9000');
    console.log('2. Check if the backend server is accessible');
    console.log('3. Verify the API endpoints are properly configured');
    console.log('4. Check backend server logs for errors');
    
    process.exit(1);
  }
}

// Run the test
testBackendIntegration();
