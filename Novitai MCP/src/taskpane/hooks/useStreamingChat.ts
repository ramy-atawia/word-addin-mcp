import { useState, useRef, useCallback, useMemo } from 'react';
import { ChatMessage } from '../components/ChatInterface/MessageBubble';
import { StreamingEvent, StreamingProgress, MCPTool } from '../services/types';
import mcpToolService from '../services/mcpToolService';
import { officeIntegrationService } from '../services/officeIntegrationService';

interface UseStreamingChatProps {
  messages: ChatMessage[];
  onMessage?: (message: ChatMessage) => void;
  onLoadingChange?: (loading: boolean) => void;
}

export const useStreamingChat = ({ messages, onMessage, onLoadingChange }: UseStreamingChatProps) => {
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

  const resetStreamingState = useCallback(() => {
    setIsStreaming(false);
    setStreamingProgress({
      currentStep: 0,
      totalSteps: 0,
      status: 'complete'
    });
    streamingResponseRef.current = '';
  }, []);

  const updateStreamingMessage = useCallback((messageId: string, content: string, metadata: any) => {
    if (onMessage) {
      // For external message handling - create new message
      const updatedMessage: ChatMessage = {
        id: messageId,
        type: 'assistant',
        content,
        timestamp: new Date(),
        metadata: { ...metadata, isStreaming: true }
      };
      onMessage(updatedMessage);
    } else {
      // For internal message handling
      setInternalMessages(prev => 
        prev.map(msg => msg.id === messageId ? {
          ...msg,
          content,
          metadata: { ...msg.metadata, ...metadata }
        } : msg)
      );
    }
  }, [onMessage]);

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
            
            updateStreamingMessage(messageId, `${progressText}\n\n${streamingResponseRef.current || 'Processing...'}`, {
              streamingProgress: status
            });
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
    }
  }, [updateStreamingMessage]);

  // Memoize conversation history to avoid recalculation
  const conversationHistory = useMemo(() => {
    return messages
      .filter(msg => !msg.metadata?.isStreaming && msg.type !== 'system' && msg.content.trim() !== '')
      .slice(-50)
      .map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content,
        timestamp: msg.timestamp
      }));
  }, [messages]);

  const startStreamingChat = useCallback(async (userMessage: string) => {
    try {
      setIsStreaming(true);
      streamingResponseRef.current = '';

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

      if (onMessage) {
        onMessage(initialMessage);
      } else if (setInternalMessages) {
        setInternalMessages(prev => [...prev, initialMessage]);
      }

      // Start streaming
      await mcpToolService.chatWithAgentStreaming({
        message: userMessage,
        context: {
          document_content: documentContent,
          chat_history: JSON.stringify(conversationHistory),
          available_tools: availableTools.map(t => t.name).join(', ')
        },
        sessionId: `session-${Date.now()}`,
        callbacks: {
          onEvent: (event) => handleStreamingEvent(event, streamingMessageId),
          onComplete: (finalResponse) => {
            const finalContent = streamingResponseRef.current || finalResponse?.final_response || 'Request completed successfully';
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
            
            if (onMessage) {
              onMessage(finalMessage);
            } else if (setInternalMessages) {
              setInternalMessages(prev => 
                prev.map(msg => msg.id === streamingMessageId ? finalMessage : msg)
              );
            }
            
            resetStreamingState();
          },
          onError: (error) => {
            const errorMessage: ChatMessage = {
              id: streamingMessageId,
              type: 'assistant',
              content: `❌ Error: ${error}`,
              timestamp: new Date(),
              metadata: { error: 'true', isStreaming: false }
            };
            
            if (onMessage) {
              onMessage(errorMessage);
            } else if (setInternalMessages) {
              setInternalMessages(prev => 
                prev.map(msg => msg.id === streamingMessageId ? errorMessage : msg)
              );
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
  }, [messages, onMessage, handleStreamingEvent, resetStreamingState, conversationHistory]);

  return {
    isStreaming,
    streamingProgress,
    startStreamingChat,
    resetStreamingState
  };
};
