import { useState, useCallback } from 'react';
import { ChatMessage } from '../components/ChatInterface/MessageBubble';

interface UseChatMessagesProps {
  externalMessages?: ChatMessage[];
  onMessage?: (message: ChatMessage) => void;
}

export const useChatMessages = ({ externalMessages = [], onMessage }: UseChatMessagesProps) => {
  const [internalMessages, setInternalMessages] = useState<ChatMessage[]>([]);
  
  const messages = externalMessages.length > 0 ? externalMessages : internalMessages;
  
  const addMessage = useCallback((message: ChatMessage) => {
    try {
      if (onMessage) {
        onMessage(message);
      } else {
        setInternalMessages(prev => [...prev, message]);
      }
    } catch (error) {
      console.error('Failed to add message:', error);
    }
  }, [onMessage]);
  
  const updateMessage = useCallback((messageId: string, updates: Partial<ChatMessage>) => {
    if (onMessage) {
      // For external message handling, we can't update directly
      // This would need to be handled by the parent component
      console.warn('Cannot update external messages directly');
    } else {
      setInternalMessages(prev => 
        prev.map(msg => msg.id === messageId ? { ...msg, ...updates } : msg)
      );
    }
  }, [onMessage]);
  
  const initializeMessages = useCallback(() => {
    if (externalMessages.length === 0) {
      const welcomeMessage: ChatMessage = {
        id: '1',
        type: 'assistant',
        content: 'Hello! I\'m your AI assistant. I can help you with document processing, web research, and more. What would you like to do today?',
        timestamp: new Date()
      };
      addMessage(welcomeMessage);
    }
  }, [externalMessages.length, addMessage]);
  
  return {
    messages,
    addMessage,
    updateMessage,
    initializeMessages,
    setInternalMessages
  };
};
