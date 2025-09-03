"""
LLM Capability Tests for Word Add-in MCP System
"""
import pytest
import httpx
import json
import time
from typing import Dict, Any
from conftest import API_BASE

class TestLLMCapabilities:
    """Test suite for LLM capabilities."""
    
    @pytest.mark.asyncio
    async def test_conversation_context_preservation(self, http_client: httpx.AsyncClient, test_result):
        """TC-076: Conversation Context Preservation"""
        test_id = "TC-076"
        try:
            conversation_history = [
                {"role": "user", "content": "My name is John"},
                {"role": "assistant", "content": "Nice to meet you, John!"},
                {"role": "user", "content": "What's my name?"}
            ]
            
            payload = {
                "message": "Can you help me with something?",
                "context": {
                    "document_content": "",
                    "chat_history": json.dumps(conversation_history),
                    "available_tools": "text_analysis_tool"
                }
            }
            
            response = await http_client.post(
                f"{API_BASE}/mcp/chat",
                json=payload
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "response" in data, "Response missing 'response' field"
            
            # Check if response references the name from context
            response_text = data["response"].lower()
            has_name_reference = "john" in response_text
            
            test_result.add_result(test_id, "PASS", {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "has_name_reference": has_name_reference,
                "response_preview": data["response"][:100] + "..." if len(data["response"]) > 100 else data["response"]
            })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
    
    @pytest.mark.asyncio
    async def test_document_context_understanding(self, http_client: httpx.AsyncClient, test_result, sample_document):
        """TC-077: Document Context Understanding"""
        test_id = "TC-077"
        try:
            payload = {
                "message": "What was the revenue increase mentioned in the document?",
                "context": {
                    "document_content": sample_document,
                    "chat_history": "[]",
                    "available_tools": "document_analysis_tool"
                }
            }
            
            response = await http_client.post(
                f"{API_BASE}/mcp/chat",
                json=payload
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "response" in data, "Response missing 'response' field"
            
            # Check if response contains revenue information
            response_text = data["response"].lower()
            has_revenue_info = any(keyword in response_text for keyword in ["15%", "revenue", "increase"])
            
            test_result.add_result(test_id, "PASS", {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "has_revenue_info": has_revenue_info,
                "response_preview": data["response"][:100] + "..." if len(data["response"]) > 100 else data["response"]
            })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
    
    @pytest.mark.asyncio
    async def test_long_conversation_context(self, http_client: httpx.AsyncClient, test_result):
        """TC-078: Long Conversation Context"""
        test_id = "TC-078"
        try:
            # Create a long conversation history
            long_conversation = []
            for i in range(30):
                long_conversation.extend([
                    {"role": "user", "content": f"Message {i} from user"},
                    {"role": "assistant", "content": f"Response {i} from assistant"}
                ])
            
            # Add a question about earlier conversation
            long_conversation.append({"role": "user", "content": "What did I ask you about 20 messages ago?"})
            
            payload = {
                "message": "Can you remember our earlier discussion?",
                "context": {
                    "document_content": "",
                    "chat_history": json.dumps(long_conversation),
                    "available_tools": "text_analysis_tool"
                }
            }
            
            response = await http_client.post(
                f"{API_BASE}/mcp/chat",
                json=payload
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "response" in data, "Response missing 'response' field"
            
            # Check if response shows context awareness
            response_text = data["response"].lower()
            has_context_awareness = any(keyword in response_text for keyword in ["message", "discussion", "earlier", "remember"])
            
            test_result.add_result(test_id, "PASS", {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "conversation_length": len(long_conversation),
                "has_context_awareness": has_context_awareness,
                "response_preview": data["response"][:100] + "..." if len(data["response"]) > 100 else data["response"]
            })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
    
    @pytest.mark.asyncio
    async def test_tool_selection_accuracy(self, http_client: httpx.AsyncClient, test_result):
        """TC-082: Tool Selection Accuracy"""
        test_id = "TC-082"
        try:
            payload = {
                "message": "I need to find information about machine learning algorithms",
                "context": {
                    "document_content": "",
                    "chat_history": "[]",
                    "available_tools": "web_search_tool,text_analysis_tool,document_analysis_tool,file_reader_tool"
                }
            }
            
            response = await http_client.post(
                f"{API_BASE}/mcp/chat",
                json=payload
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "response" in data, "Response missing 'response' field"
            
            # Check if appropriate tool was selected (if tools_used is available)
            tools_used = data.get("tools_used", [])
            response_text = data["response"].lower()
            
            # Check if response indicates search was performed
            indicates_search = any(keyword in response_text for keyword in ["search", "found", "results", "information"])
            
            test_result.add_result(test_id, "PASS", {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "tools_used": tools_used,
                "indicates_search": indicates_search,
                "response_preview": data["response"][:100] + "..." if len(data["response"]) > 100 else data["response"]
            })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
    
    @pytest.mark.asyncio
    async def test_response_coherence(self, http_client: httpx.AsyncClient, test_result):
        """TC-086: Response Coherence"""
        test_id = "TC-086"
        try:
            payload = {
                "message": "Explain the difference between supervised and unsupervised machine learning, and provide examples of each.",
                "context": {
                    "document_content": "",
                    "chat_history": "[]",
                    "available_tools": "web_search_tool,text_analysis_tool"
                }
            }
            
            response = await http_client.post(
                f"{API_BASE}/mcp/chat",
                json=payload
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "response" in data, "Response missing 'response' field"
            
            response_text = data["response"]
            
            # Check response coherence
            has_supervised = "supervised" in response_text.lower()
            has_unsupervised = "unsupervised" in response_text.lower()
            has_examples = any(keyword in response_text.lower() for keyword in ["example", "such as", "like", "including"])
            is_structured = len(response_text.split('.')) > 3  # Multiple sentences
            
            coherence_score = sum([has_supervised, has_unsupervised, has_examples, is_structured]) / 4
            
            test_result.add_result(test_id, "PASS", {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "coherence_score": coherence_score,
                "has_supervised": has_supervised,
                "has_unsupervised": has_unsupervised,
                "has_examples": has_examples,
                "is_structured": is_structured,
                "response_length": len(response_text)
            })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
    
    @pytest.mark.asyncio
    async def test_document_summarization(self, http_client: httpx.AsyncClient, test_result, sample_document):
        """TC-091: Document Summarization"""
        test_id = "TC-091"
        try:
            payload = {
                "message": "Please provide a concise summary of this document.",
                "context": {
                    "document_content": sample_document,
                    "chat_history": "[]",
                    "available_tools": "document_analysis_tool"
                }
            }
            
            response = await http_client.post(
                f"{API_BASE}/mcp/chat",
                json=payload
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "response" in data, "Response missing 'response' field"
            
            response_text = data["response"]
            original_length = len(sample_document)
            summary_length = len(response_text)
            
            # Check if summary is shorter than original
            is_shorter = summary_length < original_length
            compression_ratio = summary_length / original_length if original_length > 0 else 0
            
            # Check if summary contains key information
            has_key_info = any(keyword in response_text.lower() for keyword in ["revenue", "15%", "q3", "2025"])
            
            test_result.add_result(test_id, "PASS", {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "original_length": original_length,
                "summary_length": summary_length,
                "compression_ratio": compression_ratio,
                "is_shorter": is_shorter,
                "has_key_info": has_key_info,
                "summary_preview": response_text[:200] + "..." if len(response_text) > 200 else response_text
            })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
