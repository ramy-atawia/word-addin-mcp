import * as React from 'react';
import { makeStyles, tokens } from '@fluentui/react-components';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { ChatMessage } from './MessageBubble';
import { MCPTool } from '../../services/types';
import { useChatMessages } from '../../hooks/useChatMessages';
import { useStreamingChat } from '../../hooks/useStreamingChat';
import { useAsyncChat } from '../../hooks/useAsyncChat';
import mcpToolService from '../../services/mcpToolService';
import { useState, useCallback, useEffect } from 'react';

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
    padding: '8px 0px',
    minHeight: 0,
    '@media (min-width: 768px)': {
      padding: '12px 0px',
    },
  },
  inputContainer: {
    borderTop: `1px solid ${tokens.colorNeutralStroke1}`,
    paddingBottom: '2px',
    flexShrink: 0,
  },
  controlsContainer: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 16px',
    borderBottom: `1px solid ${tokens.colorNeutralStroke1}`,
    backgroundColor: tokens.colorNeutralBackground1,
  },
  progressContainer: {
    margin: '8px 16px',
    padding: '8px 12px',
    backgroundColor: '#f0f8ff',
    border: '1px solid #0078d4',
    borderRadius: '4px',
    fontSize: '14px',
  },
  progressHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  progressText: {
    fontSize: '12px',
    color: '#666',
    marginTop: '4px',
  },
  cancelButton: {
    background: '#dc3545',
    color: 'white',
    border: 'none',
    padding: '4px 8px',
    borderRadius: '3px',
    fontSize: '12px',
    cursor: 'pointer',
  },
  toggleContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '14px',
  },
  clearButton: {
    background: 'none',
    border: '1px solid #ccc',
    borderRadius: '4px',
    padding: '4px 8px',
    fontSize: '12px',
    cursor: 'pointer',
  },
});

const ChatInterfaceSimplified: React.FC<ChatInterfaceProps> = ({ 
  messages: externalMessages = [],
  onMessage,
  loading: externalLoading = false,
  onLoadingChange
}) => {
  const styles = useStyles();
  const [inputValue, setInputValue] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [availableTools, setAvailableTools] = useState<MCPTool[]>([]);
  
  // Use custom hooks
  const { addMessage, initializeMessages } = useChatMessages({ 
    externalMessages, 
    onMessage 
  });
  
  const { isStreaming, streamingProgress, startStreamingChat, messages: streamingMessages } = useStreamingChat({
    messages: externalMessages,
    onMessage,
    onLoadingChange
  });

  const {
    messages: asyncMessages,
    isProcessing,
    currentJobId,
    jobProgress,
    useAsyncProcessing,
    setUseAsyncProcessing,
    handleAsyncMessage,
    cancelCurrentJob,
    clearMessages
  } = useAsyncChat({
    messages: externalMessages,
    onMessage,
    onLoadingChange
  });
  
  // Use async messages when async processing is enabled, otherwise use streaming messages
  const messages = useAsyncProcessing ? asyncMessages : streamingMessages;
  const loading = externalLoading || (useAsyncProcessing ? isProcessing : isStreaming);

  // Initialize messages and load tools
  useEffect(() => {
    initializeMessages();
    loadAvailableTools();
  }, []); // Empty dependency array to run only once

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

  const handleSendMessage = useCallback(async (content: string) => {
    // Input validation
    const trimmedContent = content.trim();
    if (!trimmedContent || loading) return;
    
    // Additional validation
    if (trimmedContent.length > 10000) {
      setError('Message too long. Please keep it under 10,000 characters.');
      return;
    }
    
    // Basic XSS prevention
    if (trimmedContent.includes('<script>') || trimmedContent.includes('javascript:')) {
      setError('Invalid content detected. Please remove any script tags.');
      return;
    }

    setInputValue('');
    setError(null); // Clear any previous errors

    try {
      if (onLoadingChange) {
        onLoadingChange(true);
      }
      
      if (useAsyncProcessing) {
        // Use async processing
        const context = {
          document_content: '', // TODO: Get from document service
          chat_history: JSON.stringify(messages.slice(-10)), // Last 10 messages
          available_tools: availableTools.map(t => t.name).join(', ')
        };
        
        await handleAsyncMessage(trimmedContent, context, `session-${Date.now()}`);
      } else {
        // Use streaming processing
        await startStreamingChat(trimmedContent);
      }
    } catch (error) {
      console.error('Error handling user message:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'system',
        content: `❌ Error processing your request: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
        metadata: { error: error instanceof Error ? error.message : 'Unknown error' }
      };
      addMessage(errorMessage);
    } finally {
      if (onLoadingChange) {
        onLoadingChange(false);
      }
    }
  }, [loading, addMessage, startStreamingChat, handleAsyncMessage, useAsyncProcessing, messages, availableTools, onLoadingChange]);

  const handleAttach = () => {
    console.log('Attach functionality to be implemented');
  };

  return (
    <div className={styles.container}>
      {error && (
        <div style={{ 
          padding: '8px 16px', 
          backgroundColor: '#fef2f2', 
          color: '#dc2626', 
          fontSize: '14px',
          borderBottom: '1px solid #fecaca'
        }}>
          {error}
        </div>
      )}
      
      {/* Controls */}
      <div className={styles.controlsContainer}>
        <button
          onClick={clearMessages}
          className={styles.clearButton}
          title="Clear conversation history for new invention context"
        >
          🧹 Clear Context
        </button>
        
        <div className={styles.toggleContainer}>
          <label>
            <input
              type="checkbox"
              checked={useAsyncProcessing}
              onChange={(e) => setUseAsyncProcessing(e.target.checked)}
              style={{ marginRight: '4px' }}
            />
            Use Async Processing (Recommended for long queries)
          </label>
        </div>
      </div>

      {/* Progress Indicator for Async Processing */}
      {useAsyncProcessing && isProcessing && jobProgress && (
        <div className={styles.progressContainer}>
          <div className={styles.progressHeader}>
            <span>
              {jobProgress.status === 'processing' ? '🔄 Processing...' : 
               jobProgress.status === 'pending' ? '⏳ Queued...' : 
               jobProgress.status === 'completed' ? '✅ Completed' : 
               jobProgress.status}
              {jobProgress.progress > 0 && ` (${jobProgress.progress}%)`}
            </span>
            {currentJobId && (
              <button
                onClick={cancelCurrentJob}
                className={styles.cancelButton}
              >
                Cancel
              </button>
            )}
          </div>
          {jobProgress.estimated_duration && (
            <div className={styles.progressText}>
              Estimated time: {Math.ceil(jobProgress.estimated_duration / 60)} minutes
            </div>
          )}
        </div>
      )}

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
          placeholder={useAsyncProcessing ? "Type your message here... (Async mode)" : "Type your message here... (Streaming mode)"}
        />
      </div>
    </div>
  );
};

export default ChatInterfaceSimplified;
