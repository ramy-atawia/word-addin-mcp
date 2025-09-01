import asyncio
import httpx
import json
import os

# Base URL for the backend API (ensure this matches your running backend)
BASE_URL = "https://127.0.0.1:9000/api/v1/mcp"

async def test_mcp_interactions():
    """
    Tests the end-to-end MCP interactions:
    1. Tool retrieval/listing
    2. Agent selects a tool based on prompt
    3. Agent makes a tool call and returns formatted output
    """
    print("🚀 Starting End-to-End MCP Interactions Test...")

    async with httpx.AsyncClient(verify=False) as client:
        # --- 1. Test Tool Retrieval/Listing ---
        print("\n--- Testing Tool Retrieval ---")
        try:
            response = await client.get(f"{BASE_URL}/tools")
            response.raise_for_status()
            tools_data = response.json()

            print(f"✅ Successfully retrieved {tools_data.get('total_count', 0)} tools.")
            for tool in tools_data.get("tools", []):
                print(f"   - {tool['name']}: {tool['description']}")
            
            if not tools_data.get("tools"):
                print("❌ No tools listed. Ensure internal server is running and tools are registered.")
                return

        except httpx.RequestError as e:
            print(f"❌ Connection error during tool retrieval: {e}")
            return
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP error during tool retrieval: {e.response.status_code} - {e.response.text}")
            return
        except Exception as e:
            print(f"❌ Unexpected error during tool retrieval: {e}")
            return

        # --- 2. Test Agent Selects Tool & Makes Call (Web Search Example) ---
        print("\n--- Testing Agent Tool Selection and Execution (Web Search) ---")
        test_message = "Search for the latest trends in quantum computing"
        available_tools_str = ",".join([tool["name"] for tool in tools_data.get("tools", [])])

        agent_request_payload = {
            "message": test_message,
            "context": {
                "document_content": "",
                "chat_history": "",
                "available_tools": available_tools_str
            }
        }

        print(f"Sending message to agent: '{test_message}' with available tools: {available_tools_str}")
        try:
            response = await client.post(
                f"{BASE_URL}/agent/chat",
                json=agent_request_payload,
                timeout=30 # Increased timeout for potential LLM/tool execution
            )
            response.raise_for_status()
            agent_response = response.json()

            print(f"✅ Agent response received: {json.dumps(agent_response, indent=2)}")

            # --- 3. Verify Tool Output ---
            if agent_response.get("success"):
                if agent_response.get("tool_name") == "web_search_tool":
                    print(f"✅ Agent successfully selected and reported 'web_search_tool'.")
                    if "Here's what I found" in agent_response.get("response", "") and "URL:" in agent_response.get("response", ""):
                        print("✅ Web search results are formatted and present in the response.")
                    else:
                        print("❌ Web search results not properly formatted or missing.")
                elif agent_response.get("intent_type") == "conversation":
                    print("⚠️ Agent defaulted to conversational response. This might be expected if the LLM couldn't route to a tool.")
                else:
                    print(f"❌ Agent selected an unexpected tool or intent: {agent_response.get('tool_name')}/{agent_response.get('intent_type')}")
            else:
                print(f"❌ Agent call failed: {agent_response.get('error', 'Unknown error')}")

        except httpx.RequestError as e:
            print(f"❌ Connection error during agent chat: {e}")
            return
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP error during agent chat: {e.response.status_code} - {e.response.text}")
            print(f"Response body: {e.response.text}")
            return
        except Exception as e:
            print(f"❌ Unexpected error during agent chat: {e}")
            return

    print("\n🎉 End-to-End MCP Interactions Test Completed!")

if __name__ == "__main__":
    asyncio.run(test_mcp_interactions())
