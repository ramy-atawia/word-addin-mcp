#!/usr/bin/env python3
"""
Comprehensive Multi-Step Workflow Testing Suite

This test suite thoroughly validates the unified LangGraph multi-step workflow functionality
with various command patterns, error scenarios, and edge cases.
"""
import asyncio
import sys
import os
import json
from typing import Dict, Any, List

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.langgraph_agent_unified import (
    get_agent_graph, 
    _has_multi_step_indicators,
    _create_dynamic_workflow_plan,
    detect_intent_node,
    plan_workflow_node
)

class MultiStepWorkflowTester:
    """Comprehensive tester for multi-step workflows"""
    
    def __init__(self):
        self.test_results = []
        self.available_tools = [
            {"name": "prior_art_search_tool", "description": "Search for prior art patents"},
            {"name": "claim_drafting_tool", "description": "Draft patent claims"},
            {"name": "web_search_tool", "description": "Search the web"},
            {"name": "patent_analysis_tool", "description": "Analyze patent documents"},
            {"name": "document_analysis_tool", "description": "Analyze document content"}
        ]
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "timestamp": asyncio.get_event_loop().time()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
    
    async def test_multi_step_detection(self):
        """Test multi-step indicator detection"""
        print("\n🔍 Testing Multi-Step Detection Logic")
        print("=" * 50)
        
        test_cases = [
            # Should be detected as multi-step
            ("prior art search 5g ai, draft 2 claims", True, "Comma-separated actions"),
            ("web search ramy atawia then prior art search", True, "Then connector"),
            ("search for AI patents and draft 5 claims", True, "And connector"),
            ("find blockchain patents then analyze them", True, "Then connector"),
            ("search patents, analyze results, draft claims", True, "Multiple commas"),
            ("web search then prior art then draft", True, "Multiple thens"),
            ("search and find and draft", True, "Multiple ands"),
            
            # Should NOT be detected as multi-step
            ("prior art search for 5g technology", False, "Single action"),
            ("draft 5 claims for AI system", False, "Single action"),
            ("web search for blockchain", False, "Single action"),
            ("hello how are you", False, "Conversation"),
            ("what is a patent", False, "Question"),
        ]
        
        for input_text, expected, description in test_cases:
            result = _has_multi_step_indicators(input_text)
            success = result == expected
            self.log_test(
                f"Multi-step detection: '{input_text[:30]}...'",
                success,
                f"Expected: {expected}, Got: {result} - {description}"
            )
    
    async def test_workflow_planning(self):
        """Test workflow planning for various multi-step commands"""
        print("\n📋 Testing Workflow Planning")
        print("=" * 50)
        
        test_cases = [
            {
                "input": "prior art search 5g ai, draft 2 claims",
                "expected_tools": ["prior_art_search_tool", "claim_drafting_tool"],
                "description": "Basic prior art + claim drafting"
            },
            {
                "input": "web search ramy atawia then prior art search",
                "expected_tools": ["web_search_tool", "prior_art_search_tool"],
                "description": "Web search + prior art"
            },
            {
                "input": "search for blockchain patents then analyze them then draft claims",
                "expected_tools": ["prior_art_search_tool", "patent_analysis_tool", "claim_drafting_tool"],
                "description": "Three-step workflow"
            },
            {
                "input": "find AI patents and draft 5 claims",
                "expected_tools": ["prior_art_search_tool", "claim_drafting_tool"],
                "description": "And connector workflow"
            }
        ]
        
        for test_case in test_cases:
            try:
                workflow_plan = _create_dynamic_workflow_plan(
                    test_case["input"], 
                    self.available_tools, 
                    {}
                )
                
                actual_tools = [step["tool"] for step in workflow_plan]
                expected_tools = test_case["expected_tools"]
                
                # Check if all expected tools are present (order may vary)
                tools_match = all(tool in actual_tools for tool in expected_tools)
                correct_length = len(workflow_plan) == len(expected_tools)
                
                success = tools_match and correct_length
                details = f"Expected: {expected_tools}, Got: {actual_tools}, Steps: {len(workflow_plan)}"
                
                self.log_test(
                    f"Workflow planning: '{test_case['input'][:30]}...'",
                    success,
                    details
                )
                
            except Exception as e:
                self.log_test(
                    f"Workflow planning: '{test_case['input'][:30]}...'",
                    False,
                    f"Exception: {str(e)}"
                )
    
    async def test_intent_detection(self):
        """Test intent detection for various inputs"""
        print("\n🎯 Testing Intent Detection")
        print("=" * 50)
        
        test_cases = [
            {
                "input": "prior art search 5g ai, draft 2 claims",
                "expected_intent": "multi_step",
                "description": "Multi-step command"
            },
            {
                "input": "web search ramy atawia then prior art search",
                "expected_intent": "multi_step", 
                "description": "Multi-step with then"
            },
            {
                "input": "prior art search for 5g technology",
                "expected_intent": "tool_execution",
                "description": "Single tool command"
            },
            {
                "input": "hello how are you",
                "expected_intent": "conversation",
                "description": "Conversation"
            }
        ]
        
        for test_case in test_cases:
            try:
                state = {
                    "user_input": test_case["input"],
                    "document_content": "",
                    "conversation_history": [],
                    "available_tools": self.available_tools,
                    "selected_tool": "",
                    "intent_type": "",
                    "tool_parameters": {},
                    "workflow_plan": None,
                    "current_step": 0,
                    "total_steps": 0,
                    "step_results": {},
                    "final_response": "",
                    "success": False,
                    "execution_time": 0.0
                }
                
                result_state = await detect_intent_node(state)
                actual_intent = result_state.get("intent_type")
                expected_intent = test_case["expected_intent"]
                
                success = actual_intent == expected_intent
                details = f"Expected: {expected_intent}, Got: {actual_intent}"
                
                self.log_test(
                    f"Intent detection: '{test_case['input'][:30]}...'",
                    success,
                    details
                )
                
            except Exception as e:
                self.log_test(
                    f"Intent detection: '{test_case['input'][:30]}...'",
                    False,
                    f"Exception: {str(e)}"
                )
    
    async def test_graph_creation(self):
        """Test LangGraph creation and structure"""
        print("\n🔄 Testing LangGraph Creation")
        print("=" * 50)
        
        try:
            graph = get_agent_graph()
            graph_type = type(graph).__name__
            
            # Check if it's a real LangGraph, not a mock
            is_real_graph = "CompiledStateGraph" in graph_type or "StateGraph" in graph_type
            is_mock = "Mock" in graph_type
            
            success = is_real_graph and not is_mock
            details = f"Graph type: {graph_type}, Is real: {is_real_graph}, Is mock: {is_mock}"
            
            self.log_test("LangGraph creation", success, details)
            
        except Exception as e:
            self.log_test("LangGraph creation", False, f"Exception: {str(e)}")
    
    async def test_workflow_execution_simulation(self):
        """Test workflow execution simulation (without actual tool calls)"""
        print("\n⚙️ Testing Workflow Execution Simulation")
        print("=" * 50)
        
        test_inputs = [
            "prior art search 5g ai, draft 2 claims",
            "web search blockchain then prior art search",
            "find AI patents and analyze them and draft claims"
        ]
        
        for input_text in test_inputs:
            try:
                # Create initial state
                state = {
                    "user_input": input_text,
                    "document_content": "",
                    "conversation_history": [],
                    "available_tools": self.available_tools,
                    "selected_tool": "",
                    "intent_type": "",
                    "tool_parameters": {},
                    "workflow_plan": None,
                    "current_step": 0,
                    "total_steps": 0,
                    "step_results": {},
                    "final_response": "",
                    "success": False,
                    "execution_time": 0.0
                }
                
                # Test intent detection
                state = await detect_intent_node(state)
                intent_detected = state.get("intent_type") == "multi_step"
                
                # Test workflow planning
                if intent_detected:
                    state = await plan_workflow_node(state)
                    workflow_created = state.get("workflow_plan") is not None
                    steps_planned = len(state.get("workflow_plan", [])) > 0
                else:
                    workflow_created = False
                    steps_planned = False
                
                success = intent_detected and workflow_created and steps_planned
                details = f"Intent: {state.get('intent_type')}, Workflow: {workflow_created}, Steps: {len(state.get('workflow_plan', []))}"
                
                self.log_test(
                    f"Workflow simulation: '{input_text[:30]}...'",
                    success,
                    details
                )
                
            except Exception as e:
                self.log_test(
                    f"Workflow simulation: '{input_text[:30]}...'",
                    False,
                    f"Exception: {str(e)}"
                )
    
    async def test_edge_cases(self):
        """Test edge cases and error scenarios"""
        print("\n🔍 Testing Edge Cases")
        print("=" * 50)
        
        edge_cases = [
            {
                "input": "",
                "description": "Empty input"
            },
            {
                "input": "search search search",
                "description": "Repeated action words"
            },
            {
                "input": "then then then",
                "description": "Only connectors"
            },
            {
                "input": "draft claims for search results from prior art search",
                "description": "Complex single command"
            },
            {
                "input": "a" * 1000,
                "description": "Very long input"
            }
        ]
        
        for case in edge_cases:
            try:
                # Test multi-step detection
                is_multi_step = _has_multi_step_indicators(case["input"])
                
                # Test workflow planning
                if case["input"]:
                    workflow_plan = _create_dynamic_workflow_plan(
                        case["input"], 
                        self.available_tools, 
                        {}
                    )
                    plan_created = len(workflow_plan) > 0
                else:
                    plan_created = False
                
                # Edge cases should not crash the system
                success = True  # If we get here without exception, it's a success
                details = f"Multi-step: {is_multi_step}, Plan created: {plan_created}"
                
                self.log_test(
                    f"Edge case: {case['description']}",
                    success,
                    details
                )
                
            except Exception as e:
                self.log_test(
                    f"Edge case: {case['description']}",
                    False,
                    f"Exception: {str(e)}"
                )
    
    def print_summary(self):
        """Print test summary"""
        print("\n📊 Test Summary")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['details']}")
        
        return passed_tests == total_tests

async def main():
    """Run comprehensive multi-step workflow tests"""
    print("🧪 Comprehensive Multi-Step Workflow Testing Suite")
    print("=" * 60)
    
    tester = MultiStepWorkflowTester()
    
    # Run all test suites
    await tester.test_multi_step_detection()
    await tester.test_workflow_planning()
    await tester.test_intent_detection()
    await tester.test_graph_creation()
    await tester.test_workflow_execution_simulation()
    await tester.test_edge_cases()
    
    # Print summary
    all_passed = tester.print_summary()
    
    if all_passed:
        print("\n🎉 All tests passed! Multi-step workflow functionality is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please review the issues above.")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
