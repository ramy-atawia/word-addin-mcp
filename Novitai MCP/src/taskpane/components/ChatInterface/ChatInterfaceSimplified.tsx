  import React from 'react';
  import { makeStyles, tokens } from '@fluentui/react-components';
  import MessageList from './MessageList';
  import MessageInput from './MessageInput';
  import { ChatMessage } from './MessageBubble';
  import { MCPTool } from '../../services/types';
  import { useChatMessages } from '../../hooks/useChatMessages';
  import { useAsyncChat } from '../../hooks/useAsyncChat';
  import mcpToolService from '../../services/mcpToolService';
  import { documentContextService } from '../../services/documentContextService';
  import { officeIntegrationService } from '../../services/officeIntegrationService';
  import { DocumentModificationService } from '../../services/documentModificationService';
  import ErrorBoundary from '../ErrorBoundary';
  import { useState, useCallback, useEffect } from 'react';

  interface ChatInterfaceProps {
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
    errorContainer: {
      padding: '8px 16px',
      backgroundColor: '#fef2f2',
      color: '#dc2626',
      fontSize: '14px',
      borderBottom: '1px solid #fecaca',
    },
    '@keyframes pulse': {
      '&0%': {
        opacity: 1,
      },
      '&50%': {
        opacity: 0.5,
      },
      '&100%': {
        opacity: 1,
      },
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
    const [availableTools, setAvailableTools] = useState<MCPTool[]>([]);
    const [toolsLoading, setToolsLoading] = useState(false);
    const [documentModificationService] = useState(() => new DocumentModificationService(officeIntegrationService));
  const [messageIdCounter, setMessageIdCounter] = useState(0);
  
  const generateMessageId = useCallback(() => {
    setMessageIdCounter(prev => prev + 1);
    return `msg-${Date.now()}-${messageIdCounter}`;
  }, [messageIdCounter]);
    
    // Use custom hooks
    const { addMessage, initializeMessages, messages: chatMessages } = useChatMessages({ 
      externalMessages, 
      onMessage 
    });
    

    const {
      messages: asyncMessages,
      isProcessing,
      currentJobId,
      jobProgress,
      error: asyncError,
      processingInfo,
      handleAsyncMessage,
      cancelCurrentJob,
      retryCurrentMessage,
      clearMessages,
      canCancel,
      canRetry,
      hasError
    } = useAsyncChat({
      messages: externalMessages,
      onMessage,
      onLoadingChange,
      maxRetries: 3,
      enableRetry: true
    });
    
    // Merge messages: use async messages when processing, otherwise use chat messages (which includes welcome message)
    const messages = isProcessing ? asyncMessages : chatMessages;
    const loading = externalLoading || isProcessing;
    
    // Enhanced error handling - combine local and async errors
    const displayError = error || asyncError;

    // Initialize messages and load tools
    useEffect(() => {
      initializeMessages();
      loadAvailableTools();
    }, []); // Empty dependency array to run only once

    const loadAvailableTools = async () => {
      try {
        setToolsLoading(true);
        setError(null);
        const tools = await mcpToolService.discoverTools();
        setAvailableTools(tools);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to load tools';
        setError(errorMessage);
        console.error('Failed to load tools:', error);
      } finally {
        setToolsLoading(false);
      }
    };

    // Check if user request is for document modification
    const isModificationRequest = (message: string): boolean => {
      const modificationPatterns = [
        /change\s+['\"]?\w+['\"]?\s+to\s+['\"]?\w+['\"]?/i,
        /replace\s+['\"]?\w+['\"]?\s+with\s+['\"]?\w+['\"]?/i,
        /modify\s+['\"]?\w+['\"]?/i,
        /edit\s+['\"]?\w+['\"]?/i,
        /update\s+['\"]?\w+['\"]?/i,
        /revise\s+['\"]?\w+['\"]?/i
      ];
      
      return modificationPatterns.some(pattern => pattern.test(message));
    };

    // Handle document modification
    const handleDocumentModification = async (userRequest: string) => {
      try {
        // Check if Office.js is ready first with retry mechanism
        const isOfficeReady = await officeIntegrationService.waitForOfficeReady(5);
        if (!isOfficeReady) {
        addMessage({
          id: generateMessageId(),
          type: 'system',
          content: '❌ Office.js is not ready. Please ensure you are running this in Microsoft Word and try again.',
          timestamp: new Date()
        });
          return;
        }

        // Get document paragraphs
        const paragraphs = await documentModificationService.getDocumentParagraphs();
        
        if (paragraphs.length === 0) {
        addMessage({
          id: generateMessageId(),
          type: 'system',
          content: '❌ No document content found. Please ensure your Word document has text content and try again.',
          timestamp: new Date()
        });
          return;
        }

        console.log(`Found ${paragraphs.length} paragraphs in document`);

      // Add processing message
      addMessage({
        id: generateMessageId(),
        type: 'system',
        content: '🔍 Analyzing document and generating modification plan...',
        timestamp: new Date()
      });

        // Call backend for modification plan
        const response = await fetch(`${(window as any).BACKEND_URL || 'http://localhost:9000'}/api/v1/mcp/tools/execute`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${(window as any).getAccessToken?.() || ''}`
          },
          body: JSON.stringify({
            tool_name: 'document_modification_tool',
            parameters: {
              user_request: userRequest,
              paragraphs: paragraphs
            }
          })
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }

        const result = await response.json();
        
        if (result.success && result.data) {
          // Apply modifications
          const modificationResult = await documentModificationService.applyModifications(result.data.modifications);
          
        if (modificationResult.success) {
          addMessage({
            id: generateMessageId(),
            type: 'system',
            content: `✅ Document updated successfully! Applied ${modificationResult.changesApplied} changes. ${result.data.summary}`,
            timestamp: new Date()
          });
        } else {
          addMessage({
            id: generateMessageId(),
            type: 'system',
            content: `❌ Document modification failed: ${modificationResult.errors.join(', ')}`,
            timestamp: new Date()
          });
        }
        } else {
          throw new Error(result.error || 'Failed to generate modification plan');
        }
        
      } catch (error) {
        console.error('Document modification failed:', error);
        addMessage({
          id: generateMessageId(),
          type: 'system',
          content: `❌ Document modification failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
          timestamp: new Date()
        });
      }
    };

    const handleSendMessage = useCallback(async (content: string) => {
      // Input validation
      const trimmedContent = content.trim();
      if (!trimmedContent || loading || isProcessing) return;
      
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
        
      // Check if this is a document modification request
      if (isModificationRequest(trimmedContent)) {
        try {
          await handleDocumentModification(trimmedContent);
        } catch (error) {
          console.error('Document modification failed:', error);
          addMessage({
            id: generateMessageId(),
            type: 'system',
            content: `❌ Document modification failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
            timestamp: new Date()
          });
        }
        return; // Exit early, don't proceed with normal chat
      }
        
        // Use async processing only
        let documentContent = '';
        try {
          const documentContext = await documentContextService.buildDocumentContext();
          documentContent = documentContext.fullContent || '';
        } catch (error) {
          console.warn('Failed to get document content:', error);
          documentContent = '';
        }
        
        const sessionId = `session-${Date.now()}`;
        const context = {
          document_content: documentContent,
          chat_history: JSON.stringify(messages.slice(-10)), // Last 10 messages
          available_tools: availableTools.map(t => t.name).join(', '),
          session_id: sessionId
        };
        
        await handleAsyncMessage(trimmedContent, context, sessionId);
      } catch (error) {
        console.error('Error handling user message:', error);
      const errorMessage: ChatMessage = {
        id: generateMessageId(),
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
    }, [loading, isProcessing, addMessage, handleAsyncMessage, messages, availableTools, onLoadingChange]);


    return (
      <ErrorBoundary>
        <div className={styles.container}>
          {displayError && (
            <div className={styles.errorContainer}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>❌ {displayError}</span>
                {hasError && canRetry && (
                  <button
                    onClick={retryCurrentMessage}
                    style={{
                      background: '#0078d4',
                      color: 'white',
                      border: 'none',
                      padding: '4px 8px',
                      borderRadius: '3px',
                      fontSize: '12px',
                      cursor: 'pointer',
                      marginLeft: '8px'
                    }}
                  >
                    🔄 Retry
                  </button>
                )}
              </div>
            </div>
          )}
          
          {/* Enhanced Controls */}
          <div className={styles.controlsContainer}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              
              {isProcessing && (
                <div style={{ 
                  fontSize: '12px', 
                  color: '#0078d4',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}>
                  <div style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: '#0078d4',
                    animation: 'pulse 1.5s ease-in-out infinite'
                  }}></div>
                  Processing...
                </div>
              )}
            </div>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {toolsLoading && (
                <div style={{ fontSize: '12px', color: '#666' }}>
                  🔄 Loading tools...
                </div>
              )}
              
              {hasError && canRetry && (
                <button
                  onClick={retryCurrentMessage}
                  style={{
                    background: '#0078d4',
                    color: 'white',
                    border: 'none',
                    padding: '4px 8px',
                    borderRadius: '3px',
                    fontSize: '12px',
                    cursor: 'pointer'
                  }}
                  title="Retry the last failed operation"
                >
                  🔄 Retry
                </button>
              )}
            </div>
          </div>

          {/* Enhanced Progress Indicator for Async Processing */}
          {isProcessing && (jobProgress || processingInfo) && (
            <div className={styles.progressContainer}>
              <div className={styles.progressHeader}>
                <span>
                  {jobProgress?.status === 'processing' ? '🔄 Processing...' : 
                  jobProgress?.status === 'pending' ? '⏳ Queued...' : 
                  jobProgress?.status === 'completed' ? '✅ Completed' : 
                  processingInfo?.status === 'pending' ? '⏳ Starting...' :
                  processingInfo?.status === 'processing' ? '🔄 Processing...' :
                  'Processing...'}
                  {(jobProgress?.progress || processingInfo?.progress || 0) > 0 && 
                  ` (${jobProgress?.progress || processingInfo?.progress || 0}%)`}
                  {processingInfo?.retryCount > 0 && ` (Retry ${processingInfo.retryCount}/3)`}
                </span>
                {canCancel && (
                  <button
                    onClick={cancelCurrentJob}
                    className={styles.cancelButton}
                    title="Cancel current operation"
                  >
                    Cancel
                  </button>
                )}
              </div>
              {jobProgress?.estimated_duration && (
                <div className={styles.progressText}>
                  Estimated time: {Math.ceil(jobProgress.estimated_duration / 60)} minutes
                  {processingInfo?.jobId && ` • Job ID: ${processingInfo.jobId.slice(0, 8)}...`}
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
              onAttach={() => {}} // Placeholder for future attachment functionality
              disabled={loading}
              placeholder="Type your message here... (Async mode)"
            />
          </div>
        </div>
      </ErrorBoundary>
    );
  };

  export default ChatInterfaceSimplified;
