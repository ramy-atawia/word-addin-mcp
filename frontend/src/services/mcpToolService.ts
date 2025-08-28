/**
 * MCP Tool Service for frontend integration
 * This service handles communication with MCP tools through the backend API
 */

export interface MCPTool {
  name: string;
  description: string;
  category: string;
  version: string;
  parameters: MCPToolParameter[];
  status: 'available' | 'unavailable' | 'error';
  lastUsed?: Date;
  usageCount: number;
}

export interface MCPToolParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  description: string;
  required: boolean;
  default?: any;
  enum?: any[];
  minimum?: number;
  maximum?: number;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  minItems?: number;
  maxItems?: number;
  multipleOf?: number;
}

export interface MCPToolExecutionRequest {
  toolName: string;
  parameters: Record<string, any>;
  sessionId?: string;
  userId?: string;
}

export interface MCPToolExecutionResult {
  success: boolean;
  result: any;
  executionTime: number;
  timestamp: Date;
  error?: string;
  metadata?: Record<string, any>;
  toolName: string;
  sessionId?: string;
  userId?: string;
}

export interface MCPToolDiscoveryResult {
  tools: MCPTool[];
  totalCount: number;
  categories: string[];
  lastUpdated: Date;
}

class MCPToolService {
  private baseUrl: string;
  private tools: MCPTool[] = [];
  private toolCache: Map<string, MCPTool> = new Map();
  private lastDiscovery: Date | null = null;
  private discoveryCacheTimeout = 5 * 60 * 1000; // 5 minutes

  constructor(baseUrl: string = 'http://localhost:9000') {
    this.baseUrl = baseUrl;
  }

  /**
   * Set the base URL for the MCP backend API
   */
  setBaseUrl(url: string): void {
    this.baseUrl = url;
  }

  /**
   * Discover available MCP tools
   */
  async discoverTools(forceRefresh: boolean = false): Promise<MCPTool[]> {
    // Check cache first
    if (!forceRefresh && this.lastDiscovery && 
        Date.now() - this.lastDiscovery.getTime() < this.discoveryCacheTimeout) {
      return this.tools;
    }

    try {
      const response = await fetch(`${this.baseUrl}/api/v1/mcp/tools`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.tools && Array.isArray(data.tools)) {
        this.tools = data.tools.map((tool: any) => ({
          ...tool,
          status: 'available',
          lastUsed: tool.lastUsed ? new Date(tool.lastUsed) : undefined,
          usageCount: tool.usageCount || 0
        }));
        
        // Update cache
        this.tools.forEach(tool => {
          this.toolCache.set(tool.name, tool);
        });
        
        this.lastDiscovery = new Date();
        return this.tools;
      } else {
        throw new Error('Invalid tools data received from backend');
      }
    } catch (error) {
      console.error('Failed to discover MCP tools:', error);
      throw error;
    }
  }

  /**
   * Get a specific tool by name
   */
  async getTool(toolName: string): Promise<MCPTool | null> {
    // Check cache first
    if (this.toolCache.has(toolName)) {
      return this.toolCache.get(toolName)!;
    }

    try {
      const response = await fetch(`${this.baseUrl}/api/v1/mcp/tools/${toolName}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.tool) {
        const tool = {
          ...data.tool,
          status: 'available',
          lastUsed: data.tool.lastUsed ? new Date(data.tool.lastUsed) : undefined,
          usageCount: data.tool.usageCount || 0
        };
        
        // Update cache
        this.toolCache.set(toolName, tool);
        return tool;
      } else {
        throw new Error('Tool not found or invalid response');
      }
    } catch (error) {
      console.error(`Failed to get tool ${toolName}:`, error);
      throw error;
    }
  }

  /**
   * Execute an MCP tool
   */
  async executeTool(request: MCPToolExecutionRequest): Promise<MCPToolExecutionResult> {
    try {
      const startTime = Date.now();
      
      // Transform frontend request format to backend format
      const backendRequest = {
        tool_name: request.toolName,
        parameters: request.parameters,
        session_id: request.sessionId || `session-${Date.now()}`,
        request_id: `req-${Date.now()}`,
        timeout: 30,
        priority: 'normal'
      };
      
      const response = await fetch(`${this.baseUrl}/api/v1/mcp/tools/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(backendRequest),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      const executionTime = Date.now() - startTime;

      if (data.status === 'success') {
        const result: MCPToolExecutionResult = {
          success: true,
          result: data.result,
          executionTime,
          timestamp: new Date(),
          metadata: data.metadata,
          toolName: request.toolName
        };

        // Update tool usage statistics
        this.updateToolUsage(request.toolName);
        
        return result;
      } else {
        const result: MCPToolExecutionResult = {
          success: false,
          result: null,
          executionTime,
          timestamp: new Date(),
          error: data.error || 'Tool execution failed',
          metadata: data.metadata,
          toolName: request.toolName
        };
        
        return result;
      }
    } catch (error) {
      const executionTime = Date.now() - Date.now();
      const result: MCPToolExecutionResult = {
        success: false,
        result: null,
        executionTime,
        timestamp: new Date(),
        error: error instanceof Error ? error.message : 'Unknown error occurred',
        toolName: request.toolName
      };
      
      return result;
    }
  }

  /**
   * Get tools by category
   */
  getToolsByCategory(category: string): MCPTool[] {
    return this.tools.filter(tool => tool.category === category);
  }

  /**
   * Search tools by name or description
   */
  searchTools(query: string): MCPTool[] {
    const lowerQuery = query.toLowerCase();
    return this.tools.filter(tool => 
      tool.name.toLowerCase().includes(lowerQuery) ||
      tool.description.toLowerCase().includes(lowerQuery) ||
      tool.category.toLowerCase().includes(lowerQuery)
    );
  }

  /**
   * Get tool categories
   */
  getCategories(): string[] {
    const categories = new Set(this.tools.map(tool => tool.category));
    return Array.from(categories).sort();
  }

  /**
   * Get recently used tools
   */
  getRecentlyUsedTools(limit: number = 5): MCPTool[] {
    return this.tools
      .filter(tool => tool.lastUsed)
      .sort((a, b) => (b.lastUsed?.getTime() || 0) - (a.lastUsed?.getTime() || 0))
      .slice(0, limit);
  }

  /**
   * Get most used tools
   */
  getMostUsedTools(limit: number = 5): MCPTool[] {
    return this.tools
      .sort((a, b) => b.usageCount - a.usageCount)
      .slice(0, limit);
  }

  /**
   * Validate tool parameters
   */
  validateToolParameters(tool: MCPTool, parameters: Record<string, any>): {
    isValid: boolean;
    errors: string[];
    warnings: string[];
  } {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Check required parameters
    tool.parameters.forEach(param => {
      if (param.required && !(param.name in parameters)) {
        errors.push(`Required parameter '${param.name}' is missing`);
      }
    });

    // Check parameter types and values
    Object.entries(parameters).forEach(([name, value]) => {
      const param = tool.parameters.find(p => p.name === name);
      if (!param) {
        warnings.push(`Unknown parameter '${name}'`);
        return;
      }

      // Type validation
      if (value !== null && value !== undefined) {
        const actualType = Array.isArray(value) ? 'array' : typeof value;
        if (actualType !== param.type) {
          errors.push(`Parameter '${name}' expects type '${param.type}', got '${actualType}'`);
        }
      }

      // Enum validation
      if (param.enum && !param.enum.includes(value)) {
        errors.push(`Parameter '${name}' must be one of: ${param.enum.join(', ')}`);
      }
    });

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Get tool execution history
   */
  async getToolExecutionHistory(toolName?: string, limit: number = 50): Promise<MCPToolExecutionResult[]> {
    try {
      const url = toolName 
        ? `${this.baseUrl}/api/v1/mcp/tools/${toolName}/history?limit=${limit}`
        : `${this.baseUrl}/api/v1/mcp/tools/history?limit=${limit}`;
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.success && data.history) {
        return data.history.map((item: any) => ({
          ...item,
          timestamp: new Date(item.timestamp),
          result: item.result
        }));
      } else {
        throw new Error(data.error || 'Failed to get execution history');
      }
    } catch (error) {
      console.error('Failed to get tool execution history:', error);
      throw error;
    }
  }

  /**
   * Test tool connectivity
   */
  async testToolConnectivity(toolName: string): Promise<{
    isAvailable: boolean;
    responseTime: number;
    error?: string;
  }> {
    try {
      const startTime = Date.now();
      
      const response = await fetch(`${this.baseUrl}/api/v1/mcp/tools/${toolName}/health`);
      const responseTime = Date.now() - startTime;

      if (!response.ok) {
        return {
          isAvailable: false,
          responseTime,
          error: `HTTP ${response.status}: ${response.statusText}`
        };
      }

      const data = await response.json();
      
      return {
        isAvailable: data.success || false,
        responseTime,
        error: data.success ? undefined : (data.error || 'Tool health check failed')
      };
    } catch (error) {
      return {
        isAvailable: false,
        responseTime: 0,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Update tool usage statistics
   */
  private updateToolUsage(toolName: string): void {
    const tool = this.tools.find(t => t.name === toolName);
    if (tool) {
      tool.lastUsed = new Date();
      tool.usageCount = (tool.usageCount || 0) + 1;
      
      // Update cache
      this.toolCache.set(toolName, tool);
    }
  }

  /**
   * Clear tool cache
   */
  clearCache(): void {
    this.tools = [];
    this.toolCache.clear();
    this.lastDiscovery = null;
  }

  /**
   * Get service status
   */
  async getServiceStatus(): Promise<{
    isConnected: boolean;
    toolsCount: number;
    lastDiscovery: Date | null;
    cacheSize: number;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/mcp/health`);
      
      if (!response.ok) {
        return {
          isConnected: false,
          toolsCount: 0,
          lastDiscovery: this.lastDiscovery,
          cacheSize: this.toolCache.size
        };
      }

      const data = await response.json();
      
      return {
        isConnected: data.success || false,
        toolsCount: this.tools.length,
        lastDiscovery: this.lastDiscovery,
        cacheSize: this.toolCache.size
      };
    } catch (error) {
      return {
        isConnected: false,
        toolsCount: 0,
        lastDiscovery: this.lastDiscovery,
        cacheSize: this.toolCache.size
      };
    }
  }
}

// Export singleton instance
export const mcpToolService = new MCPToolService();
export default mcpToolService;
