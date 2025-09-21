import { useState, useRef, useCallback, useMemo } from 'react';
import { ChatMessage } from '../components/ChatInterface/MessageBubble';
import { StreamingEvent, StreamingProgress, MCPTool } from '../services/types';
import mcpToolService from '../services/mcpToolService';
import { officeIntegrationService } from '../services/officeIntegrationService';

interface UseStreamingChatProps {
  messages?: ChatMessage[];
  onMessage?: (message: ChatMessage) => void;
  onLoadingChange?: (loading: boolean) => void;
}

export const useStreamingChat = ({ messages: externalMessages = [], onMessage, onLoadingChange }: UseStreamingChatProps) => {
  // Use onLoadingChange to avoid unused parameter warning
  const handleLoadingChange = onLoadingChange || (() => {});
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingProgress, setStreamingProgress] = useState<StreamingProgress>({
    currentStep: 0,
    totalSteps: 0,
    status: 'complete'
  });
  
  const streamingResponseRef = useRef('');
  const [internalMessages, setInternalMessages] = useState<ChatMessage[]>([]);
  const [currentUserMessageId, setCurrentUserMessageId] = useState<string | null>(null);
  
  // During streaming, always use internal messages for real-time updates
  // When not streaming, use external messages if available (for persistence across tab switches)
  const messages = isStreaming ? internalMessages : (externalMessages.length > 0 ? externalMessages : internalMessages);

  const resetStreamingState = useCallback(() => {
    setIsStreaming(false);
    setStreamingProgress({
      currentStep: 0,
      totalSteps: 0,
      status: 'complete'
    });
    streamingResponseRef.current = '';
    setCurrentUserMessageId(null); // Clear current user message ID
  }, []);

  const updateStreamingMessage = useCallback((messageId: string, content: string, metadata: any) => {
    // Always use internal state for streaming updates to avoid creating multiple bubbles
    // The parent will receive the final message via onMessage in the completion handler
    setInternalMessages(prev => 
      prev.map(msg => msg.id === messageId ? {
        ...msg,
        content,
        metadata: { ...msg.metadata, ...metadata }
      } : msg)
    );
  }, []);

  const handleStreamingEvent = useCallback((event: StreamingEvent, messageId: string) => {
    if (event.event_type === 'langgraph_chunk') {
      const data = event.data;
      
      // Handle node updates
      if (data.updates?.updates) {
        for (const [nodeName, nodeData] of Object.entries(data.updates.updates)) {
          if (['workflow_planning', 'response_generation', 'intent_detection'].includes(nodeName)) {
            const status = nodeName === 'intent_detection' ? 'intent_detection' :
                          nodeName === 'workflow_planning' ? 'tool_execution' : 'response_generation';
            
            setStreamingProgress(prev => ({
              ...prev,
              status,
              currentStep: prev.currentStep + 1
            }));

            const progressText = status === 'intent_detection' ? '🔍 Detecting intent...' :
                               status === 'tool_execution' ? '⚙️ Planning workflow...' :
                               status === 'response_generation' ? '✍️ Generating response...' : '🤔 Thinking...';
            
            // Check if this node contains a final_response
            if (nodeName === 'response_generation' && nodeData && typeof nodeData === 'object' && 'final_response' in nodeData) {
              streamingResponseRef.current = (nodeData as any).final_response;
              updateStreamingMessage(messageId, streamingResponseRef.current, {
                streamingProgress: status
              });
            } else {
              updateStreamingMessage(messageId, `${progressText}\n\n${streamingResponseRef.current || 'Processing...'}`, {
                streamingProgress: status
              });
            }
          }
        }
      }
      
      // Handle LLM token streaming
      if (data.messages?.length > 0) {
        for (const message of data.messages) {
          if (message?.content) {
            streamingResponseRef.current += message.content;
            updateStreamingMessage(messageId, streamingResponseRef.current, {
              streamingProgress: 'response_generation'
            });
          }
        }
      }
    } else if (event.event_type === 'llm_response') {
      // Handle direct LLM response events
      const data = event.data;
      if (data?.content) {
        streamingResponseRef.current = data.content;
        updateStreamingMessage(messageId, streamingResponseRef.current, {
          streamingProgress: 'response_generation'
        });
      }
    }
  }, [updateStreamingMessage]);

  // Memoize conversation history to avoid recalculation
  // Use external messages if available (for persistence), otherwise use internal messages
  // But exclude the current streaming message to avoid context confusion
  const conversationHistory = useMemo(() => {
    const sourceMessages = externalMessages.length > 0 ? externalMessages : internalMessages;
    return sourceMessages
      .filter(msg => 
        !msg.metadata?.isStreaming && 
        msg.type !== 'system' && 
        msg.content.trim() !== '' &&
        msg.id !== currentUserMessageId // Exclude current user message from context
      )
      .slice(-50)
      .map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content,
        timestamp: msg.timestamp
      }));
  }, [externalMessages, internalMessages, currentUserMessageId]);

  const startStreamingChat = useCallback(async (userMessage: string) => {
    try {
      setIsStreaming(true);
      streamingResponseRef.current = '';

      // Set current user message ID first (before conversation history calculation)
      const userMessageId = Date.now().toString();
      setCurrentUserMessageId(userMessageId);
      
      // Add user message to internal state
      const userMessageObj: ChatMessage = {
        id: userMessageId,
        type: 'user',
        content: userMessage,
        timestamp: new Date()
      };
      setInternalMessages(prev => [...prev, userMessageObj]);

      // Calculate conversation history from the updated messages (including current user message)
      // then exclude the current user message to send only previous conversation to backend
      const sourceMessages = externalMessages.length > 0 ? externalMessages : internalMessages;
      const updatedMessages = [...sourceMessages, userMessageObj]; // Include current user message
      const currentConversationHistory = updatedMessages
        .filter(msg => 
          !msg.metadata?.isStreaming && 
          msg.type !== 'system' && 
          msg.content.trim() !== '' &&
          msg.id !== userMessageId // Exclude current user message
        )
        .slice(-50)
        .map(msg => ({
          role: msg.type === 'user' ? 'user' : 'assistant',
          content: msg.content,
          timestamp: msg.timestamp
        }));

      // Constants for better maintainability
      const MAX_DOCUMENT_LENGTH = 10000;

      // Get document content with error handling
      let documentContent = '';
      try {
        documentContent = await officeIntegrationService.getDocumentContent();
        if (documentContent.length > MAX_DOCUMENT_LENGTH) {
          documentContent = documentContent.substring(0, MAX_DOCUMENT_LENGTH) + '... [truncated]';
        }
      } catch (error) {
        console.warn('Failed to get document content:', error);
        documentContent = 'Document content unavailable';
      }

      // Get available tools with error handling and proper typing
      let availableTools: MCPTool[] = [];
      try {
        const toolsData = await mcpToolService.discoverTools();
        availableTools = Array.isArray(toolsData) ? toolsData : [];
      } catch (error) {
        console.warn('Failed to get available tools:', error);
        availableTools = [];
      }

      // Create streaming message
      const streamingMessageId = (Date.now() + 1).toString();
      const initialMessage: ChatMessage = {
        id: streamingMessageId,
        type: 'assistant',
        content: '🤔 Thinking...',
        timestamp: new Date(),
        metadata: { isStreaming: true, streamingProgress: 'intent_detection' }
      };

      // Always add to internal state for streaming updates
      setInternalMessages(prev => [...prev, initialMessage]);

      // Debug: Log what we're sending
      console.log('🔍 Streaming Debug:', {
        userMessage,
        conversationHistoryLength: currentConversationHistory.length,
        conversationHistory: currentConversationHistory.map(msg => ({ role: msg.role, content: msg.content.substring(0, 50) + '...' })),
        documentContentLength: documentContent.length,
        availableToolsCount: availableTools.length
      });

      // Start streaming
      await mcpToolService.chatWithAgentStreaming({
        message: userMessage,
        context: {
          document_content: documentContent,
          chat_history: JSON.stringify(currentConversationHistory),
          available_tools: availableTools.map(t => t.name).join(', ')
        },
        sessionId: `session-${Date.now()}`,
        callbacks: {
          onEvent: (event) => handleStreamingEvent(event, streamingMessageId),
          onComplete: (finalResponse) => {
            const finalContent = streamingResponseRef.current || finalResponse?.final_response || 'Request completed successfully';
            
            // Update internal state with final content
            setInternalMessages(prev => 
              prev.map(msg => msg.id === streamingMessageId ? {
                ...msg,
                content: finalContent,
                metadata: {
                  ...msg.metadata,
                  agentResponse: true,
                  toolUsed: finalResponse?.tool_name,
                  intentType: finalResponse?.intent_type,
                  isStreaming: false
                }
              } : msg)
            );
            
            // If external message handler is provided, send the final message
            if (onMessage) {
              const finalMessage: ChatMessage = {
                id: streamingMessageId,
                type: 'assistant',
                content: finalContent,
                timestamp: new Date(),
                metadata: {
                  agentResponse: true,
                  toolUsed: finalResponse?.tool_name,
                  intentType: finalResponse?.intent_type,
                  isStreaming: false
                }
              };
              onMessage(finalMessage);
            }
            
            resetStreamingState();
          },
          onError: (error) => {
            // Update internal state with error content
            setInternalMessages(prev => 
              prev.map(msg => msg.id === streamingMessageId ? {
                ...msg,
                content: `❌ Error: ${error}`,
                metadata: { ...msg.metadata, error: 'true', isStreaming: false }
              } : msg)
            );
            
            // If external message handler is provided, send the error message
            if (onMessage) {
              const errorMessage: ChatMessage = {
                id: streamingMessageId,
                type: 'assistant',
                content: `❌ Error: ${error}`,
                timestamp: new Date(),
                metadata: { error: 'true', isStreaming: false }
              };
              onMessage(errorMessage);
            }
            
            resetStreamingState();
          }
        }
      });

    } catch (error) {
      console.error('Streaming chat failed:', error);
      resetStreamingState();
      throw error;
    }
  }, [onMessage, handleStreamingEvent, resetStreamingState, conversationHistory]);

  return {
    isStreaming,
    streamingProgress,
    startStreamingChat,
    resetStreamingState,
    messages
  };
};
