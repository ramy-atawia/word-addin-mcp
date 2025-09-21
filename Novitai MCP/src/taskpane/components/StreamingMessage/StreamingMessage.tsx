import React from 'react';
import { ChatMessage } from '../ChatInterface/MessageBubble';
import { StreamingProgress } from '../../services/types';

interface StreamingMessageProps {
  message: ChatMessage;
  progress: StreamingProgress;
}

const StreamingMessage: React.FC<StreamingMessageProps> = ({ message, progress }) => {
  const getProgressText = (status: StreamingProgress['status']) => {
    switch (status) {
      case 'intent_detection':
        return '🔍 Detecting intent...';
      case 'tool_execution':
        return '⚙️ Planning workflow...';
      case 'response_generation':
        return '✍️ Generating response...';
      default:
        return '🤔 Thinking...';
    }
  };

  return (
    <div className="streaming-message">
      <div className="progress-indicator">
        {getProgressText(progress.status)}
      </div>
      {message.content && (
        <div className="streaming-content">
          {message.content}
        </div>
      )}
    </div>
  );
};

export default StreamingMessage;
