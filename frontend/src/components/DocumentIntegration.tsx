import React, { useState, useEffect, useCallback } from 'react';
import officeService, { 
  DocumentContent, 
  DocumentSelection, 
  DocumentState,
  InsertionOptions 
} from '../services/officeService';
import mcpToolService, { MCPToolExecutionRequest, MCPToolExecutionResult } from '../services/mcpToolService';

interface DocumentIntegrationProps {
  onContentRead?: (content: DocumentContent) => void;
  onSelectionChange?: (selection: DocumentSelection) => void;
  onStateChange?: (state: DocumentState) => void;
}

const DocumentIntegration: React.FC<DocumentIntegrationProps> = ({
  onContentRead,
  onSelectionChange,
  onStateChange
}) => {
  const [isInitialized, setIsInitialized] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [documentState, setDocumentState] = useState<DocumentState | null>(null);
  const [currentSelection, setCurrentSelection] = useState<DocumentSelection | null>(null);
  const [documentContent, setDocumentContent] = useState<DocumentContent | null>(null);
  const [insertContent, setInsertContent] = useState('');
  const [insertOptions, setInsertionOptions] = useState<InsertionOptions>({
    insertLocation: 'start',
    formatting: 'keep',
    trackChanges: false
  });
  const [error, setError] = useState<string | null>(null);
  
  // MCP Tool Integration
  const [availableTools, setAvailableTools] = useState<string[]>([]);
  const [selectedTool, setSelectedTool] = useState<string>('');
  const [toolExecutionResult, setToolExecutionResult] = useState<MCPToolExecutionResult | null>(null);
  const [isExecutingTool, setIsExecutingTool] = useState(false);

  // Load available MCP tools
  useEffect(() => {
    const loadTools = async () => {
      try {
        const tools = await mcpToolService.discoverTools();
        setAvailableTools(tools.map(tool => tool.name));
      } catch (err) {
        console.error('Failed to load MCP tools:', err);
      }
    };
    
    loadTools();
  }, []);

  // Initialize Office.js service
  useEffect(() => {
    const initService = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const success = await officeService.initialize();
        if (success) {
          setIsInitialized(true);
          
          // Add event listeners
          officeService.addChangeListener(handleDocumentStateChange);
          
          // Get initial document state
          const state = officeService.getDocumentState();
          if (state) {
            setDocumentState(state);
            if (onStateChange) onStateChange(state);
          }
          
          // Get initial selection
          try {
            const selection = await officeService.getSelection();
            setCurrentSelection(selection);
            if (onSelectionChange) onSelectionChange(selection);
          } catch (err) {
            console.warn('Could not get initial selection:', err);
          }
        } else {
          setError('Failed to initialize Office.js service');
        }
      } catch (err) {
        setError(`Initialization error: ${err instanceof Error ? err.message : 'Unknown error'}`);
      } finally {
        setIsLoading(false);
      }
    };

    initService();

    // Cleanup on unmount
    return () => {
      officeService.cleanup();
    };
  }, [onStateChange, onSelectionChange]);

  // Handle document state changes
  const handleDocumentStateChange = useCallback((state: DocumentState) => {
    setDocumentState(state);
    if (onStateChange) onStateChange(state);
  }, [onStateChange]);

  // Handle selection changes
  const handleSelectionChange = useCallback(async () => {
    if (!isInitialized) return;
    
    try {
      const selection = await officeService.getSelection();
      setCurrentSelection(selection);
      if (onSelectionChange) onSelectionChange(selection);
    } catch (err) {
      console.error('Failed to get selection:', err);
    }
  }, [isInitialized, onSelectionChange]);

  // Read document content
  const handleReadContent = async (options: {
    includeFormatting?: boolean;
    includeTables?: boolean;
    includeImages?: boolean;
  } = {}) => {
    if (!isInitialized) return;
    
    try {
      setIsLoading(true);
      setError(null);
      
      const content = await officeService.readDocumentContent(options);
      setDocumentContent(content);
      
      if (onContentRead) onContentRead(content);
    } catch (err) {
      setError(`Failed to read document content: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Insert content into document
  const handleInsertContent = async () => {
    if (!isInitialized || !insertContent.trim()) return;
    
    try {
      setIsLoading(true);
      setError(null);
      
      const success = await officeService.insertContent(insertContent, insertOptions);
      if (success) {
        setInsertContent('');
        // Refresh document state
        const state = officeService.getDocumentState();
        if (state) {
          setDocumentState(state);
        }
      }
    } catch (err) {
      setError(`Failed to insert content: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Save document
  const handleSaveDocument = async () => {
    if (!isInitialized) return;
    
    try {
      setIsLoading(true);
      setError(null);
      
      const success = await officeService.saveDocument();
      if (success) {
        // Refresh document state
        const state = officeService.getDocumentState();
        if (state) {
          setDocumentState(state);
        }
      }
    } catch (err) {
      setError(`Failed to save document: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Replace selected content
  const handleReplaceSelection = async (newContent: string) => {
    if (!isInitialized || !currentSelection) return;
    
    try {
      setIsLoading(true);
      setError(null);
      
      const success = await officeService.replaceRange(currentSelection.range, newContent);
      if (success) {
        // Refresh selection and document state
        await handleSelectionChange();
        const state = officeService.getDocumentState();
        if (state) {
          setDocumentState(state);
        }
      }
    } catch (err) {
      setError(`Failed to replace selection: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Execute MCP tool on document content
  const handleExecuteTool = async () => {
    if (!selectedTool || !documentContent) return;
    
    try {
      setIsExecutingTool(true);
      setError(null);
      setToolExecutionResult(null);
      
      // Prepare tool execution request
      const request: MCPToolExecutionRequest = {
        toolName: selectedTool,
        parameters: await prepareToolParameters(selectedTool, documentContent),
        sessionId: `doc-${Date.now()}`
      };
      
      // Execute the tool
      const result = await mcpToolService.executeTool(request);
      setToolExecutionResult(result);
      
      if (!result.success) {
        setError(`Tool execution failed: ${result.error || 'Unknown error'}`);
      }
    } catch (err) {
      setError(`Failed to execute tool: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsExecutingTool(false);
    }
  };

  // Prepare tool parameters based on tool type and document content
  const prepareToolParameters = async (toolName: string, content: DocumentContent): Promise<Record<string, any>> => {
    const params: Record<string, any> = {};
    
    switch (toolName) {
      case 'document_analyzer':
        params.content = content.text || '';
        params.analysis_type = 'readability';
        break;
      
      case 'text_processor':
        params.text = content.text || '';
        params.operation = 'summarize';
        break;
      
      case 'data_formatter':
        params.data = content.text || '';
        params.format = 'summary';
        break;
      
      default:
        // For other tools, try to use the content as a parameter
        if (content.text) {
          params.text = content.text;
        }
    }
    
    return params;
  };

  if (!isInitialized) {
    return (
      <div className="card">
        <div className="text-center py-8">
          {isLoading ? (
            <div className="flex flex-col items-center space-y-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              <p className="text-gray-600">Initializing Office.js integration...</p>
            </div>
          ) : (
            <div className="text-center">
              <div className="text-red-500 mb-4">
                <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Office.js Not Available</h3>
              <p className="text-gray-600 mb-4">
                This component requires Office.js to be available. Please ensure you're running this add-in within Microsoft Word.
              </p>
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
                  {error}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Document Status */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Document Status</h3>
        {documentState && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <span className="text-sm font-medium text-gray-700">Document Name:</span>
              <p className="text-sm text-gray-900">{documentState.documentName}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-700">Status:</span>
              <div className="flex items-center space-x-2">
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                  documentState.hasUnsavedChanges 
                    ? 'bg-yellow-100 text-yellow-800' 
                    : 'bg-green-100 text-green-800'
                }`}>
                  {documentState.hasUnsavedChanges ? 'Unsaved Changes' : 'Saved'}
                </span>
                {documentState.lastSaved && (
                  <span className="text-xs text-gray-500">
                    Last saved: {documentState.lastSaved.toLocaleString()}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
        
        <div className="mt-4 flex space-x-2">
          <button
            onClick={handleSaveDocument}
            disabled={isLoading || !documentState?.hasUnsavedChanges}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Saving...' : 'Save Document'}
          </button>
        </div>
      </div>

      {/* Current Selection */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Current Selection</h3>
        {currentSelection ? (
          <div className="space-y-3">
            <div>
              <span className="text-sm font-medium text-gray-700">Selected Text:</span>
              <div className="mt-1 p-3 bg-gray-50 rounded-lg border">
                {currentSelection.isEmpty ? (
                  <span className="text-gray-500 italic">No text selected (cursor position)</span>
                ) : (
                  <p className="text-sm text-gray-900 whitespace-pre-wrap">{currentSelection.range.text}</p>
                )}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium text-gray-700">Start Position:</span>
                <span className="ml-2 text-gray-900">{currentSelection.range.start}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">End Position:</span>
                <span className="ml-2 text-gray-900">{currentSelection.range.end}</span>
              </div>
            </div>
            
            {!currentSelection.isEmpty && (
              <div className="pt-3 border-t">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Replace Selection With:
                </label>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    placeholder="Enter new content..."
                    className="input-field flex-1"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        const target = e.target as HTMLInputElement;
                        if (target.value.trim()) {
                          handleReplaceSelection(target.value.trim());
                          target.value = '';
                        }
                      }
                    }}
                  />
                  <button
                    onClick={() => {
                      const input = document.querySelector('input[placeholder="Enter new content..."]') as HTMLInputElement;
                      if (input?.value.trim()) {
                        handleReplaceSelection(input.value.trim());
                        input.value = '';
                      }
                    }}
                    className="btn-secondary"
                  >
                    Replace
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-gray-500">No selection information available</p>
        )}
      </div>

      {/* Content Reading */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Document Content</h3>
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleReadContent()}
              disabled={isLoading}
              className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Reading...' : 'Read Full Content'}
            </button>
            <button
              onClick={() => handleReadContent({ includeTables: true, includeImages: true })}
              disabled={isLoading}
              className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Reading...' : 'Read with Tables & Images'}
            </button>
          </div>
          
          {documentContent && (
            <div className="space-y-3">
              <div>
                <span className="text-sm font-medium text-gray-700">Document Text:</span>
                <div className="mt-1 p-3 bg-gray-50 rounded-lg border max-h-40 overflow-y-auto">
                  <p className="text-sm text-gray-900 whitespace-pre-wrap">{documentContent.text}</p>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Paragraphs:</span>
                  <span className="ml-2 text-gray-900">{documentContent.paragraphs.length}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Tables:</span>
                  <span className="ml-2 text-gray-900">{documentContent.tables.length}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Images:</span>
                  <span className="ml-2 text-gray-900">{documentContent.images.length}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* MCP Tool Integration */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">MCP Tool Analysis</h3>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Tool:
              </label>
              <select
                value={selectedTool}
                onChange={(e) => setSelectedTool(e.target.value)}
                className="input-field"
                disabled={!documentContent}
              >
                <option value="">Choose a tool...</option>
                {availableTools.map(tool => (
                  <option key={tool} value={tool}>
                    {tool.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="flex items-end">
              <button
                onClick={handleExecuteTool}
                disabled={!selectedTool || !documentContent || isExecutingTool}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isExecutingTool ? 'Executing...' : 'Execute Tool'}
              </button>
            </div>
          </div>
          
          {toolExecutionResult && (
            <div className="space-y-3">
              <div>
                <span className="text-sm font-medium text-gray-700">Tool Result:</span>
                <div className="mt-1 p-3 bg-gray-50 rounded-lg border">
                  {toolExecutionResult.success ? (
                    <div>
                      <div className="text-sm text-gray-900">
                        <strong>Status:</strong> ✅ Success
                        {toolExecutionResult.executionTime && (
                          <span className="ml-4 text-gray-600">
                            (Executed in {toolExecutionResult.executionTime}ms)
                          </span>
                        )}
                      </div>
                      <div className="mt-2">
                        <strong>Result:</strong>
                        <pre className="mt-1 text-xs bg-white p-2 rounded border overflow-x-auto">
                          {JSON.stringify(toolExecutionResult.result, null, 2)}
                        </pre>
                      </div>
                    </div>
                  ) : (
                    <div className="text-red-600">
                      <strong>Status:</strong> ❌ Failed
                      <div className="mt-1">{toolExecutionResult.error}</div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
          
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
              ⚠️ {error}
            </div>
          )}
        </div>
      </div>

      {/* Content Insertion */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Insert Content</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Content to Insert:
            </label>
            <textarea
              value={insertContent}
              onChange={(e) => setInsertContent(e.target.value)}
              placeholder="Enter content to insert into the document..."
              className="input-field"
              rows={3}
            />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Insert Location:
              </label>
              <select
                value={insertOptions.insertLocation}
                onChange={(e) => setInsertionOptions(prev => ({ 
                  ...prev, 
                  insertLocation: e.target.value as InsertionOptions['insertLocation'] 
                }))}
                className="input-field"
              >
                <option value="start">Start of Document</option>
                <option value="end">End of Document</option>
                <option value="replace">Replace Selection</option>
                <option value="before">Before Selection</option>
                <option value="after">After Selection</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Formatting:
              </label>
              <select
                value={insertOptions.formatting}
                onChange={(e) => setInsertionOptions(prev => ({ 
                  ...prev, 
                  formatting: e.target.value as InsertionOptions['formatting'] 
                }))}
                className="input-field"
              >
                <option value="keep">Keep Existing</option>
                <option value="matchDestination">Match Document</option>
                <option value="matchSource">Match Source</option>
              </select>
            </div>
            
            <div className="flex items-end">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={insertOptions.trackChanges}
                  onChange={(e) => setInsertionOptions(prev => ({ 
                    ...prev, 
                    trackChanges: e.target.checked 
                  }))}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-700">Track Changes</span>
              </label>
            </div>
          </div>
          
          <button
            onClick={handleInsertContent}
            disabled={isLoading || !insertContent.trim()}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Inserting...' : 'Insert Content'}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="card border-red-200 bg-red-50">
          <div className="flex items-center space-x-2 text-red-700">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <span className="font-medium">Error:</span>
            <span>{error}</span>
          </div>
          <button
            onClick={() => setError(null)}
            className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
};

export default DocumentIntegration;
