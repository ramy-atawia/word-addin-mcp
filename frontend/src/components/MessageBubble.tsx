import React from 'react';

export interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system' | 'tool_result';
  content: string;
  timestamp: Date;
  metadata?: {
    toolUsed?: string;
    toolResult?: any;
    error?: string;
    executionTime?: number;
    [key: string]: any;
  };
}

interface MessageBubbleProps {
  message: Message;
  isLastMessage?: boolean;
  onToolResultClick?: (toolResult: any) => void;
  onErrorDetailsClick?: (error: string) => void;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  isLastMessage = false,
  onToolResultClick,
  onErrorDetailsClick
}) => {
  const getMessageStyle = () => {
    switch (message.type) {
      case 'user':
        return 'bg-primary-600 text-white ml-auto';
      case 'assistant':
        return 'bg-gray-100 text-gray-900';
      case 'system':
        return 'bg-yellow-100 text-yellow-800 border border-yellow-300';
      case 'tool_result':
        return 'bg-green-50 text-gray-900 border border-green-200';
      default:
        return 'bg-gray-100 text-gray-900';
    }
  };

  const getMessageIcon = () => {
    switch (message.type) {
      case 'user':
        return (
          <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
            <span className="text-primary-700 font-medium text-sm">U</span>
          </div>
        );
      case 'assistant':
        return (
          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
        );
      case 'system':
        return (
          <div className="w-8 h-8 rounded-full bg-yellow-100 flex items-center justify-center">
            <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
        );
      case 'tool_result':
        return (
          <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
            <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          </div>
        );
      default:
        return null;
    }
  };

  const formatContent = (content: string) => {
    // Simple markdown-like formatting
    return content
      .split('\n')
      .map((line, index) => (
        <React.Fragment key={index}>
          {line}
          {index < content.split('\n').length - 1 && <br />}
        </React.Fragment>
      ));
  };

  const renderToolResult = () => {
    if (message.type !== 'tool_result' || !message.metadata?.toolResult) {
      return null;
    }

    const toolResult = message.metadata.toolResult;
    const toolName = message.metadata.toolUsed || 'Unknown Tool';

    return (
      <div className="mt-3 p-3 bg-white rounded-lg border border-green-200">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-green-700">
            {toolName} Result
          </span>
          {message.metadata.executionTime && (
            <span className="text-xs text-gray-500">
              {message.metadata.executionTime.toFixed(2)}s
            </span>
          )}
        </div>
        <div className="text-sm text-gray-700">
          {typeof toolResult === 'object' ? (
            <pre className="whitespace-pre-wrap text-xs">
              {JSON.stringify(toolResult, null, 2)}
            </pre>
          ) : (
            <span>{String(toolResult)}</span>
          )}
        </div>
        {onToolResultClick && (
          <button
            onClick={() => onToolResultClick(toolResult)}
            className="mt-2 text-xs text-green-600 hover:text-green-800 underline"
          >
            View Details
          </button>
        )}
      </div>
    );
  };

  const renderErrorDetails = () => {
    if (!message.metadata?.error) {
      return null;
    }

    return (
      <div className="mt-3 p-3 bg-red-50 rounded-lg border border-red-200">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-red-700">
            Error Details
          </span>
        </div>
        <div className="text-sm text-red-600">
          {message.metadata.error}
        </div>
        {onErrorDetailsClick && message.metadata?.error && (
          <button
            onClick={() => onErrorDetailsClick(message.metadata!.error!)}
            className="mt-2 text-xs text-red-600 hover:text-red-800 underline"
          >
            View Full Error
          </button>
        )}
      </div>
    );
  };

  const renderMetadata = () => {
    if (!message.metadata) return null;

    const metadataItems = [];
    
    if (message.metadata.toolUsed) {
      metadataItems.push(
        <span key="tool" className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
          {message.metadata.toolUsed}
        </span>
      );
    }

    if (message.metadata.executionTime) {
      metadataItems.push(
        <span key="time" className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
          <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {message.metadata.executionTime.toFixed(2)}s
        </span>
      );
    }

    return metadataItems.length > 0 ? (
      <div className="flex flex-wrap gap-2 mt-2">
        {metadataItems}
      </div>
    ) : null;
  };

  return (
    <div className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
      {message.type !== 'user' && (
        <div className="flex-shrink-0 mr-3">
          {getMessageIcon()}
        </div>
      )}
      
      <div className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${getMessageStyle()} relative`}>
        {/* Message content */}
        <div className="text-sm leading-relaxed">
          {formatContent(message.content)}
        </div>
        
        {/* Metadata badges */}
        {renderMetadata()}
        
        {/* Tool result display */}
        {renderToolResult()}
        
        {/* Error details */}
        {renderErrorDetails()}
        
        {/* Timestamp */}
        <div className="text-xs opacity-75 mt-2">
          {message.timestamp.toLocaleTimeString()}
        </div>
        
        {/* New message indicator */}
        {isLastMessage && (
          <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
          </div>
        )}
      </div>
      
      {message.type === 'user' && (
        <div className="flex-shrink-0 ml-3">
          {getMessageIcon()}
        </div>
      )}
    </div>
  );
};

export default MessageBubble;
