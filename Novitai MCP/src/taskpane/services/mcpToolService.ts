import { MCPTool, MCPToolExecutionResult, MCPConnectionStatus } from './types';
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
    // TODO: Implement tool schema endpoint in backend
    // For now, return a mock schema or throw an error
    throw new Error(`Tool schema endpoint not yet implemented for ${toolName}`);
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
    message: string;
    context: {
      document_content: string;
      chat_history: string;
      available_tools: string;
      session_id?: string; // Add session_id to context instead of separate field
    };
  }): Promise<{
    success: boolean;
    result?: {
      response: string;
      tool_name?: string;
      intent_type?: string;
      execution_time?: number;
      workflow_metadata?: any;
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
      
      // Send request in backend-expected format
      const requestBody = {
        message: params.message,
        context: {
          document_content: params.context.document_content,
          chat_history: params.context.chat_history,
          available_tools: params.context.available_tools,
          session_id: params.context.session_id
        }
      };
      
      const response = await fetch(`${this.baseUrl}/api/v1/mcp/agent/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify(requestBody),
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
          intent_type: result.intent_type,
          execution_time: result.execution_time,
          workflow_metadata: result.workflow_metadata
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


}

export default new MCPToolService();
export { MCPToolService };
