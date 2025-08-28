import React, { useState, useEffect } from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { Message } from './MessageBubble';
import mcpToolService, { MCPTool, MCPToolExecutionRequest, MCPToolExecutionResult } from '../services/mcpToolService';

interface ChatInterfaceProps {}

const ChatInterface: React.FC<ChatInterfaceProps> = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [availableTools, setAvailableTools] = useState<MCPTool[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Load available tools on component mount
  useEffect(() => {
    loadAvailableTools();
  }, []);

  const loadAvailableTools = async () => {
    try {
      const tools = await mcpToolService.discoverTools();
      setAvailableTools(tools);
    } catch (err) {
      console.error('Failed to load tools:', err);
      setError('Failed to load available tools');
    }
  };

  const handleSendMessage = async (content: string, messageType?: string, metadata?: any) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date(),
      metadata
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      // Check if user wants to use a specific tool
      if (metadata?.toolSelected) {
        await executeTool(metadata.toolSelected, content, metadata);
      } else {
        // Use intelligent agent for intent detection and routing
        await handleUserIntentWithAgent(content);
      }
    } catch (err) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `I encountered an error while processing your request: ${err instanceof Error ? err.message : 'Unknown error'}`,
        timestamp: new Date(),
        metadata: {
          error: err instanceof Error ? err.message : 'Unknown error'
        }
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const executeTool = async (toolName: string, userRequest: string, metadata?: any) => {
    try {
      // Find the tool
      const tool = availableTools.find(t => t.name === toolName);
      if (!tool) {
        throw new Error(`Tool '${toolName}' not found`);
      }

      // Add tool execution message
      const executionMessage: Message = {
        id: Date.now().toString(),
        type: 'system',
        content: `Executing ${toolName} tool...`,
        timestamp: new Date(),
        metadata: {
          toolSelected: toolName,
          status: 'executing'
        }
      };
      setMessages(prev => [...prev, executionMessage]);

      // Prepare tool execution request
      const request: MCPToolExecutionRequest = {
        toolName,
        parameters: await prepareToolParameters(toolName, userRequest, tool),
        sessionId: metadata?.sessionId,
        userId: metadata?.userId
      };

      // Execute the tool
      const result = await mcpToolService.executeTool(request);

      // Add clean AI response message
      const resultMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: formatToolResult(result),
        timestamp: new Date(),
        metadata: {
          toolUsed: toolName,
          success: result.success
        }
      };
      setMessages(prev => [...prev, resultMessage]);

      // Remove the execution message since we now show the clean result
      setMessages(prev => prev.filter(msg => 
        !(msg.metadata?.toolSelected === toolName && msg.metadata?.status === 'executing')
      ));

    } catch (err) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `Failed to execute ${toolName}: ${err instanceof Error ? err.message : 'Unknown error'}`,
        timestamp: new Date(),
        metadata: {
          error: err instanceof Error ? err.message : 'Unknown error',
          toolUsed: toolName
        }
      };
      setMessages(prev => [...prev, errorMessage]);

      // Update the execution message to show failure
      setMessages(prev => prev.map(msg => 
        msg.metadata?.toolSelected === toolName && msg.metadata?.status === 'executing'
          ? { ...msg, content: `❌ ${toolName} failed`, metadata: { ...msg.metadata, status: 'failed' } }
          : msg
      ));
    }
  };

  const prepareToolParameters = async (toolName: string, userRequest: string, tool: MCPTool): Promise<Record<string, any>> => {
    // Default parameter preparation based on tool type
    const params: Record<string, any> = {};
    
    switch (toolName) {
      case 'document_analyzer':
        // For document analyzer, we need a document path
        // In a real scenario, this would come from file upload or document selection
        params.document_path = '/sample/document.txt'; // Placeholder
        params.analysis_type = 'full';
        break;
      
      case 'text_processor':
        // For text processor, use the user's request as input text
        params.text = userRequest;
        params.operation = 'summarize';
        break;
      
      case 'web_content_fetcher':
        // For web content fetcher, handle both URLs and search queries
        const urlMatch = userRequest.match(/https?:\/\/[^\s]+/);
        if (urlMatch) {
          // URL fetch request
          params.url = urlMatch[0];
        } else {
          // Search query request - extract search terms
          const searchMatch = userRequest.match(/search.*?for\s+(.+)/i);
          if (searchMatch) {
            params.query = searchMatch[1].trim();
            params.max_results = 10;
            params.search_engine = 'google';
            params.include_abstracts = true;
          } else {
            // Fallback: treat the entire request as a search query
            params.query = userRequest;
            params.max_results = 10;
            params.search_engine = 'google';
            params.include_abstracts = true;
          }
        }
        break;
      
      case 'file_reader':
        // For file reader, we need a file path
        params.file_path = '/sample/file.txt'; // Placeholder
        params.encoding = 'utf-8';
        break;
      
      default:
        // For other tools, try to use the user request as a parameter
        if (tool.parameters && tool.parameters.length > 0) {
          const firstParam = tool.parameters[0];
          if (firstParam.type === 'string') {
            params[firstParam.name] = userRequest;
          }
        }
    }
    
    return params;
  };

  const formatToolResult = (result: MCPToolExecutionResult): string => {
    if (!result.success) {
      return `❌ ${result.error || 'Something went wrong. Please try again.'}`;
    }

    if (result.result && typeof result.result === 'object' && result.result.content) {
      const backendResult = result.result.content;
      
      // For web content fetcher, show the content
      if (backendResult.content && backendResult.source_type === 'fallback_search') {
        return backendResult.content;
      }
      
      // For web content fetcher with real results
      if (backendResult.content && backendResult.url && backendResult.url !== 'search://' + backendResult.query) {
        return `📄 **Search Results for "${backendResult.query}"**\n\n${backendResult.content}`;
      }
      
      // For text processing tools, show only the AI response
      if (backendResult.processed_text) {
        return backendResult.processed_text;
      }
      
      // For document analysis, show the summary
      if (backendResult.summary) {
        return backendResult.summary;
      }
      
      // Fallback to processed text if available
      if (backendResult.analysis) {
        return backendResult.analysis;
      }
      
      // For web content fetcher fallback
      if (backendResult.content) {
        return backendResult.content;
      }
    }
    
    // Fallback for other result types
    if (typeof result.result === 'string') {
      return result.result;
    }
    
    return 'Processing completed successfully.';
  };



  // New intelligent agent-based intent detection
  const handleUserIntentWithAgent = async (content: string) => {
    console.log('Starting agent-based intent detection for:', content);
    
    try {
      // Prepare conversation history for context
      const conversationHistory = messages.slice(-5).map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content,
        timestamp: msg.timestamp
      }));
      
      console.log('Conversation history:', conversationHistory);
      
      // Get document content if available (placeholder for now)
      const documentContent = ""; // TODO: Extract from Word document
      
      console.log('Calling agent service...');
      
      // Use intelligent agent service for intent detection and routing
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:9000'}/api/v1/mcp/agent/intent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content,
          conversation_history: conversationHistory,
          document_content: documentContent,
          available_tools: availableTools
        }),
      });
      
      console.log('Agent service response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('Agent response received:', data);
        console.log('Agent response status:', data.status);
        
        if (data.status === 'success') {
          const { intent_type, routing_decision, parameters, reasoning } = data;
          
          console.log('Agent routing decision', {
            intent: intent_type,
            routing_decision: routing_decision,
            reasoning: reasoning
          });
          
          // Route based on agent decision
          console.log('Routing decision:', routing_decision, 'Intent type:', intent_type);
          console.log('Routing decision type:', typeof routing_decision);
          console.log('Routing decision === "conversational_ai":', routing_decision === 'conversational_ai');
          console.log('Routing decision === conversational_ai:', routing_decision === 'conversational_ai');
          
          if (routing_decision === 'conversational_ai' || routing_decision?.toLowerCase() === 'conversational_ai') {
            console.log('Routing to conversational AI...');
            // Get conversational response from agent
            const convResponse = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:9000'}/api/v1/mcp/conversation`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                message: content,
                context: intent_type
              }),
            });
            
            console.log('Conversational response status:', convResponse.status);
            
            if (convResponse.ok) {
              const convData = await convResponse.json();
              console.log('Conversational response data:', convData);
              
              if (convData.status === 'success') {
                const aiMessage: Message = {
                  id: (Date.now() + 1).toString(),
                  type: 'assistant',
                  content: convData.response,
                  timestamp: new Date(),
                  metadata: { 
                    intent_type, 
                    routing_decision, 
                    aiGenerated: true,
                    reasoning 
                  }
                };
                setMessages(prev => [...prev, aiMessage]);
                console.log('Conversational message added to chat');
                return;
              }
            }
          } else {
            console.log('Routing to tool execution:', routing_decision);
            console.log('Why did conversational_ai not match? routing_decision value:', JSON.stringify(routing_decision));
            // Execute appropriate tool based on routing decision
            const toolName = parameters.tool_name || routing_decision;
            await executeTool(toolName, content, parameters);
            return;
          }
        }
      }
    } catch (err) {
      console.error('Agent service failed:', err);
      
      // Show specific error message to user
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `I encountered an error while processing your request: ${err instanceof Error ? err.message : 'Unknown error'}. Please try again.`,
        timestamp: new Date(),
        metadata: { error: 'true', agent_failed: true }
      };
      setMessages(prev => [...prev, errorMessage]);
      return;
    }
    
    // Fallback: show error message instead of executing text processor
    const errorMessage: Message = {
      id: (Date.now() + 1).toString(),
      type: 'assistant',
      content: `I'm having trouble processing your request. Please try again or ask me something specific about document analysis or text processing.`,
      timestamp: new Date(),
      metadata: { error: 'true', fallback: true }
    };
    setMessages(prev => [...prev, errorMessage]);
  };

  const handleFileUpload = async (file: File) => {
    // Add file upload message
    const fileMessage: Message = {
      id: Date.now().toString(),
      type: 'system',
      content: `File uploaded: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`,
      timestamp: new Date(),
      metadata: {
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type
      }
    };
    
    setMessages(prev => [...prev, fileMessage]);
    
    // Process file with backend
    setIsLoading(true);
    try {
      // Store file info for later use with tools
      const fileInfo = {
        name: file.name,
        size: file.size,
        type: file.type,
        // In a real app, you'd upload the file to the backend here
        // For now, we'll simulate processing
      };
      
      const processedMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `I've processed your file "${file.name}". I can now help you analyze it using the Document Analyzer tool, extract content with the File Reader, or process the text with the Text Processor.\n\nWhat would you like me to do with this file?`,
        timestamp: new Date(),
        metadata: {
          fileProcessed: file.name,
          fileInfo: fileInfo,
          suggestedTools: ['document_analyzer', 'file_reader', 'text_processor']
        }
      };
      
      setMessages(prev => [...prev, processedMessage]);
    } catch (err) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `Failed to process file "${file.name}": ${err instanceof Error ? err.message : 'Unknown error'}`,
        timestamp: new Date(),
        metadata: {
          error: err instanceof Error ? err.message : 'Unknown error',
          fileName: file.name
        }
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-xl font-semibold text-gray-900">
          AI Assistant with MCP Tools
        </h1>
        <p className="text-sm text-gray-600 mt-1">
          Ask questions, analyze documents, and use powerful MCP tools to enhance your work
        </p>
        {error && (
          <div className="mt-2 p-2 bg-red-100 border border-red-300 rounded text-red-700 text-sm">
            ⚠️ {error}
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6">
        <MessageList messages={messages} />
        
        {/* Quick Actions */}
        {messages.length === 0 && (
          <div className="text-center py-8">
            <div className="text-gray-500 mb-4">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Welcome to your AI Assistant!</h3>
            <p className="text-gray-600 mb-4">
              I'm here to help you with document analysis, text processing, and more using powerful MCP tools.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                onClick={() => handleSendMessage('What tools do you have available?')}
                className="text-xs text-primary-600 hover:text-primary-700 underline"
              >
                Show available tools
              </button>
              <button
                onClick={() => handleSendMessage('Help me analyze a document')}
                className="text-xs text-primary-600 hover:text-primary-700 underline"
              >
                Document Analysis Help
              </button>
              <button
                onClick={() => handleSendMessage('How can I process text content?')}
                className="text-xs text-primary-600 hover:text-primary-700 underline"
              >
                Text Processing Help
              </button>
              <button
                onClick={() => handleSendMessage('What can you do with files?')}
                className="text-xs text-primary-600 hover:text-primary-700 underline"
              >
                File Operations Help
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-6">
        <MessageInput
          onSendMessage={handleSendMessage}
          onFileUpload={handleFileUpload}
          availableTools={availableTools}
          showToolSelector={true}
          showFileUpload={true}
          disabled={isLoading}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
};

export default ChatInterface;
