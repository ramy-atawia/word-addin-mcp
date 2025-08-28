import React, { useState, useEffect } from 'react';
import mcpToolService, { MCPTool, MCPToolExecutionResult } from '../services/mcpToolService';

interface MCPToolManagerProps {
  onToolExecuted?: (result: MCPToolExecutionResult) => void;
}

type ViewMode = 'overview' | 'tools' | 'execution' | 'history';

const MCPToolManager: React.FC<MCPToolManagerProps> = ({ onToolExecuted }) => {
  const [viewMode, setViewMode] = useState<ViewMode>('overview');
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [executionHistory, setExecutionHistory] = useState<MCPToolExecutionResult[]>([]);
  const [executionParams, setExecutionParams] = useState<Record<string, any>>({});

  // Load tools on component mount
  useEffect(() => {
    loadTools();
    loadExecutionHistory();
  }, []);

  const loadTools = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const discoveredTools = await mcpToolService.discoverTools();
      setTools(discoveredTools);
    } catch (err) {
      setError(`Failed to load tools: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const loadExecutionHistory = async () => {
    try {
      const history = await mcpToolService.getToolExecutionHistory();
      setExecutionHistory(history);
    } catch (err) {
      console.error('Failed to load execution history:', err);
    }
  };

  const handleToolSelect = (tool: MCPTool) => {
    setSelectedTool(tool);
    setViewMode('execution');
    // Initialize execution parameters
    const initialParams: Record<string, any> = {};
    if (tool.parameters) {
      tool.parameters.forEach(param => {
        if (param.default !== undefined) {
          initialParams[param.name] = param.default;
        }
      });
    }
    setExecutionParams(initialParams);
  };

  const handleExecuteTool = async () => {
    if (!selectedTool) return;

    try {
      setIsLoading(true);
      setError(null);

      const request = {
        toolName: selectedTool.name,
        parameters: executionParams,
        sessionId: `session-${Date.now()}`
      };

      const result = await mcpToolService.executeTool(request);
      
      if (onToolExecuted) {
        onToolExecuted(result);
      }

      // Add to history
      setExecutionHistory(prev => [result, ...prev]);
      
      // Switch to history view
      setViewMode('history');
      
    } catch (err) {
      setError(`Tool execution failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleParameterChange = (key: string, value: any) => {
    setExecutionParams(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const renderOverview = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">MCP Tools Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{tools.length}</div>
            <div className="text-sm text-gray-600">Total Tools</div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {tools.filter(t => t.status === 'available').length}
            </div>
            <div className="text-sm text-gray-600">Available</div>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-gray-600">{executionHistory.length}</div>
            <div className="text-sm text-gray-600">Executions</div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-3">Recent Executions</h3>
        {executionHistory.slice(0, 5).map((execution, index) => (
          <div key={index} className="flex items-center justify-between py-2 border-b">
            <div>
              <div className="font-medium">{execution.toolName}</div>
                              <div className="text-sm text-gray-500">
                  {execution.success ? 'Success' : 'Failed'} • {new Date(execution.timestamp).toLocaleString()}
                </div>
            </div>
            <button
              onClick={() => {
                const tool = tools.find(t => t.name === execution.toolName);
                if (tool) handleToolSelect(tool);
              }}
              className="text-blue-600 hover:text-blue-800 text-sm"
            >
              Re-run
            </button>
          </div>
        ))}
      </div>
    </div>
  );

  const renderToolsList = () => (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Available Tools</h2>
      {isLoading ? (
        <div className="text-center py-8">Loading tools...</div>
      ) : error ? (
        <div className="text-red-600 text-center py-8">{error}</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tools.map((tool) => (
            <div
              key={tool.name}
              className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => handleToolSelect(tool)}
            >
              <div className="font-semibold text-lg mb-2">{tool.name}</div>
              <div className="text-gray-600 text-sm mb-3">{tool.description}</div>
              <div className="flex items-center justify-between">
                <span className={`px-2 py-1 rounded text-xs ${
                  tool.status === 'available' ? 'bg-green-100 text-green-800' :
                  tool.status === 'unavailable' ? 'bg-red-100 text-red-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {tool.status}
                </span>
                <button className="text-blue-600 hover:text-blue-800 text-sm">
                  Use Tool
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderToolExecution = () => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">
          Execute: {selectedTool?.name}
        </h2>
        <button
          onClick={() => setViewMode('overview')}
          className="text-gray-600 hover:text-gray-800"
        >
          ← Back to Overview
        </button>
      </div>

      {selectedTool && (
        <div className="space-y-4">
          <div className="text-gray-600 mb-4">{selectedTool.description}</div>
          
          {selectedTool.parameters && selectedTool.parameters.length > 0 && (
            <div className="space-y-4">
              <h3 className="font-semibold">Parameters</h3>
              {selectedTool.parameters.map((param) => (
                <div key={param.name}>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {param.name}
                    {param.required && <span className="text-red-500">*</span>}
                  </label>
                  <input
                    type="text"
                    value={executionParams[param.name] || ''}
                    onChange={(e) => handleParameterChange(param.name, e.target.value)}
                    placeholder={param.description || `Enter ${param.name}`}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {param.description && (
                    <p className="text-xs text-gray-500 mt-1">{param.description}</p>
                  )}
                </div>
              ))}
            </div>
          )}

          <div className="pt-4">
            <button
              onClick={handleExecuteTool}
              disabled={isLoading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Executing...' : 'Execute Tool'}
            </button>
          </div>

          {error && (
            <div className="text-red-600 text-center py-2">{error}</div>
          )}
        </div>
      )}
    </div>
  );

  const renderExecutionHistory = () => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">Execution History</h2>
        <button
          onClick={() => setViewMode('overview')}
          className="text-gray-600 hover:text-gray-800"
        >
          ← Back to Overview
        </button>
      </div>

      {executionHistory.length === 0 ? (
        <div className="text-center py-8 text-gray-500">No executions yet</div>
      ) : (
        <div className="space-y-4">
          {executionHistory.map((execution, index) => (
            <div key={index} className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="font-semibold">{execution.toolName}</div>
                <span className={`px-2 py-1 rounded text-xs ${
                  execution.success ? 'bg-green-100 text-green-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {execution.success ? 'Success' : 'Failed'}
                </span>
              </div>
              <div className="text-sm text-gray-600 mb-2">
                {new Date(execution.timestamp).toLocaleString()}
              </div>
              {execution.result && (
                <div className="bg-gray-50 p-3 rounded text-sm">
                  <pre className="whitespace-pre-wrap">{JSON.stringify(execution.result, null, 2)}</pre>
                </div>
              )}
              <div className="mt-3">
                <button
                  onClick={() => {
                    const tool = tools.find(t => t.name === execution.toolName);
                    if (tool) handleToolSelect(tool);
                  }}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  Re-run this tool
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderNavigation = () => (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <nav className="flex space-x-4">
        <button
          onClick={() => setViewMode('overview')}
          className={`px-3 py-2 rounded-md text-sm font-medium ${
            viewMode === 'overview'
              ? 'bg-blue-100 text-blue-700'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setViewMode('tools')}
          className={`px-3 py-2 rounded-md text-sm font-medium ${
            viewMode === 'tools'
              ? 'bg-blue-100 text-blue-700'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Tools
        </button>
        <button
          onClick={() => setViewMode('execution')}
          className={`px-3 py-2 rounded-md text-sm font-medium ${
            viewMode === 'execution'
              ? 'bg-blue-100 text-blue-700'
              : 'text-gray-500 hover:text-gray-700'
          }`}
          disabled={!selectedTool}
        >
          Execution
        </button>
        <button
          onClick={() => setViewMode('history')}
          className={`px-3 py-2 rounded-md text-sm font-medium ${
            viewMode === 'history'
              ? 'bg-blue-100 text-blue-700'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          History
        </button>
      </nav>
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">MCP Tool Manager</h1>
        <p className="text-gray-600 mt-2">
          Manage and execute Model Context Protocol tools
        </p>
      </div>

      {renderNavigation()}

      {viewMode === 'overview' && renderOverview()}
      {viewMode === 'tools' && renderToolsList()}
      {viewMode === 'execution' && renderToolExecution()}
      {viewMode === 'history' && renderExecutionHistory()}
    </div>
  );
};

export default MCPToolManager;
