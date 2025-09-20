"""
Streaming agent service for real-time progress updates.

This module provides streaming capabilities for the LangGraph agent workflow.
"""

import asyncio
import json
import logging
import time
from typing import AsyncGenerator, Dict, Any, Optional
from fastapi.responses import StreamingResponse

from ..schemas.streaming import (
    StreamEvent, StreamEventType, WorkflowStartEvent, IntentDetectedEvent,
    WorkflowPlannedEvent, ToolExecutionStartEvent, ToolExecutionCompleteEvent,
    ResponseGenerationStartEvent, ResponseChunkEvent, WorkflowCompleteEvent,
    ErrorEvent
)
from ..services.agent import AgentService
from ..services.langgraph_agent_unified import AgentState, get_agent_graph

logger = logging.getLogger(__name__)


class StreamingAgentService:
    """Service for streaming agent responses with real-time progress updates."""
    
    def __init__(self):
        self.agent_service = AgentService()
    
    async def stream_agent_response(
        self,
        user_message: str,
        document_content: Optional[str] = None,
        available_tools: Optional[list] = None,
        frontend_chat_history: Optional[list] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream agent response with real-time progress updates.
        
        Args:
            user_message: User's message
            document_content: Document content
            available_tools: Available tools
            frontend_chat_history: Chat history
            
        Yields:
            SSE formatted events
        """
        try:
            # Initialize workflow state
            initial_state = AgentState(
                user_input=user_message,
                document_content=document_content or "",
                conversation_history=frontend_chat_history or [],
                available_tools=available_tools or [],
                selected_tool="",
                tool_parameters={},
                tool_result=None,
                final_response="",
                intent_type="",
                workflow_plan=None,
                current_step=0,
                total_steps=0,
                step_results={}
            )
            
            # Stream workflow start event
            yield self._format_sse_event(WorkflowStartEvent(
                data={
                    "message": user_message,
                    "workflow_id": f"workflow_{int(time.time())}",
                    "status": "initializing"
                }
            ))
            
            # Get the agent graph
            agent_graph = get_agent_graph()
            
            # Stream the workflow execution
            async for event in self._stream_workflow_execution(agent_graph, initial_state):
                yield event
                
        except Exception as e:
            logger.error(f"Streaming agent error: {str(e)}")
            yield self._format_sse_event(ErrorEvent(
                data={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "status": "error"
                }
            ))
    
    async def _stream_workflow_execution(
        self, 
        agent_graph, 
        initial_state: AgentState
    ) -> AsyncGenerator[str, None]:
        """Stream the execution of the LangGraph workflow."""
        
        try:
            # Execute the workflow with streaming
            result = await agent_graph.astream(initial_state)
            
            # Track state changes for event generation
            previous_state = None
            
            async for state in result:
                # Process each state update and stream appropriate events
                await self._process_state_update(state)
                
                # Generate events based on state changes
                events = self._generate_events_from_state_change(previous_state, state)
                for event in events:
                    yield self._format_sse_event(event)
                
                previous_state = state.copy()
                    
        except Exception as e:
            logger.error(f"Workflow execution error: {str(e)}")
            yield self._format_sse_event(ErrorEvent(
                data={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "status": "workflow_error"
                }
            ))
    
    async def _process_state_update(self, state: AgentState):
        """Process state updates and log progress."""
        logger.debug(f"State update: {state.get('intent_type', 'unknown')} - {state.get('current_step', 0)}/{state.get('total_steps', 0)}")
    
    def _generate_events_from_state_change(self, previous_state: Optional[AgentState], current_state: AgentState) -> list[StreamEvent]:
        """Generate streaming events based on state changes."""
        events = []
        
        # Intent detection event
        if current_state.get("intent_type") and (not previous_state or not previous_state.get("intent_type")):
            events.append(IntentDetectedEvent(
                data={
                    "intent_type": current_state["intent_type"],
                    "selected_tool": current_state.get("selected_tool"),
                    "workflow_type": "multi_step" if current_state.get("total_steps", 0) > 1 else "single_tool"
                }
            ))
        
        # Workflow planning event
        if current_state.get("workflow_plan") and (not previous_state or not previous_state.get("workflow_plan")):
            events.append(WorkflowPlannedEvent(
                data={
                    "workflow_plan": current_state["workflow_plan"],
                    "total_steps": current_state.get("total_steps", 0),
                    "estimated_duration": len(current_state["workflow_plan"]) * 10  # 10 seconds per step estimate
                }
            ))
        
        # Tool execution events
        current_step = current_state.get("current_step", 0)
        total_steps = current_state.get("total_steps", 0)
        previous_step = previous_state.get("current_step", 0) if previous_state else 0
        
        if current_step > previous_step and total_steps > 0:
            # Tool execution start
            workflow_plan = current_state.get("workflow_plan", [])
            if current_step <= len(workflow_plan):
                current_tool = workflow_plan[current_step - 1]
                events.append(ToolExecutionStartEvent(
                    data={
                        "step": current_step,
                        "total_steps": total_steps,
                        "tool_name": current_tool.get("tool"),
                        "tool_display_name": self._get_tool_display_name(current_tool.get("tool")),
                        "progress_percentage": int((current_step / total_steps) * 100)
                    }
                ))
        
        # Tool execution complete
        if current_state.get("step_results") and previous_state:
            current_step_results = current_state.get("step_results", {})
            previous_step_results = previous_state.get("step_results", {})
            
            # Check for new step results
            for key, result in current_step_results.items():
                if key not in previous_step_results and result:
                    # Find which step this result belongs to
                    workflow_plan = current_state.get("workflow_plan", [])
                    for i, step in enumerate(workflow_plan):
                        if step.get("output_key") == key:
                            events.append(ToolExecutionCompleteEvent(
                                data={
                                    "step": i + 1,
                                    "total_steps": total_steps,
                                    "tool_name": step.get("tool"),
                                    "tool_display_name": self._get_tool_display_name(step.get("tool")),
                                    "success": result.get("success", True),
                                    "result_preview": self._get_result_preview(result),
                                    "progress_percentage": int(((i + 1) / total_steps) * 100)
                                }
                            ))
                            break
        
        # Response generation start
        if current_state.get("final_response") and (not previous_state or not previous_state.get("final_response")):
            events.append(ResponseGenerationStartEvent(
                data={
                    "status": "generating_response",
                    "total_steps_completed": current_state.get("current_step", 0)
                }
            ))
        
        # Workflow complete
        if (current_state.get("final_response") and 
            current_state.get("current_step", 0) >= current_state.get("total_steps", 0) and
            (not previous_state or previous_state.get("current_step", 0) < previous_state.get("total_steps", 0))):
            events.append(WorkflowCompleteEvent(
                data={
                    "final_response": current_state["final_response"],
                    "total_steps": current_state.get("total_steps", 0),
                    "execution_time": time.time() - getattr(self, '_start_time', time.time()),
                    "success": True
                }
            ))
        
        return events

    def _generate_events_from_state(self, state: AgentState) -> list[StreamEvent]:
        """Generate streaming events based on state changes."""
        events = []
        
        # Intent detection event
        if state.get("intent_type") and not hasattr(self, '_intent_sent'):
            events.append(IntentDetectedEvent(
                data={
                    "intent_type": state["intent_type"],
                    "selected_tool": state.get("selected_tool"),
                    "workflow_type": "multi_step" if state.get("total_steps", 0) > 1 else "single_tool"
                }
            ))
            self._intent_sent = True
        
        # Workflow planning event
        if state.get("workflow_plan") and not hasattr(self, '_workflow_planned'):
            events.append(WorkflowPlannedEvent(
                data={
                    "workflow_plan": state["workflow_plan"],
                    "total_steps": state.get("total_steps", 0),
                    "estimated_duration": len(state["workflow_plan"]) * 10  # 10 seconds per step estimate
                }
            ))
            self._workflow_planned = True
        
        # Tool execution events
        current_step = state.get("current_step", 0)
        total_steps = state.get("total_steps", 0)
        
        if current_step > 0 and total_steps > 0:
            # Tool execution start
            if not hasattr(self, f'_tool_started_{current_step}'):
                workflow_plan = state.get("workflow_plan", [])
                if current_step <= len(workflow_plan):
                    current_tool = workflow_plan[current_step - 1]
                    events.append(ToolExecutionStartEvent(
                        data={
                            "step": current_step,
                            "total_steps": total_steps,
                            "tool_name": current_tool.get("tool"),
                            "tool_display_name": self._get_tool_display_name(current_tool.get("tool")),
                            "progress_percentage": int((current_step / total_steps) * 100)
                        }
                    ))
                    setattr(self, f'_tool_started_{current_step}', True)
            
            # Tool execution complete
            if not hasattr(self, f'_tool_completed_{current_step}'):
                step_results = state.get("step_results", {})
                workflow_plan = state.get("workflow_plan", [])
                if current_step <= len(workflow_plan):
                    current_tool = workflow_plan[current_step - 1]
                    output_key = current_tool.get("output_key")
                    
                    if output_key in step_results:
                        tool_result = step_results[output_key]
                        events.append(ToolExecutionCompleteEvent(
                            data={
                                "step": current_step,
                                "total_steps": total_steps,
                                "tool_name": current_tool.get("tool"),
                                "tool_display_name": self._get_tool_display_name(current_tool.get("tool")),
                                "success": tool_result.get("success", True),
                                "result_preview": self._get_result_preview(tool_result),
                                "progress_percentage": int((current_step / total_steps) * 100)
                            }
                        ))
                        setattr(self, f'_tool_completed_{current_step}', True)
        
        # Response generation start
        if state.get("final_response") and not hasattr(self, '_response_started'):
            events.append(ResponseGenerationStartEvent(
                data={
                    "status": "generating_response",
                    "total_steps_completed": state.get("current_step", 0)
                }
            ))
            self._response_started = True
        
        # Workflow complete
        if state.get("final_response") and state.get("current_step", 0) >= state.get("total_steps", 0):
            events.append(WorkflowCompleteEvent(
                data={
                    "final_response": state["final_response"],
                    "total_steps": state.get("total_steps", 0),
                    "execution_time": time.time() - getattr(self, '_start_time', time.time()),
                    "success": True
                }
            ))
        
        return events
    
    def _get_tool_display_name(self, tool_name: str) -> str:
        """Get user-friendly display name for a tool."""
        display_names = {
            "web_search_tool": "Web Search",
            "prior_art_search_tool": "Prior Art Search",
            "claim_drafting_tool": "Claim Drafting",
            "claim_analysis_tool": "Claim Analysis",
            "text_analysis_tool": "Text Analysis",
            "document_analysis_tool": "Document Analysis"
        }
        return display_names.get(tool_name, tool_name.replace("_", " ").title())
    
    def _get_result_preview(self, tool_result: Dict[str, Any]) -> str:
        """Get a preview of the tool result for display."""
        if not tool_result:
            return "No result"
        
        result_text = tool_result.get("result", "")
        if isinstance(result_text, str):
            # Truncate to 100 characters for preview
            return result_text[:100] + "..." if len(result_text) > 100 else result_text
        return str(result_text)[:100]
    
    def _format_sse_event(self, event: StreamEvent) -> str:
        """Format an event as Server-Sent Event."""
        event_data = {
            "event": event.event_type,
            "timestamp": event.timestamp,
            "data": event.data
        }
        
        return f"data: {json.dumps(event_data)}\n\n"
    
    def create_streaming_response(self, generator: AsyncGenerator[str, None]) -> StreamingResponse:
        """Create a StreamingResponse from the event generator."""
        return StreamingResponse(
            generator,
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
