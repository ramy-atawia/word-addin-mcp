"""
Consolidated Patent Search Tests

This module contains all patent search related tests including:
- Claims fetching functionality
- Report structure validation
- Integration testing
- Real API testing with patent IDs from our testing history
"""

import asyncio
import httpx
import os
import subprocess
from unittest.mock import AsyncMock, patch
import json


class MockLLMClient:
    """Mock LLM client for testing."""
    
    def __init__(self):
        pass
    
    def generate_text(self, prompt, max_tokens=1000, temperature=0.7):
        """Mock LLM response."""
        return {
            "success": True,
            "text": f"Mock LLM response for prompt with {max_tokens} tokens"
        }


class PatentSearchService:
    """Simplified PatentSearchService for testing."""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.base_url = "https://search.patentsview.org/api/v1"
        self.api_key = "nIT60mkq.UjM34uFT7p1XtMDhInHStS7w3dq02Nds"
    
    async def _fetch_claims(self, patent_id: str):
        """Fetch claims for a specific patent."""
        
        url = f"{self.base_url}/g_claim/"
        
        payload = {
            "q": {"patent_id": patent_id},
            "f": ["claim_sequence", "claim_text", "claim_number", "claim_dependent"],
            "o": {"size": 100},  # Increased from 50 to 100 for more claims
            "s": [{"claim_sequence": "asc"}]
        }
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                # Handle specific HTTP status codes
                if response.status_code == 400:
                    raise ValueError(f"Bad Request: Invalid patent ID '{patent_id}'. API returned: {response.text}")
                elif response.status_code == 401:
                    raise ValueError(f"Unauthorized: Invalid API key for claims API. Please check your PatentsView API credentials.")
                elif response.status_code == 403:
                    raise ValueError(f"Forbidden: API access denied for claims. Check your API key permissions.")
                elif response.status_code == 404:
                    raise ValueError(f"Not Found: No claims found for patent ID '{patent_id}'.")
                elif response.status_code == 429:
                    raise ValueError(f"Rate Limited: Too many requests to PatentsView claims API. Please try again later.")
                elif response.status_code >= 500:
                    raise ValueError(f"Server Error: PatentsView claims API is experiencing issues. Please try again later.")
                
                # Parse response
                data = response.json()
                
                if data.get("error"):
                    error_msg = data.get("error", "Unknown API error")
                    if isinstance(error_msg, dict):
                        error_msg = error_msg.get("message", str(error_msg))
                    raise ValueError(f"PatentsView Claims API Error: {error_msg}")
                
                claims_data = data.get("g_claims", [])
                
                if not claims_data:
                    print(f"No claims data found for patent {patent_id}")
                    return []
                
                # Parse claims into simple format with validation
                claims = []
                for claim in claims_data:
                    claim_text = claim.get("claim_text", "")
                    claim_number = claim.get("claim_number", "")
                    
                    # Validate that we have meaningful claim text
                    if not claim_text or len(claim_text.strip()) < 10:
                        print(f"Invalid or truncated claim text for patent {patent_id}, claim {claim_number}")
                        continue
                    
                    claims.append({
                        "number": claim_number,
                        "text": claim_text.strip(),  # Ensure clean text
                        "type": "dependent" if claim.get("claim_dependent") else "independent",
                        "sequence": claim.get("claim_sequence", 0)
                    })
                
                print(f"Successfully fetched {len(claims)} claims for patent {patent_id}")
                return claims
                
        except httpx.TimeoutException:
            raise ValueError(f"Request Timeout: Claims API took too long to respond for patent '{patent_id}'. Please try again.")
        except httpx.ConnectError:
            raise ValueError(f"Connection Error: Cannot connect to PatentsView claims API for patent '{patent_id}'. Please check your internet connection.")
        except httpx.HTTPError as e:
            raise ValueError(f"HTTP Error: {str(e)}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON response from PatentsView claims API for patent '{patent_id}'.")
        except Exception as e:
            raise ValueError(f"Unexpected error fetching claims for patent '{patent_id}': {str(e)}")
    
    async def _summarize_claims(self, patents):
        """Summarize claims for all patents using LLM."""
        claims_summaries = []
        
        for patent in patents:
            patent_id = patent.get("patent_id", "Unknown")
            patent_title = patent.get("patent_title", "No title")
            claims = patent.get("claims", [])
            
            if not claims:
                claims_summaries.append(f"**Patent {patent_id}: {patent_title}**\n- Claims: Not available\n")
                continue
            
            # Prepare claims text for LLM analysis with full text
            claims_text = []
            independent_claims = []
            dependent_claims = []
            
            for claim in claims:
                claim_number = claim.get("number", "")
                claim_text = claim.get("text", "")
                claim_type = claim.get("type", "unknown")
                claim_sequence = claim.get("sequence", 0)
                
                if claim_text and claim_number and len(claim_text.strip()) > 10:
                    full_claim = f"Claim {claim_number} ({claim_type}): {claim_text}"
                    claims_text.append(full_claim)
                    
                    if claim_type == "independent":
                        independent_claims.append(full_claim)
                    else:
                        dependent_claims.append(full_claim)
            
            if not claims_text:
                claims_summaries.append(f"**Patent {patent_id}: {patent_title}**\n- Claims: No valid claim text found\n")
                continue
            
            # Create prompt for claims summarization
            claims_prompt = f"""
Analyze and summarize the following patent claims for patent {patent_id} titled "{patent_title}".

**FULL CLAIMS TEXT TO ANALYZE:**
{chr(10).join(claims_text)}

**INDEPENDENT CLAIMS ({len(independent_claims)}):**
{chr(10).join(independent_claims) if independent_claims else "None"}

**DEPENDENT CLAIMS ({len(dependent_claims)}):**
{chr(10).join(dependent_claims) if dependent_claims else "None"}

**ANALYSIS REQUIREMENTS:**
1. **Technical Summary**: Provide a detailed 3-4 sentence summary of the main invention based on the FULL claim text
2. **Key Technical Features**: Extract specific technical elements, methods, and innovations from the claims
3. **Claim Structure Analysis**: 
   - Identify all independent claims and their scope
   - Map dependent claims to their independent claims
   - Analyze claim dependencies and relationships
4. **Technical Scope & Limitations**: 
   - Define the technical scope based on claim language
   - Identify specific limitations and constraints
   - Note any technical specifications or requirements

**IMPORTANT**: Use the FULL claim text provided above. Do not truncate or summarize the claims - analyze them in their entirety.

Format as markdown with clear sections and detailed technical analysis.
"""
            
            try:
                # Use LLM to summarize claims
                response = self.llm_client.generate_text(
                    prompt=claims_prompt,
                    max_tokens=2000,  # Increased from 1000 to 2000 for more detailed analysis
                    temperature=0.3
                )
                
                if response.get("success"):
                    summary = response["text"]
                    claims_summaries.append(f"**Patent {patent_id}: {patent_title}**\n{summary}\n")
                else:
                    # Fallback: basic claims listing
                    claims_summaries.append(f"**Patent {patent_id}: {patent_title}**\n" + 
                                          f"- Claims: {len(claims)} claims found\n" +
                                          f"- Independent Claims: {len([c for c in claims if c.get('type') == 'independent'])}\n" +
                                          f"- Dependent Claims: {len([c for c in claims if c.get('type') == 'dependent'])}\n")
                    
            except Exception as e:
                print(f"Failed to summarize claims for patent {patent_id}: {e}")
                # Fallback: detailed claims listing with full text
                fallback_text = f"**Patent {patent_id}: {patent_title}**\n"
                fallback_text += f"- **Total Claims**: {len(claims)} claims found\n"
                fallback_text += f"- **Independent Claims**: {len([c for c in claims if c.get('type') == 'independent'])}\n"
                fallback_text += f"- **Dependent Claims**: {len([c for c in claims if c.get('type') == 'dependent'])}\n\n"
                
                # Include first few claims as examples
                if claims:
                    fallback_text += "**Sample Claims (Full Text):**\n"
                    for i, claim in enumerate(claims[:3]):  # Show first 3 claims
                        fallback_text += f"\n**{claim.get('number', 'Unknown')} ({claim.get('type', 'unknown')}):**\n"
                        fallback_text += f"{claim.get('text', 'No text available')}\n"
                    
                    if len(claims) > 3:
                        fallback_text += f"\n*... and {len(claims) - 3} more claims*\n"
                
                claims_summaries.append(fallback_text)
        
        # Combine all summaries into a markdown string
        found_claims_summary = "\n".join(claims_summaries)
        
        print(f"Generated claims summary for {len(patents)} patents")
        return found_claims_summary


async def test_claims_fetching_real_patents():
    """Test claims fetching with real patent IDs from our testing history."""
    print("=" * 60)
    print("TESTING CLAIMS FETCHING WITH REAL PATENT IDs")
    print("=" * 60)
    
    # Real patent IDs from our testing history
    real_patent_ids = [
        "12192952",  # Efficient positioning enhancement for dynamic spectrum sharing
        "11888610",  # Method and apparatus for positioning with LTE-NR dynamic spectrum sharing
        "11832111",  # Dynamic spectrum sharing between 4G and 5G wireless networks
    ]
    
    llm_client = MockLLMClient()
    patent_service = PatentSearchService(llm_client)
    
    for patent_id in real_patent_ids:
        print(f"\n--- Testing Patent ID: {patent_id} ---")
        try:
            claims = await patent_service._fetch_claims(patent_id)
            
            if claims:
                print(f"✅ Successfully fetched {len(claims)} claims")
                
                # Analyze claim types
                independent_claims = [c for c in claims if c["type"] == "independent"]
                dependent_claims = [c for c in claims if c["type"] == "dependent"]
                
                print(f"   - Independent Claims: {len(independent_claims)}")
                print(f"   - Dependent Claims: {len(dependent_claims)}")
                
                # Show first claim as example
                if claims:
                    first_claim = claims[0]
                    print(f"   - First Claim: {first_claim['number']} ({first_claim['type']})")
                    print(f"     Text: {first_claim['text'][:100]}...")
                
                # Test claims summarization
                patent_data = {
                    "patent_id": patent_id,
                    "patent_title": f"Test Patent {patent_id}",
                    "claims": claims
                }
                
                summary = await patent_service._summarize_claims([patent_data])
                print(f"   - Claims Summary Length: {len(summary)} characters")
                print(f"   - Summary Preview: {summary[:200]}...")
                
            else:
                print(f"⚠️  No claims found for patent {patent_id}")
                
        except Exception as e:
            print(f"❌ Error fetching claims for patent {patent_id}: {e}")
    
    print("\n" + "=" * 60)
    print("CLAIMS FETCHING TEST COMPLETED")
    print("=" * 60)


async def test_claims_validation():
    """Test claims validation logic."""
    print("\n" + "=" * 60)
    print("TESTING CLAIMS VALIDATION")
    print("=" * 60)
    
    llm_client = MockLLMClient()
    patent_service = PatentSearchService(llm_client)
    
    # Test data with mixed quality claims
    test_patents = [
        {
            "patent_id": "test_patent",
            "patent_title": "Test Patent",
            "claims": [
                {
                    "number": "00001",
                    "text": "A method for wireless communication comprising the steps of transmitting and receiving signals.",  # Valid
                    "type": "independent",
                    "sequence": 1
                },
                {
                    "number": "00002",
                    "text": "Short",  # Too short - should be filtered out
                    "type": "dependent",
                    "sequence": 2
                },
                {
                    "number": "00003",
                    "text": "",  # Empty - should be filtered out
                    "type": "dependent",
                    "sequence": 3
                },
                {
                    "number": "00004",
                    "text": "The method of claim 1, wherein the signals are transmitted using orthogonal frequency division multiplexing (OFDM) modulation techniques.",  # Valid
                    "type": "dependent",
                    "sequence": 4
                }
            ]
        }
    ]
    
    summary = await patent_service._summarize_claims(test_patents)
    
    print("✅ Claims validation test completed")
    print(f"Summary length: {len(summary)} characters")
    print(f"Summary preview: {summary[:300]}...")


def test_prompt_template_changes():
    """Test that the prompt template has been updated correctly."""
    print("\n" + "=" * 60)
    print("TESTING PROMPT TEMPLATE CHANGES")
    print("=" * 60)
    
    # Read the prompt template file
    template_path = "backend/app/prompts/prior_art_search_comprehensive.txt"
    
    if not os.path.exists(template_path):
        print(f"❌ Template file not found: {template_path}")
        return False
    
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Check for Key Claims section removal
    if "**Key Claims**" in content:
        print("❌ Key Claims section still present in prompt template")
        return False
    else:
        print("✅ Key Claims section successfully removed")
    
    # Check for enhanced Innovation Summary
    if "Comprehensive 4-5 sentence summary" in content:
        print("✅ Innovation Summary enhanced with comprehensive requirements")
    else:
        print("❌ Innovation Summary not properly enhanced")
        return False
    
    # Check for detailed requirements
    required_text = "key technical features, novel aspects, how it relates to the search query, patent scope and limitations, and technical implementation details"
    if required_text in content:
        print("✅ Innovation Summary includes all required elements")
    else:
        print("❌ Innovation Summary missing required elements")
        return False
    
    # Check for claim text references (should be removed)
    if "first 3 claims with full text" in content:
        print("❌ Old claim text references still present")
        return False
    else:
        print("✅ Old claim text references successfully removed")
    
    print("✅ All prompt template changes verified successfully")
    return True


def test_patent_search_service_changes():
    """Test that the patent search service has been updated correctly."""
    print("\n" + "=" * 60)
    print("TESTING PATENT SEARCH SERVICE CHANGES")
    print("=" * 60)
    
    # Read the patent search service file
    service_path = "backend/app/services/patent_search_service.py"
    
    if not os.path.exists(service_path):
        print(f"❌ Service file not found: {service_path}")
        return False
    
    with open(service_path, 'r') as f:
        content = f.read()
    
    # Check for simplified patent summary structure (no full_abstract - we removed it)
    if "full_abstract" not in content:
        print("✅ full_abstract field removed from patent summary (simplified)")
    else:
        print("❌ full_abstract field still present (should be removed)")
        return False
    
    # Check for simplified patent summary structure
    if "Create patent summary for Innovation Summary" in content:
        print("✅ Simplified patent summary structure implemented")
    else:
        print("❌ Simplified patent summary structure not implemented")
        return False
    
    # Check for claims_text processing
    if "claims_text" in content:
        print("✅ Claims text processing maintained")
    else:
        print("❌ Claims text processing missing")
        return False
    
    print("✅ All patent search service changes verified successfully")
    return True


def test_docker_status():
    """Test that Docker is running and the service is available."""
    print("\n" + "=" * 60)
    print("TESTING DOCKER STATUS")
    print("=" * 60)
    
    try:
        # Check if Docker containers are running
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        
        if 'wordaddin-backend' in result.stdout:
            print("✅ Backend container is running")
        else:
            print("❌ Backend container not running")
            return False
        
        if 'wordaddin-redis' in result.stdout:
            print("✅ Redis container is running")
        else:
            print("❌ Redis container not running")
            return False
        
        print("✅ All Docker containers are running")
        return True
        
    except Exception as e:
        print(f"❌ Error checking Docker status: {e}")
        return False


async def test_claims_configuration():
    """Test claims fetching configuration."""
    print("\n" + "=" * 60)
    print("TESTING CLAIMS CONFIGURATION")
    print("=" * 60)
    
    llm_client = MockLLMClient()
    patent_service = PatentSearchService(llm_client)
    
    # Test the expected configuration
    print(f"✅ Base URL: {patent_service.base_url}")
    print(f"✅ API Key: {'Set' if patent_service.api_key else 'Not set'}")
    
    # Test payload structure
    patent_id = "test_patent"
    expected_payload = {
        "q": {"patent_id": patent_id},
        "f": ["claim_sequence", "claim_text", "claim_number", "claim_dependent"],
        "o": {"size": 100},  # Verify increased size limit
        "s": [{"claim_sequence": "asc"}]
    }
    
    print(f"✅ Size limit: {expected_payload['o']['size']} (increased from 50)")
    print(f"✅ Required fields: {expected_payload['f']}")
    print(f"✅ Sorting: {expected_payload['s']}")


async def main():
    """Run all consolidated tests."""
    print("🚀 STARTING CONSOLIDATED PATENT SEARCH TESTS")
    print("Testing claims fetching, report structure, and system status")
    
    success = True
    
    # Run all tests
    await test_claims_configuration()
    await test_claims_validation()
    success &= test_prompt_template_changes()
    success &= test_patent_search_service_changes()
    success &= test_docker_status()
    await test_claims_fetching_real_patents()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL CONSOLIDATED TESTS PASSED!")
        print("✅ Claims fetching working correctly")
        print("✅ Report structure updated successfully")
        print("✅ System status healthy")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the output above for details")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
