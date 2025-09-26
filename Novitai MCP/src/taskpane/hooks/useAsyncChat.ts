import { useState, useCallback, useRef } from 'react';
import { asyncChatService, JobStatus, JobResult, AsyncChatCallbacks } from '../services/asyncChatService';

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: any;
}

export interface UseAsyncChatProps {
  messages?: ChatMessage[];
  onMessage?: (message: ChatMessage) => void;
  onLoadingChange?: (loading: boolean) => void;
}

export interface AsyncChatState {
  isProcessing: boolean;
  currentJobId: string | null;
  jobProgress: JobStatus | null;
  useAsyncProcessing: boolean;
}

export const useAsyncChat = ({ 
  messages: externalMessages = [], 
  onMessage, 
  onLoadingChange 
}: UseAsyncChatProps) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [jobProgress, setJobProgress] = useState<JobStatus | null>(null);
  const [useAsyncProcessing, setUseAsyncProcessing] = useState(true); // Default to async
  const [internalMessages, setInternalMessages] = useState<ChatMessage[]>([]);
  
  const abortControllerRef = useRef<AbortController | null>(null);

  // During processing, always use internal messages for real-time updates
  // When not processing, use external messages if available (for persistence across tab switches)
  const messages = isProcessing ? internalMessages : (externalMessages.length > 0 ? externalMessages : internalMessages);

  const resetAsyncState = useCallback(() => {
    setIsProcessing(false);
    setCurrentJobId(null);
    setJobProgress(null);
    setInternalMessages([]);
  }, []);

  const cancelCurrentJob = useCallback(async () => {
    if (currentJobId) {
      try {
        await asyncChatService.cancelJob(currentJobId);
        console.log('Job cancelled:', currentJobId);
        resetAsyncState();
      } catch (error) {
        console.error('Failed to cancel job:', error);
      }
    }
  }, [currentJobId, resetAsyncState]);

  const handleAsyncMessage = useCallback(async (message: string, context: {
    document_content: string;
    chat_history: string;
    available_tools: string;
  }, sessionId: string) => {
    if (isProcessing) return;

    // Create user message
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: message,
      timestamp: new Date(),
    };

    // Add user message to internal state
    setInternalMessages(prev => [...prev, userMessage]);
    
    // Notify parent component
    if (onMessage) {
      onMessage(userMessage);
    }

    setIsProcessing(true);
    setJobProgress(null);
    setCurrentJobId(null);
    
    // Notify parent component of loading state change
    if (onLoadingChange) {
      onLoadingChange(true);
    }

    // Create assistant message placeholder
    const assistantMessageId = `assistant-${Date.now()}`;
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      type: 'assistant',
      content: 'Processing your request...',
      timestamp: new Date(),
      metadata: { isProcessing: true }
    };

    setInternalMessages(prev => [...prev, assistantMessage]);

    try {
      const callbacks: AsyncChatCallbacks = {
        onProgress: (status: JobStatus) => {
          console.log('Job progress:', status);
          setJobProgress(status);
          setCurrentJobId(status.job_id);
          
          // Update assistant message with progress
          setInternalMessages(prev => 
            prev.map(msg => 
              msg.id === assistantMessageId 
                ? {
                    ...msg,
                    content: `Processing... ${status.progress}%`,
                    metadata: { 
                      ...msg.metadata, 
                      isProcessing: true,
                      progress: status.progress,
                      status: status.status
                    }
                  }
                : msg
            )
          );
        },
        onComplete: (result: JobResult) => {
          console.log('Job completed:', result);
          setIsProcessing(false);
          setCurrentJobId(null);
          
          // Notify parent component of loading state change
          if (onLoadingChange) {
            onLoadingChange(false);
          }
          
          // Update assistant message with final result
            const finalContent = typeof result.result?.result === 'string' 
              ? result.result.result 
              : typeof result.result === 'string' 
                ? result.result 
                : String(result.result || 'Request completed successfully');
          setInternalMessages(prev => 
            prev.map(msg => 
              msg.id === assistantMessageId 
                ? {
                    ...msg,
                    content: finalContent,
                    metadata: { 
                      ...msg.metadata, 
                      isProcessing: false,
                      progress: 100,
                      status: 'completed'
                    }
                  }
                : msg
            )
          );

          // Notify parent component
          if (onMessage) {
            onMessage({
              id: assistantMessageId,
              type: 'assistant',
              content: finalContent,
              timestamp: new Date(),
              metadata: { isProcessing: false }
            });
          }
        },
        onError: (error: Error) => {
          console.error('Async processing error:', error);
          setIsProcessing(false);
          setCurrentJobId(null);
          
          // Notify parent component of loading state change
          if (onLoadingChange) {
            onLoadingChange(false);
          }
          
          // Update assistant message with error
          setInternalMessages(prev => 
            prev.map(msg => 
              msg.id === assistantMessageId 
                ? {
                    ...msg,
                    content: `Error: ${error.message}`,
                    metadata: { 
                      ...msg.metadata, 
                      isProcessing: false,
                      error: error.message
                    }
                  }
                : msg
            )
          );

          // Notify parent component
          if (onMessage) {
            onMessage({
              id: assistantMessageId,
              type: 'assistant',
              content: `Error: ${error.message}`,
              timestamp: new Date(),
              metadata: { error: error.message }
            });
          }
        }
      };

      // Start async processing
      await asyncChatService.processChatAsync({
        message,
        context,
        sessionId
      }, callbacks);

    } catch (error) {
      console.error('Error in async processing:', error);
      setIsProcessing(false);
      setCurrentJobId(null);
      
      // Notify parent component of loading state change
      if (onLoadingChange) {
        onLoadingChange(false);
      }
      
      // Update assistant message with error
      setInternalMessages(prev => 
        prev.map(msg => 
          msg.id === assistantMessageId 
            ? {
                ...msg,
                content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
                metadata: { 
                  ...msg.metadata, 
                  isProcessing: false,
                  error: error instanceof Error ? error.message : 'Unknown error'
                }
              }
            : msg
        )
      );
    }
  }, [isProcessing, onMessage]);

  const clearMessages = useCallback(() => {
    setInternalMessages([]);
    resetAsyncState();
  }, [resetAsyncState]);

  return {
    messages,
    isProcessing,
    currentJobId,
    jobProgress,
    useAsyncProcessing,
    setUseAsyncProcessing,
    handleAsyncMessage,
    cancelCurrentJob,
    clearMessages,
    resetAsyncState
  };
};
