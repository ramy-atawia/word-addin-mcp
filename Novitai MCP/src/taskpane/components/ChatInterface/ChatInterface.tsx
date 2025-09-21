// This file has been simplified! Use ChatInterfaceSimplified.tsx instead
// Keeping this file for backward compatibility

import * as React from 'react';
import { ChatMessage } from './MessageBubble';
import { MCPTool } from '../../services/types';

// Import the simplified version
import ChatInterfaceSimplified from './ChatInterfaceSimplified';

interface ChatInterfaceProps {
  onToolSelect?: (tool: MCPTool) => void;
  messages?: ChatMessage[];
  onMessage?: (message: ChatMessage) => void;
  loading?: boolean;
  onLoadingChange?: (loading: boolean) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = (props) => {
  // Use the simplified version
  return <ChatInterfaceSimplified {...props} />;
};

export default ChatInterface;