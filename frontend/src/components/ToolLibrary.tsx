import React, { useState, useEffect } from 'react';
import mcpToolService, { MCPTool } from '../services/mcpToolService';

interface ToolLibraryProps {}

const ToolLibrary: React.FC<ToolLibraryProps> = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Load tools on component mount
  useEffect(() => {
    loadTools();
  }, []);

  const loadTools = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const discoveredTools = await mcpToolService.discoverTools();
      setTools(discoveredTools);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to load tools:', err);
      setError(`Failed to load tools: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshTools = async () => {
    await loadTools();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available':
        return 'bg-green-100 text-green-800';
      case 'unavailable':
        return 'bg-yellow-100 text-yellow-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'available':
        return 'Available';
      case 'unavailable':
        return 'Unavailable';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  const categories = ['all', ...Array.from(new Set(tools.map(tool => tool.category)))];

  const filteredTools = tools.filter(tool => {
    const matchesCategory = selectedCategory === 'all' || tool.category === selectedCategory;
    const matchesSearch = tool.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         tool.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-center h-64">
            <div className="flex items-center space-x-2 text-gray-500">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
              <span>Loading tools...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="text-center">
            <div className="text-red-600 text-lg font-medium mb-2">Failed to load tools</div>
            <div className="text-gray-600 mb-4">{error}</div>
            <button
              onClick={refreshTools}
              className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">MCP Tool Library</h1>
              <p className="text-sm text-gray-600 mt-1">
                Discover and explore available MCP tools for document processing and analysis
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={refreshTools}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
              >
                Refresh
              </button>
              {lastUpdated && (
                <span className="text-xs text-gray-500">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex flex-wrap gap-4">
            {/* Category Filter */}
            <div className="flex-1 min-w-48">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category
              </label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {categories.map(category => (
                  <option key={category} value={category}>
                    {category === 'all' ? 'All Categories' : category}
                  </option>
                ))}
              </select>
            </div>

            {/* Search */}
            <div className="flex-1 min-w-48">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search Tools
              </label>
              <input
                type="text"
                placeholder="Search by name or description..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            {/* Tool Count */}
            <div className="flex items-end">
              <div className="text-sm text-gray-600">
                {filteredTools.length} of {tools.length} tools
              </div>
            </div>
          </div>
        </div>

        {/* Tools Grid */}
        <div className="p-6">
          {filteredTools.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-500 text-lg mb-2">No tools found</div>
              <div className="text-gray-400 text-sm">
                Try adjusting your search criteria or category filter
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredTools.map(tool => (
                <div
                  key={tool.name}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  {/* Tool Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900 mb-1">{tool.name}</h3>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(tool.status)}`}>
                          {getStatusText(tool.status)}
                        </span>
                        <span className="text-xs text-gray-500">v{tool.version}</span>
                      </div>
                    </div>
                  </div>

                  {/* Tool Description */}
                  <p className="text-sm text-gray-600 mb-4 line-clamp-3">
                    {tool.description}
                  </p>

                  {/* Tool Category */}
                  <div className="mb-3">
                    <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                      {tool.category}
                    </span>
                  </div>

                  {/* Tool Parameters */}
                  {tool.parameters.length > 0 && (
                    <div className="mb-3">
                      <div className="text-xs text-gray-500 mb-1">Parameters:</div>
                      <div className="space-y-1">
                        {tool.parameters.slice(0, 3).map(param => (
                          <div key={param.name} className="text-xs text-gray-600">
                            <span className="font-medium">{param.name}</span>
                            <span className="text-gray-400"> ({param.type})</span>
                            {param.required && <span className="text-red-500"> *</span>}
                          </div>
                        ))}
                        {tool.parameters.length > 3 && (
                          <div className="text-xs text-gray-400">
                            +{tool.parameters.length - 3} more parameters
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Tool Usage Stats */}
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    {tool.lastUsed && (
                      <span>Last used: {tool.lastUsed.toLocaleDateString()}</span>
                    )}
                    {tool.usageCount > 0 && (
                      <span>Used {tool.usageCount} times</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ToolLibrary;
