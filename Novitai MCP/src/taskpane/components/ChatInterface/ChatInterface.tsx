import * as React from 'react';
import { makeStyles, tokens } from '@fluentui/react-components';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { ChatMessage } from './MessageBubble';
import { MCPTool } from '../../services/types';
import { documentContextService } from '../../services/documentContextService';
import { officeIntegrationService } from '../../services/officeIntegrationService';
import { useState } from 'react';
import { getApiUrl } from '../../../config/backend';
import mcpToolService from '../../services/mcpToolService';

interface ChatInterfaceProps {
  onToolSelect?: (tool: MCPTool) => void;
  messages?: ChatMessage[];
  onMessage?: (message: ChatMessage) => void;
  loading?: boolean;
  onLoadingChange?: (loading: boolean) => void;
}

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    border: `1px solid ${tokens.colorNeutralStroke1}`,
    borderRadius: tokens.borderRadiusMedium,
    backgroundColor: tokens.colorNeutralBackground2,
    overflow: 'hidden',
    minHeight: 0,
  },
  messagesContainer: {
    flex: 1,
    overflow: 'hidden',
    padding: '8px',
    minHeight: 0,
    '@media (min-width: 768px)': {
      padding: '12px',
    },
  },
  inputContainer: {
    borderTop: `1px solid ${tokens.colorNeutralStroke1}`,
    paddingBottom: '2px',
    flexShrink: 0,
  },
});

const ChatInterface: React.FC<ChatInterfaceProps> = ({ 
  messages: externalMessages = [],
  onMessage,
  loading: externalLoading = false,
  onLoadingChange
}) => {
  const styles = useStyles();
  const [internalMessages, setInternalMessages] = useState<ChatMessage[]>([]);
  const [internalLoading, setInternalLoading] = useState(false);
  const [availableTools, setAvailableTools] = useState<MCPTool[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  
  const messages = externalMessages.length > 0 ? externalMessages : internalMessages;
  const loading = externalLoading || internalLoading;
  
  // Using mcpToolService instead of mcpService

  React.useEffect(() => {
    if (externalMessages.length === 0) {
      setInternalMessages([{
        id: '1',
        type: 'assistant',
        content: 'Hello! I\'m your AI assistant. I can help you with document processing, web research, and more. What would you like to do today?',
        timestamp: new Date()
      }]);
    }
    
    // Load available tools
    loadAvailableTools();
  }, [externalMessages.length]);

  const loadAvailableTools = async () => {
    try {
      setError(null);
      const tools = await mcpToolService.discoverTools();
      setAvailableTools(tools);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load tools';
      setError(errorMessage);
      console.error('Failed to load tools:', error);
    } finally {
      setIsInitializing(false);
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: content.trim(),
      timestamp: new Date()
    };

    if (onMessage) {
      onMessage(userMessage);
    } else {
      setInternalMessages(prev => [...prev, userMessage]);
    }
    setInputValue('');
    if (onLoadingChange) {
      onLoadingChange(true);
    } else {
      setInternalLoading(true);
    }

    try {
      await handleUserIntentWithAgent(content.trim());
    } catch (error) {
      console.error('💥 Error handling user message:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'system',
        content: `❌ Error processing your request: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
        metadata: { error: error instanceof Error ? error.message : 'Unknown error' }
      };
      if (onMessage) {
        onMessage(errorMessage);
      } else {
        setInternalMessages(prev => [...prev, errorMessage]);
      }
    } finally {
      if (onLoadingChange) {
        onLoadingChange(false);
      } else {
        setInternalLoading(false);
      }
    }
  };

  // Handle user intent with backend agent (same pattern as standalone frontend)
  const handleUserIntentWithAgent = async (userMessage: string) => {
    try {
      // Check if this is a response to an insertion offer
      if (userMessage.toLowerCase().includes('insert') || userMessage.toLowerCase().includes('yes')) {
        const lastMessage = messages[messages.length - 1];
        if (lastMessage?.metadata?.insertionOffer) {
          console.log('🔄 Handling insertion response...');
          await handleContentInsertion(lastMessage.metadata.searchContent, lastMessage.metadata.userRequest);
          return; // Skip normal intent detection
        }
      }
      
      console.log('🔍 Starting intent detection for:', userMessage);
      
      // Step 1: Get available tools
      const availableTools = await mcpToolService.discoverTools();
      console.log('📚 Available tools:', availableTools);
      
      // Step 2: Send to backend agent for intent detection
      console.log('🚀 Calling intent detection API...');
      
      // Get conversation history from current messages
      const conversationHistory = messages.slice(-5).map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content,
        timestamp: msg.timestamp
      }));
      
      // Get document content from Word using Office integration
      let documentContent = '';
      try {
        documentContent = await officeIntegrationService.getDocumentContent();
        console.log('Document content length:', documentContent.length);
        
        // Truncate if too long (backend has limits)
        if (documentContent.length > 5000) {
          documentContent = documentContent.substring(0, 5000) + '... [truncated]';
          console.log('Document content truncated to 5000 chars');
        }
      } catch (error) {
        console.warn('Failed to get document content:', error);
        documentContent = 'Document content unavailable';
      }
      
      console.log('📚 Conversation history for context:', conversationHistory);
      console.log('📄 Document content for context:', documentContent.substring(0, 100) + '...');
      
      // Use our new agent chat method
      const agentResponse = await mcpToolService.chatWithAgent({
        message: userMessage,
        context: {
          document_content: documentContent,
          chat_history: JSON.stringify(conversationHistory),
          available_tools: availableTools.map(t => t.name).join(', ')
        },
        sessionId: `session-${Date.now()}`
      });

      console.log('🎯 Agent response:', agentResponse);

      if (agentResponse.success && agentResponse.result) {
        // The agent has already handled tool execution and routing
        const agentMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: agentResponse.result.response || 'Agent processed your request successfully',
          timestamp: new Date(),
          metadata: {
            agentResponse: true,
            toolUsed: agentResponse.result.tool_name,
            intentType: agentResponse.result.intent_type
          }
        };

        if (onMessage) {
          onMessage(agentMessage);
        } else {
          setInternalMessages(prev => [...prev, agentMessage]);
        }
      } else {
        throw new Error(agentResponse.error || 'Agent failed to process request');
      }

    } catch (error) {
      console.error('Intent detection failed:', error);
      
      // Show specific error message to user (matching standalone frontend)
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `I encountered an error while processing your request: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`,
        timestamp: new Date(),
        metadata: { error: 'true', intent_detection_failed: true }
      };

      if (onMessage) {
        onMessage(errorMessage);
      } else {
        setInternalMessages(prev => [...prev, errorMessage]);
      }
      
      // Stop execution and show error to user (matching standalone frontend)
      return;
    }
  };

  // Agent now handles tool execution automatically
  // The agent service will handle all tool routing and execution

  // Get insertion offer text for search results
  const getInsertionOfferText = async (_searchContent: any, userRequest: string): Promise<string | null> => {
    try {
      // Check if we have Office.js available
      const isOfficeReady = await officeIntegrationService.checkOfficeReady();
      if (!isOfficeReady) {
        console.log('Office.js not available, skipping content insertion offer');
        return null;
      }

      // Check if text is selected for replacement
      const hasSelection = await officeIntegrationService.hasSelection();
      
      if (hasSelection) {
        return `I found information about "${userRequest}". Would you like me to replace the selected text with a summary of these search results? Click "Insert" to proceed.`;
      } else {
        return `I found information about "${userRequest}". Would you like me to add a summary of these search results to your document? Click "Insert" to proceed.`;
      }
    } catch (error) {
      console.error('Failed to get insertion offer text:', error);
      return null;
    }
  };

  // Handle content insertion when user accepts
  const handleContentInsertion = async (searchContent: any, userRequest: string) => {
    try {
      const isOfficeReady = await officeIntegrationService.checkOfficeReady();
      if (!isOfficeReady) {
        throw new Error('Office.js not available');
      }

      // Extract summary from search content
      let contentToInsert = '';
      if (typeof searchContent === 'string') {
        contentToInsert = searchContent;
      } else if (searchContent.content) {
        contentToInsert = searchContent.content;
      } else if (searchContent.summary) {
        contentToInsert = searchContent.summary;
      } else {
        contentToInsert = `Information about: ${userRequest}`;
      }

      // Check if text is selected for replacement
      const hasSelection = await officeIntegrationService.hasSelection();
      
      if (hasSelection) {
        // Replace selected text
        await officeIntegrationService.replaceSelectedText(contentToInsert, {
          location: 'selection',
          format: 'withSource',
          source: `Web search for: ${userRequest}`
        });
        
        const successMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: `✅ I've replaced the selected text with information about "${userRequest}".`,
          timestamp: new Date(),
          metadata: { 
            toolUsed: 'content_insertion',
            success: true,
            action: 'replaced_selection'
          }
        };

        if (onMessage) {
          onMessage(successMessage);
        } else {
          setInternalMessages(prev => [...prev, successMessage]);
        }
      } else {
        // Add to end of document
        await officeIntegrationService.insertText(contentToInsert, {
          location: 'end',
          format: 'withSource',
          source: `Web search for: ${userRequest}`
        });
        
        const successMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: `✅ I've added information about "${userRequest}" to your document.`,
          timestamp: new Date(),
          metadata: { 
            toolUsed: 'content_insertion',
            success: true,
            action: 'added_to_end'
          }
        };

        if (onMessage) {
          onMessage(successMessage);
        } else {
          setInternalMessages(prev => [...prev, successMessage]);
        }
      }
    } catch (error) {
      console.error('Failed to insert content:', error);
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `❌ Failed to insert content: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
        metadata: { 
          error: 'true',
          toolUsed: 'content_insertion',
          failed: true
        }
      };

      if (onMessage) {
        onMessage(errorMessage);
      } else {
        setInternalMessages(prev => [...prev, errorMessage]);
      }
    }
  };

  // Prepare tool parameters (same logic as standalone frontend)
  const prepareToolParameters = async (toolName: string, userRequest: string): Promise<any> => {
          console.log('Preparing parameters for tool:', toolName, 'with request:', userRequest);
    
    const params: any = {};

    switch (toolName) {
      case 'web_content_fetcher':
        const urlMatch = userRequest.match(/https?:\/\/[^\s]+/);
        if (urlMatch) {
          params.url = urlMatch[0];
          console.log('URL detected:', params.url);
        } else {
          // Enhanced search query extraction for "web search for X" patterns
          const searchMatch = userRequest.match(/(?:web\s+)?search\s+(?:for\s+)?(.+)/i);
          if (searchMatch) {
            params.query = searchMatch[1].trim();
            console.log('Search query extracted:', params.query);
          } else {
            // Fallback: treat entire request as search query
            params.query = userRequest;
            console.log('Using full request as search query:', params.query);
          }
          
          // Set backend-expected parameters
          params.extract_type = 'summary';  // ✅ CORRECT: Backend expects this
          params.max_length = 500;          // ✅ CORRECT: Backend expects this
        }
        break;
      
      case 'text_processor':
        params.text = userRequest;
        params.operation = 'summarize';
        console.log('Text processing params:', params);
        break;
      
      case 'document_analyzer':
        params.content = userRequest;
        params.analysis_type = 'summary';
        console.log('Document analysis params:', params);
        break;
      
      default:
        params.input = userRequest;
        console.log('Default params for unknown tool:', params);
    }
    
    console.log('Final tool parameters:', params);
    return params;
  };

  // Execute conversational AI
  const executeConversationalAI = async (userMessage: string) => {
    try {
      setInternalLoading(true);
      setError(null);

      // Get document content
      let documentContent = '';
      try {
        documentContent = await officeIntegrationService.getDocumentContent();
      } catch (error) {
        console.warn('Failed to get document content:', error);
        documentContent = 'Document content unavailable';
      }

      // Truncate document content if too long
      if (documentContent.length > 5000) {
        documentContent = documentContent.substring(0, 5000) + '...';
      }

      // Format chat history as string
      const chatHistoryString = messages
        .map(msg => `${msg.type}: ${msg.content}`)
        .join('\n');

      // Send message to agent chat endpoint
      const response = await mcpToolService.sendAgentMessage({
        message: userMessage,
        context: {
          document_content: documentContent,
          chat_history: chatHistoryString
        }
      });

      // Add AI response to messages
      const aiMessage: ChatMessage = {
        id: Date.now().toString(),
        type: 'assistant',
        content: response.response,
        timestamp: new Date()
      };

      setInternalMessages(prev => [...prev, aiMessage]);

      // Log agent response details
      console.log('Agent Response:', {
        intent_type: response.intent_type,
        tools_used: response.tools_used,
        execution_time: response.execution_time,
        reasoning: response.reasoning
      });

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Conversational AI failed';
      setError(errorMessage);
      console.error('Conversational AI error:', error);
    } finally {
      setInternalLoading(false);
    }
  };

    // Format tool result (EXACTLY matching working frontend)
  const formatToolResult = (result: any, _userRequest: string): string => {
    console.log('Formatting tool result:', result);
    
    if (!result.success) {
      return `❌ ${result.error || 'Something went wrong. Please try again.'}`;
    }

    // Enhanced debugging: log the actual result structure
    console.log('Result structure:', {
      hasResult: !!result.result,
      resultType: typeof result.result,
      resultKeys: result.result ? Object.keys(result.result) : 'no result',
      resultValue: result.result
    });

    if (result.result && typeof result.result === 'object' && result.result.content) {
      const backendResult = result.result.content;
      
      console.log('Backend result.content fields:', Object.keys(backendResult));
      console.log('Backend result.content values:', backendResult);
      
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



  const handleAttach = () => {
    console.log('Attach functionality to be implemented');
  };

  return (
    <div className={styles.container}>
      <div className={styles.messagesContainer}>
        <MessageList 
          messages={messages}
          loading={loading}
        />
      </div>
      <div className={styles.inputContainer}>
        <MessageInput
          value={inputValue}
          onChange={setInputValue}
          onSend={handleSendMessage}
          onAttach={handleAttach}
          disabled={loading}
          placeholder="Type your message here..."
        />
      </div>
    </div>
  );
};

export default ChatInterface;
