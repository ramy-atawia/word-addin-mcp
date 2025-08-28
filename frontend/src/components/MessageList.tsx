import React, { useRef, useEffect } from 'react';
import MessageBubble, { Message } from './MessageBubble';

export interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
  onToolResultClick?: (toolResult: any) => void;
  onErrorDetailsClick?: (error: string) => void;
  onScrollToTop?: () => void;
  onScrollToBottom?: () => void;
  showScrollButtons?: boolean;
  maxHeight?: string;
}

const MessageList: React.FC<MessageListProps> = ({
  messages,
  isLoading = false,
  onToolResultClick,
  onErrorDetailsClick,
  onScrollToTop,
  onScrollToBottom,
  showScrollButtons = true,
  maxHeight = 'calc(100vh - 300px)'
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [showTopButton, setShowTopButton] = React.useState(false);
  const [showBottomButton, setShowBottomButton] = React.useState(false);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Handle scroll events to show/hide scroll buttons
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      
      // Show top button if scrolled down
      setShowTopButton(scrollTop > 100);
      
      // Show bottom button if not at bottom
      setShowBottomButton(scrollTop < scrollHeight - clientHeight - 100);
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToTop = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
    if (onScrollToTop) {
      onScrollToTop();
    }
  };

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
    if (onScrollToBottom) {
      onScrollToBottom();
    }
  };

  const renderEmptyState = () => {
    if (messages.length > 0) return null;

    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500">
        <svg className="w-16 h-16 mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <h3 className="text-lg font-medium mb-2">No messages yet</h3>
        <p className="text-sm text-center">
          Start a conversation by typing a message below.<br />
          You can ask questions, request document analysis, or use MCP tools.
        </p>
      </div>
    );
  };

  const renderLoadingIndicator = () => {
    if (!isLoading) return null;

    return (
      <div className="flex justify-center py-4">
        <div className="flex items-center space-x-2 text-gray-500">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
          <span className="text-sm">Processing your request...</span>
        </div>
      </div>
    );
  };

  const renderScrollButtons = () => {
    if (!showScrollButtons) return null;

    return (
      <>
        {/* Top scroll button */}
        {showTopButton && (
          <button
            onClick={scrollToTop}
            className="fixed bottom-24 right-6 w-12 h-12 bg-white border border-gray-300 rounded-full shadow-lg hover:shadow-xl transition-all duration-200 flex items-center justify-center text-gray-600 hover:text-gray-800 hover:bg-gray-50"
            title="Scroll to top"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
            </svg>
          </button>
        )}

        {/* Bottom scroll button */}
        {showBottomButton && (
          <button
            onClick={scrollToBottom}
            className="fixed bottom-24 right-6 w-12 h-12 bg-white border border-gray-300 rounded-full shadow-lg hover:shadow-xl transition-all duration-200 flex items-center justify-center text-gray-600 hover:text-gray-800 hover:bg-gray-50"
            title="Scroll to bottom"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
          </button>
        )}
      </>
    );
  };

  const renderMessageGroup = (message: Message, index: number) => {
    const isLastMessage = index === messages.length - 1;
    const showTimestamp = index === 0 || 
      messages[index - 1]?.timestamp.toDateString() !== message.timestamp.toDateString();

    return (
      <div key={message.id}>
        {/* Date separator */}
        {showTimestamp && (
          <div className="flex justify-center my-4">
            <div className="bg-gray-100 px-3 py-1 rounded-full text-xs text-gray-500">
              {message.timestamp.toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              })}
            </div>
          </div>
        )}

        {/* Message bubble */}
        <MessageBubble
          message={message}
          isLastMessage={isLastMessage}
          onToolResultClick={onToolResultClick}
          onErrorDetailsClick={onErrorDetailsClick}
        />
      </div>
    );
  };

  return (
    <div className="relative">
      {/* Messages container */}
      <div
        ref={messagesContainerRef}
        className="overflow-y-auto space-y-1 px-4"
        style={{ maxHeight }}
      >
        {/* Empty state */}
        {renderEmptyState()}

        {/* Messages */}
        {messages.map((message, index) => renderMessageGroup(message, index))}

        {/* Loading indicator */}
        {renderLoadingIndicator()}

        {/* Invisible element for auto-scroll */}
        <div ref={messagesEndRef} />
      </div>

      {/* Scroll buttons */}
      {renderScrollButtons()}

      {/* Scroll to bottom hint */}
      {messages.length > 0 && showBottomButton && (
        <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2">
          <div className="bg-gray-800 text-white text-xs px-2 py-1 rounded-full opacity-75">
            New messages below
          </div>
        </div>
      )}
    </div>
  );
};

export default MessageList;
