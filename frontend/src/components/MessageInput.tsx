import React, { useState, useRef, useEffect } from 'react';

export interface MessageInputProps {
  onSendMessage: (message: string, messageType?: string, metadata?: any) => void;
  onFileUpload?: (file: File) => void;
  onToolSelection?: (toolName: string) => void;
  placeholder?: string;
  disabled?: boolean;
  isLoading?: boolean;
  availableTools?: Array<{
    name: string;
    description: string;
    category: string;
  }>;
  showToolSelector?: boolean;
  showFileUpload?: boolean;
  maxLength?: number;
}

const MessageInput: React.FC<MessageInputProps> = ({
  onSendMessage,
  onFileUpload,
  onToolSelection,
  placeholder = "Type your message here...",
  disabled = false,
  isLoading = false,
  availableTools = [],
  showToolSelector = false,
  showFileUpload = false,
  maxLength = 2000
}) => {
  const [inputValue, setInputValue] = useState('');
  const [selectedTool, setSelectedTool] = useState<string>('');
  const [showToolDropdown, setShowToolDropdown] = useState(false);
  const [inputType, setInputType] = useState<'text' | 'file' | 'tool'>('text');
  const [characterCount, setCharacterCount] = useState(0);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setCharacterCount(inputValue.length);
  }, [inputValue]);

  useEffect(() => {
    if (textareaRef.current) {
      // Auto-resize textarea
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [inputValue]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    if (value.length <= maxLength) {
      setInputValue(value);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSendMessage = () => {
    if (!inputValue.trim() || disabled || isLoading) return;

    const metadata: any = {};
    
    if (selectedTool) {
      metadata.toolSelected = selectedTool;
    }
    
    if (inputType === 'tool' && selectedTool) {
      metadata.messageType = 'tool_request';
    }

    onSendMessage(inputValue.trim(), inputType, metadata);
    setInputValue('');
    setSelectedTool('');
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onFileUpload) {
      onFileUpload(file);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleToolSelection = (toolName: string) => {
    setSelectedTool(toolName);
    setShowToolDropdown(false);
    if (onToolSelection) {
      onToolSelection(toolName);
    }
  };

  const handleInputTypeChange = (type: 'text' | 'file' | 'tool') => {
    setInputType(type);
    setInputValue('');
    setSelectedTool('');
  };

  const getInputTypeIcon = () => {
    switch (inputType) {
      case 'text':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        );
      case 'file':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        );
      case 'tool':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
        );
      default:
        return null;
    }
  };

  const renderToolSelector = () => {
    if (!showToolSelector || inputType !== 'tool') return null;

    return (
      <div className="mb-3">
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowToolDropdown(!showToolDropdown)}
            className="w-full flex items-center justify-between px-3 py-2 border border-gray-300 rounded-lg bg-white text-left text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <span className={selectedTool ? 'text-gray-900' : 'text-gray-500'}>
              {selectedTool || 'Select a tool...'}
            </span>
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {showToolDropdown && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-auto">
              {availableTools.length > 0 ? (
                availableTools.map((tool) => (
                  <button
                    key={tool.name}
                    onClick={() => handleToolSelection(tool.name)}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
                  >
                    <div className="font-medium text-gray-900">{tool.name}</div>
                    <div className="text-xs text-gray-500">{tool.description}</div>
                    <div className="text-xs text-gray-400">{tool.category}</div>
                  </button>
                ))
              ) : (
                <div className="px-3 py-2 text-sm text-gray-500">
                  No tools available
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderFileUpload = () => {
    if (!showFileUpload || inputType !== 'file') return null;

    return (
      <div className="mb-3">
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileUpload}
            className="hidden"
            accept=".txt,.doc,.docx,.pdf,.md"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="text-primary-600 hover:text-primary-700 font-medium"
          >
            Click to upload a file
          </button>
          <p className="text-xs text-gray-500 mt-1">
            Supported formats: TXT, DOC, DOCX, PDF, MD
          </p>
        </div>
      </div>
    );
  };

  const renderInputTypeSelector = () => {
    if (!showToolSelector && !showFileUpload) return null;

    return (
      <div className="mb-3 flex space-x-2">
        <button
          type="button"
          onClick={() => handleInputTypeChange('text')}
          className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
            inputType === 'text'
              ? 'bg-primary-100 text-primary-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          Text
        </button>
        
        {showFileUpload && (
          <button
            type="button"
            onClick={() => handleInputTypeChange('file')}
            className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              inputType === 'file'
                ? 'bg-primary-100 text-primary-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            File
          </button>
        )}
        
        {showToolSelector && (
          <button
            type="button"
            onClick={() => handleInputTypeChange('tool')}
            className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              inputType === 'tool'
                ? 'bg-primary-100 text-primary-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
            Tool
          </button>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-3">
      {/* Input type selector */}
      {renderInputTypeSelector()}
      
      {/* Tool selector */}
      {renderToolSelector()}
      
      {/* File upload */}
      {renderFileUpload()}
      
      {/* Text input */}
      {inputType === 'text' && (
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            disabled={disabled || isLoading}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
            rows={1}
            maxLength={maxLength}
          />
          
          {/* Character count */}
          <div className="absolute bottom-2 right-2 text-xs text-gray-400">
            {characterCount}/{maxLength}
          </div>
          
          {/* Send button */}
          <div className="flex items-center justify-between mt-3">
            <div className="flex items-center space-x-2">
              {/* Tool indicator removed from text input section */}
            </div>
            
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || disabled || isLoading}
              className="btn-primary px-6 py-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                  <span>Send</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
      
      {/* File upload button for file type */}
      {inputType === 'file' && (
        <div className="text-center">
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled || isLoading}
            className="btn-primary px-6 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Processing...' : 'Upload File'}
          </button>
        </div>
      )}
      
      {/* Tool execution button for tool type */}
      {inputType === 'tool' && selectedTool && (
        <div className="text-center">
          <button
            onClick={handleSendMessage}
            disabled={disabled || isLoading}
            className="btn-primary px-6 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Processing...' : `Execute ${selectedTool}`}
          </button>
        </div>
      )}
    </div>
  );
};

export default MessageInput;
