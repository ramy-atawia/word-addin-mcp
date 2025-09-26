import { MCPTool, MCPToolExecutionResult, MCPConnectionStatus, StreamingEvent, AgentStreamingCallbacks } from './types';
import { getAccessToken } from '../../services/authTokenStore';

class MCPToolService {
  private baseUrl: string = (window as any).BACKEND_URL || 'http://localhost:9000';
  private connectionStatus: MCPConnectionStatus = 'disconnected';

  setBaseUrl(url: string) {
    this.baseUrl = url;
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }

  getConnectionStatus(): MCPConnectionStatus {
    return this.connectionStatus;
  }

  async discoverTools(): Promise<MCPTool[]> {
    try {
      this.connectionStatus = 'connecting';
      
      const token = getAccessToken();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${this.baseUrl}/api/v1/mcp/tools`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      this.connectionStatus = 'connected';
      return data.tools || [];
    } catch (error) {
      this.connectionStatus = 'error';
      console.error('Failed to discover tools:', error);
      throw error;
    }
  }

  async executeTool(toolName: string, arguments_: any): Promise<MCPToolExecutionResult> {
    try {
      const token = getAccessToken();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${this.baseUrl}/api/v1/mcp/tools/${toolName}/execute`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          parameters: arguments_,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Failed to execute tool:', error);
      throw error;
    }
  }

  async getToolSchema(toolName: string): Promise<any> {
    try {
      const token = getAccessToken();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${this.baseUrl}/api/v1/mcp/tools/${toolName}/schema`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const schema = await response.json();
      return schema;
    } catch (error) {
      console.error('Failed to get tool schema:', error);
      throw error;
    }
  }

  async testConnection(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      this.connectionStatus = response.ok ? 'connected' : 'error';
      return response.ok;
    } catch (error) {
      this.connectionStatus = 'error';
      return false;
    }
  }

  async chatWithAgent(params: {
    message: any;
    context: {
      document_content: string;
      chat_history: string;
      available_tools: string;
    };
    sessionId: string;
  }): Promise<{
    success: boolean;
    result?: {
      response: string;
      tool_name?: string;
      intent_type?: string;
    };
    error?: string;
  }> {
    try {
      const token = getAccessToken();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${this.baseUrl}/api/v1/mcp/agent/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify(params),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      // Transform backend response to match frontend expectations
      return {
        success: result.success,
        result: {
          response: result.response,
          tool_name: result.tool_name,
          intent_type: result.intent_type
        },
        error: result.error
      };
    } catch (error) {
      console.error('Failed to chat with agent:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to chat with agent',
      };
    }
  }

  async chatWithAgentStreaming(params: {
    message: string;
    context: {
      document_content: string;
      chat_history: string;
      available_tools: string;
    };
    sessionId: string;
    callbacks: AgentStreamingCallbacks;
  }): Promise<void> {
    try {
      const token = getAccessToken();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Use fetch with streaming response
      const response = await fetch(`${this.baseUrl}/api/v1/mcp/agent/chat/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message: params.message,
          context: params.context,
          session_id: params.sessionId
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      // Read the streaming response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) {
            break;
          }

          // Decode the chunk and add to buffer
          buffer += decoder.decode(value, { stream: true });
          
          // Process complete lines
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep the last incomplete line in buffer

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const eventData = line.slice(6); // Remove 'data: ' prefix
                if (eventData.trim()) {
                  const streamingEvent: StreamingEvent = JSON.parse(eventData);
                  params.callbacks.onEvent(streamingEvent);
                  
                  // Check if this is a completion event
                  if (streamingEvent.event_type === 'workflow_complete') {
                    params.callbacks.onComplete(streamingEvent.data);
                    return;
                  }
                  
                  // Check if this is an error event
                  if (streamingEvent.event_type === 'workflow_error' || streamingEvent.event_type === 'stream_error') {
                    params.callbacks.onError(streamingEvent.data.message || 'Streaming error occurred');
                    return;
                  }
                  
                  // Handle LangGraph chunks
                  if (streamingEvent.event_type === 'langgraph_chunk') {
                    const chunk = streamingEvent.data;
                    
                    // Process LangGraph updates - handle both old and new formats
                    if (chunk.updates && typeof chunk.updates === 'object') {
                      try {
                        for (const [nodeName, nodeData] of Object.entries(chunk.updates)) {
                          params.callbacks.onEvent({
                            event_type: `node_${nodeName}`,
                            data: {
                              node: nodeName,
                              message: `Completed ${nodeName}`,
                              state: nodeData
                            },
                            timestamp: streamingEvent.timestamp
                          });
                        }
                      } catch (error) {
                        console.warn('Failed to process LangGraph updates:', error);
                      }
                    }
                    
                    // Process LangGraph messages (LLM tokens)
                    if (chunk.messages && Array.isArray(chunk.messages)) {
                      for (const message of chunk.messages) {
                        if (message && message.content) {
                          // Ensure content is a string
                          const contentString = typeof message.content === 'string' 
                            ? message.content 
                            : String(message.content || '');
                          
                          params.callbacks.onEvent({
                            event_type: 'llm_token',
                            data: {
                              content: contentString,
                              is_streaming: true
                            },
                            timestamp: streamingEvent.timestamp
                          });
                        }
                      }
                    }
                    
                    // Handle raw chunk data if present
                    if (chunk.raw_chunk) {
                      console.log('Raw LangGraph chunk:', chunk.raw_chunk);
                      params.callbacks.onEvent({
                        event_type: 'raw_chunk',
                        data: {
                          content: JSON.stringify(chunk.raw_chunk),
                          is_streaming: true
                        },
                        timestamp: streamingEvent.timestamp
                      });
                    }
                  }
                }
              } catch (parseError) {
                console.error('Failed to parse streaming event:', parseError);
                // Continue processing other events
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
      
    } catch (error) {
      console.error('Failed to start streaming chat:', error);
      params.callbacks.onError(error instanceof Error ? error.message : 'Failed to start streaming chat');
    }
  }

}

export default new MCPToolService();
export { MCPToolService };
