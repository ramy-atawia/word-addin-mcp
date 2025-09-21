import * as React from 'react';
import { makeStyles, tokens } from '@fluentui/react-components';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { ChatMessage } from './MessageBubble';
import { MCPTool } from '../../services/types';
import { useChatMessages } from '../../hooks/useChatMessages';
import { useStreamingChat } from '../../hooks/useStreamingChat';
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
  const { messages, addMessage, initializeMessages } = useChatMessages({ 
    externalMessages, 
    onMessage 
  });
  
  const { isStreaming, streamingProgress, startStreamingChat } = useStreamingChat({
    messages,
    onMessage,
    onLoadingChange
  });
  
  const loading = externalLoading || isStreaming;

  // Initialize messages and load tools
  useEffect(() => {
    initializeMessages();
    loadAvailableTools();
  }, [initializeMessages]);

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
    if (!content.trim() || isStreaming) return;

    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: content.trim(),
      timestamp: new Date()
    };
    addMessage(userMessage);
    setInputValue('');

    try {
      if (onLoadingChange) {
        onLoadingChange(true);
      }
      
      await startStreamingChat(content.trim());
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
  }, [isStreaming, addMessage, startStreamingChat, onLoadingChange]);

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

export default ChatInterfaceSimplified;
