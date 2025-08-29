import axios from 'axios';

export interface MCPTool {
  name: string;
  description: string;
  parameters?: Record<string, any>;
}

export interface MCPToolExecutionRequest {
  tool_name: string;
  parameters: Record<string, any>;
  session_id?: string;
  user_id?: string;
}

export interface MCPToolExecutionResult {
  success: boolean;
  data?: any;
  error?: string;
  status: string;
}

export interface MCPConnectionStatus {
  connected: boolean;
  server_url: string;
  last_check: Date;
}

class MCPService {
  private baseUrl: string;
  private sessionId: string;
  private userId: string;

  constructor() {
    // Default to localhost:8000 for development
    this.baseUrl = process.env.NODE_ENV === 'production' 
      ? 'https://your-production-domain.com' 
      : 'http://localhost:8000';
    
    // Generate unique session and user IDs
    this.sessionId = `word-addin-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    this.userId = `user-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Test connection to MCP server
   */
  async testConnection(): Promise<MCPConnectionStatus> {
    try {
      const response = await axios.get(`${this.baseUrl}/health`, { timeout: 5000 });
      return {
        connected: response.status === 200,
        server_url: this.baseUrl,
        last_check: new Date()
      };
    } catch (error) {
      return {
        connected: false,
        server_url: this.baseUrl,
        last_check: new Date()
      };
    }
  }

  /**
   * Get available MCP tools
   */
  async getAvailableTools(): Promise<MCPTool[]> {
    try {
      console.log('Fetching MCP tools from:', `${this.baseUrl}/api/v1/mcp/tools`);
      const response = await axios.get(`${this.baseUrl}/api/v1/mcp/tools`);
      console.log('MCP tools response:', response.data);
      return response.data.tools || [];
    } catch (error) {
      console.error('Error fetching MCP tools:', error);
      return [];
    }
  }

  /**
   * Execute an MCP tool
   */
  async executeTool(request: MCPToolExecutionRequest): Promise<MCPToolExecutionResult> {
    try {
      const response = await axios.post(`${this.baseUrl}/api/v1/mcp/tools/execute`, {
        ...request,
        session_id: this.sessionId,
        user_id: this.userId
      });

      return {
        success: response.data.success || false,
        data: response.data.data,
        error: response.data.error,
        status: response.data.status || 'completed'
      };
    } catch (error: any) {
      console.error('Error executing MCP tool:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Unknown error',
        status: 'error'
      };
    }
  }

  /**
   * Get document content from Word
   */
  async getDocumentContent(): Promise<string> {
    return new Promise((resolve, reject) => {
      try {
        Word.run(async (context) => {
          const body = context.document.body;
          body.load('text');
          
          await context.sync();
          
          const text = body.text || '';
          resolve(text);
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Insert text into Word document
   */
  async insertText(text: string, location: Word.InsertLocation = Word.InsertLocation.end): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        Word.run(async (context) => {
          const body = context.document.body;
          body.insertParagraph(text, location as any);
          
          await context.sync();
          resolve();
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Replace selected text in Word document
   */
  async replaceSelectedText(text: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        Word.run(async (context) => {
          const selection = context.document.getSelection();
          selection.load('text');
          
          await context.sync();
          
          if (selection.text) {
            selection.insertText(text, Word.InsertLocation.replace as any);
            await context.sync();
          }
          
          resolve();
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Get selected text from Word document
   */
  async getSelectedText(): Promise<string> {
    return new Promise((resolve, reject) => {
      try {
        Word.run(async (context) => {
          const selection = context.document.getSelection();
          selection.load('text');
          
          await context.sync();
          
          resolve(selection.text || '');
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Update base URL (useful for configuration)
   */
  updateBaseUrl(newUrl: string): void {
    this.baseUrl = newUrl;
  }

  /**
   * Get current configuration
   */
  getConfiguration() {
    return {
      baseUrl: this.baseUrl,
      sessionId: this.sessionId,
      userId: this.userId
    };
  }
}

export default MCPService;
