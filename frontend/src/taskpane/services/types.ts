export interface ToolSchema {
  type: string;
  properties: Record<string, any>;
  required?: string[];
}

export interface MCPTool {
  name: string;
  description: string;
  inputSchema: ToolSchema;
  outputSchema: ToolSchema;
  parameters?: Record<string, any>;
  category?: string;
  tags?: string[];
  enabled?: boolean;
}

export interface MCPToolExecutionResult {
  success: boolean;
  output?: Record<string, any>;
  data?: Record<string, any>;
  error?: string;
  executionTime?: number;
  metadata?: Record<string, any>;
}

export type MCPConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export interface MCPServerConfig {
  name: string;
  url: string;
  server_url?: string; // Alternative field name for backend compatibility
  enabled: boolean;
  description?: string;
  tools?: MCPTool[];
}

export interface MCPServerInfo {
  id: string;
  name: string;
  url: string;
  status: string;
  connected: boolean;
  toolCount: number;
  description?: string;
  lastHealthCheck?: number;
}

export interface MCPExecutionHistoryItem {
  id: string;
  tool: string;
  parameters: Record<string, any>;
  result: Record<string, any>;
  timestamp: Date;
  success: boolean;
  executionTime?: number;
}

export interface MCPMessage {
  id: string;
  type: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  timestamp: Date;
  metadata?: Record<string, any>;
}

export interface MCPToolCall {
  tool: string;
  arguments: Record<string, any>;
  id?: string;
}

export interface MCPToolResponse {
  tool: string;
  output: Record<string, any>;
  error?: string;
  id?: string;
}
