#!/usr/bin/env python3
"""
Azure Log Checker - Simple tool to test the enhanced error reporting
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime

class AzureLogChecker:
    def __init__(self, base_url: str = "https://novitai-word-mcp-backend-dev.azurewebsites.net"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_enhanced_error_reporting(self):
        """Test the enhanced error reporting by triggering a fallback response"""
        print("🔍 Testing Enhanced Error Reporting")
        print("=" * 50)
        
        # Test with a request that might trigger the fallback
        test_message = "hi"
        
        try:
            print(f"📤 Sending test message: '{test_message}'")
            start_time = time.time()
            
            # Submit job
            submit_url = f"{self.base_url}/api/v1/async/chat/submit"
            payload = {
                "message": test_message,
                "context": {
                    "test": True,
                    "timestamp": datetime.now().isoformat(),
                    "purpose": "error_reporting_test"
                },
                "job_type": "general_chat"
            }
            
            async with self.session.post(submit_url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"❌ Submit failed: HTTP {response.status} - {error_text}")
                    return
                
                data = await response.json()
                job_id = data.get('job_id')
                
                if not job_id:
                    print("❌ No job ID returned")
                    return
                
                print(f"✅ Job submitted: {job_id}")
                
                # Poll for completion
                result = await self._poll_job(job_id)
                duration = time.time() - start_time
                
                print(f"⏱️  Total duration: {duration:.2f}s")
                print(f"✅ Success: {result.get('success', False)}")
                
                if result.get('success'):
                    response_text = result.get('response', '')
                    print(f"📝 Response: {response_text}")
                    
                    # Check if it's a fallback response with error details
                    if "Error:" in response_text and " - " in response_text:
                        print("🎯 ENHANCED ERROR REPORTING DETECTED!")
                        print("   The response now includes error codes and detailed information")
                    elif "I apologize, but I'm having trouble" in response_text:
                        print("⚠️  FALLBACK RESPONSE DETECTED (but no error details)")
                    else:
                        print("✅ NORMAL RESPONSE")
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")
                    
                    # Check if we have detailed error information
                    if 'error_code' in result:
                        print(f"🔍 Error Code: {result.get('error_code')}")
                    if 'error_details' in result:
                        print(f"🔍 Error Details: {result.get('error_details')}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    async def _poll_job(self, job_id: str, max_polls: int = 30):
        """Poll job for completion"""
        for i in range(max_polls):
            try:
                status_url = f"{self.base_url}/api/v1/async/chat/status/{job_id}"
                async with self.session.get(status_url) as response:
                    if response.status != 200:
                        return {
                            "success": False,
                            "error": f"Status check failed: HTTP {response.status}"
                        }
                    
                    data = await response.json()
                    status = data.get('status')
                    
                    if status in ['completed', 'failed', 'cancelled']:
                        if status == 'completed':
                            # Get the result
                            result_url = f"{self.base_url}/api/v1/async/chat/result/{job_id}"
                            async with self.session.get(result_url) as result_response:
                                if result_response.status == 200:
                                    result_data = await result_response.json()
                                    return {
                                        "success": True,
                                        "response": result_data.get('response', 'No response'),
                                        "error_code": result_data.get('error_code'),
                                        "error_details": result_data.get('error_details')
                                    }
                                else:
                                    return {
                                        "success": False,
                                        "error": f"Failed to get result: HTTP {result_response.status}"
                                    }
                        else:
                            error_msg = data.get('error', 'Unknown error')
                            return {
                                "success": False,
                                "error": f"Job {status}: {error_msg}",
                                "error_code": data.get('error_code'),
                                "error_details": data.get('error_details')
                            }
                    
                    await asyncio.sleep(1)
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Polling error: {str(e)}"
                }
        
        return {
            "success": False,
            "error": "Job timed out"
        }

async def main():
    """Run the Azure log checker"""
    async with AzureLogChecker() as checker:
        await checker.test_enhanced_error_reporting()

if __name__ == "__main__":
    asyncio.run(main())
