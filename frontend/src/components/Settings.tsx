import React, { useState, useEffect, useCallback } from 'react';

interface MCPServer {
  id: string;
  name: string;
  url: string;
  status: 'connected' | 'disconnected' | 'error' | 'testing';
  lastConnected?: Date;
  autoConnect: boolean;
  timeout: number;
  retryAttempts: number;
  healthCheckInterval: number;
}

interface AppSettings {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  notifications: boolean;
  autoSave: boolean;
  maxHistorySize: number;
  autoConnectServers: boolean;
  connectionTimeout: number;
  maxRetryAttempts: number;
  healthCheckEnabled: boolean;
  healthCheckInterval: number;
}

interface ConnectionTestResult {
  success: boolean;
  responseTime: number;
  error?: string;
  details?: any;
}

const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'servers' | 'general' | 'advanced'>('servers');
  const [mcpServers, setMcpServers] = useState<MCPServer[]>([
    {
      id: '1',
      name: 'Local MCP Server',
              url: 'http://localhost:9000',
      status: 'connected',
      lastConnected: new Date(),
      autoConnect: true,
      timeout: 30,
      retryAttempts: 3,
      healthCheckInterval: 60
    },
    {
      id: '2',
      name: 'Remote MCP Server',
      url: 'https://remote-mcp.example.com',
      status: 'disconnected',
      autoConnect: false,
      timeout: 30,
      retryAttempts: 3,
      healthCheckInterval: 60
    }
  ]);

  const [settings, setSettings] = useState<AppSettings>({
    theme: 'light',
    language: 'en',
    notifications: true,
    autoSave: true,
    maxHistorySize: 100,
    autoConnectServers: true,
    connectionTimeout: 30,
    maxRetryAttempts: 3,
    healthCheckEnabled: true,
    healthCheckInterval: 60
  });

  const [newServer, setNewServer] = useState({
    name: '',
    url: '',
    autoConnect: false,
    timeout: 30,
    retryAttempts: 3,
    healthCheckInterval: 60
  });

  const [testingConnections, setTestingConnections] = useState<Set<string>>(new Set());
  const [connectionResults, setConnectionResults] = useState<Record<string, ConnectionTestResult>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Load settings from localStorage on component mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = () => {
    try {
      const savedSettings = localStorage.getItem('appSettings');
      const savedServers = localStorage.getItem('mcpServers');
      
      if (savedSettings) {
        setSettings(prev => ({ ...prev, ...JSON.parse(savedSettings) }));
      }
      
      if (savedServers) {
        const servers = JSON.parse(savedServers);
        // Convert date strings back to Date objects
        servers.forEach((server: MCPServer) => {
          if (server.lastConnected) {
            server.lastConnected = new Date(server.lastConnected);
          }
        });
        setMcpServers(servers);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const saveSettings = useCallback(async () => {
    setIsSaving(true);
    setSaveMessage(null);
    
    try {
      // Save to localStorage
      localStorage.setItem('appSettings', JSON.stringify(settings));
      localStorage.setItem('mcpServers', JSON.stringify(mcpServers));
      
      // In a real app, you would also save to backend
      // await api.saveSettings({ settings, mcpServers });
      
      setSaveMessage({ type: 'success', text: 'Settings saved successfully!' });
      
      // Clear success message after 3 seconds
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (error) {
      console.error('Failed to save settings:', error);
      setSaveMessage({ type: 'error', text: 'Failed to save settings. Please try again.' });
    } finally {
      setIsSaving(false);
    }
  }, [settings, mcpServers]);

  const testConnection = async (server: MCPServer): Promise<ConnectionTestResult> => {
    try {
      const startTime = Date.now();
      
      // Test basic connectivity
      const response = await fetch(`${server.url}/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(server.timeout * 1000)
      });
      
      const responseTime = Date.now() - startTime;
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      return {
        success: true,
        responseTime,
        details: data
      };
    } catch (error) {
      return {
        success: false,
        responseTime: 0,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  };

  const handleTestConnection = async (serverId: string) => {
    const server = mcpServers.find(s => s.id === serverId);
    if (!server) return;
    
    setTestingConnections(prev => new Set(prev).add(serverId));
    setConnectionResults(prev => ({ ...prev, [serverId]: { success: false, responseTime: 0 } }));
    
    // Update server status to testing
    setMcpServers(prev => prev.map(s => 
      s.id === serverId ? { ...s, status: 'testing' } : s
    ));
    
    try {
      const result = await testConnection(server);
      setConnectionResults(prev => ({ ...prev, [serverId]: result }));
      
      // Update server status based on test result
      const newStatus = result.success ? 'connected' : 'error';
      setMcpServers(prev => prev.map(s => 
        s.id === serverId 
          ? { ...s, status: newStatus, lastConnected: result.success ? new Date() : s.lastConnected }
          : s
      ));
    } finally {
      setTestingConnections(prev => {
        const newSet = new Set(prev);
        newSet.delete(serverId);
        return newSet;
      });
    }
  };

  const handleTestAllConnections = async () => {
    const serversToTest = mcpServers.filter(server => server.status !== 'connected');
    
    for (const server of serversToTest) {
      await handleTestConnection(server.id);
      // Small delay between tests to avoid overwhelming servers
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  };

  const handleAddServer = () => {
    if (!newServer.name || !newServer.url) return;

    const server: MCPServer = {
      id: Date.now().toString(),
      name: newServer.name,
      url: newServer.url,
      status: 'disconnected',
      autoConnect: newServer.autoConnect,
      timeout: newServer.timeout,
      retryAttempts: newServer.retryAttempts,
      healthCheckInterval: newServer.healthCheckInterval
    };

    setMcpServers(prev => [...prev, server]);
    setNewServer({ 
      name: '', 
      url: '', 
      autoConnect: false, 
      timeout: 30, 
      retryAttempts: 3, 
      healthCheckInterval: 60 
    });
    
    // Auto-save after adding server
    setTimeout(saveSettings, 100);
  };

  const handleRemoveServer = (id: string) => {
    setMcpServers(prev => prev.filter(server => server.id !== id));
    setConnectionResults(prev => {
      const newResults = { ...prev };
      delete newResults[id];
      return newResults;
    });
    
    // Auto-save after removing server
    setTimeout(saveSettings, 100);
  };

  const handleConnectServer = async (id: string) => {
    await handleTestConnection(id);
  };

  const handleDisconnectServer = (id: string) => {
    setMcpServers(prev => prev.map(server => 
      server.id === id 
        ? { ...server, status: 'disconnected' }
        : server
    ));
    
    // Auto-save after disconnecting
    setTimeout(saveSettings, 100);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'bg-green-100 text-green-800';
      case 'disconnected': return 'bg-gray-100 text-gray-800';
      case 'error': return 'bg-red-100 text-red-800';
      case 'testing': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'connected': return 'Connected';
      case 'disconnected': return 'Disconnected';
      case 'error': return 'Error';
      case 'testing': return 'Testing...';
      default: return 'Unknown';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'disconnected':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
      case 'error':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        );
      case 'testing':
        return (
          <div className="w-4 h-4 animate-spin rounded-full border-2 border-current border-t-transparent"></div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="h-full">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">Configure MCP servers and application preferences</p>
      </div>

      {/* Save Message */}
      {saveMessage && (
        <div className={`mb-4 p-3 rounded-lg ${
          saveMessage.type === 'success' 
            ? 'bg-green-100 text-green-800 border border-green-200' 
            : 'bg-red-100 text-red-800 border border-red-200'
        }`}>
          {saveMessage.text}
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'servers', name: 'MCP Servers' },
            { id: 'general', name: 'General' },
            { id: 'advanced', name: 'Advanced' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'servers' && (
        <div className="space-y-6">
          {/* Add New Server */}
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Add New MCP Server</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Server Name
                </label>
                <input
                  type="text"
                  value={newServer.name}
                  onChange={(e) => setNewServer(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="My MCP Server"
                  className="input-field"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Server URL
                </label>
                <input
                  type="url"
                  value={newServer.url}
                  onChange={(e) => setNewServer(prev => ({ ...prev, url: e.target.value }))}
                  placeholder="https://server.example.com"
                  className="input-field"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Timeout (seconds)
                </label>
                <input
                  type="number"
                  value={newServer.timeout}
                  onChange={(e) => setNewServer(prev => ({ ...prev, timeout: parseInt(e.target.value) }))}
                  min="5"
                  max="120"
                  className="input-field"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={handleAddServer}
                  disabled={!newServer.name || !newServer.url}
                  className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Add Server
                </button>
              </div>
            </div>
            <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={newServer.autoConnect}
                  onChange={(e) => setNewServer(prev => ({ ...prev, autoConnect: e.target.checked }))}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-700">Auto-connect on startup</span>
              </label>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Retry Attempts
                </label>
                <input
                  type="number"
                  value={newServer.retryAttempts}
                  onChange={(e) => setNewServer(prev => ({ ...prev, retryAttempts: parseInt(e.target.value) }))}
                  min="1"
                  max="10"
                  className="input-field w-20"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Health Check (seconds)
                </label>
                <input
                  type="number"
                  value={newServer.healthCheckInterval}
                  onChange={(e) => setNewServer(prev => ({ ...prev, healthCheckInterval: parseInt(e.target.value) }))}
                  min="30"
                  max="3600"
                  className="input-field w-20"
                />
              </div>
            </div>
          </div>

          {/* Connection Testing */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Connection Testing</h3>
              <button
                onClick={handleTestAllConnections}
                className="btn-secondary text-sm"
                disabled={mcpServers.every(s => s.status === 'connected')}
              >
                Test All Connections
              </button>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Test connectivity to your MCP servers to ensure they're working properly.
            </p>
          </div>

          {/* Server List */}
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">MCP Servers</h3>
            <div className="space-y-4">
              {mcpServers.map(server => (
                <div key={server.id} className="border border-gray-200 rounded-lg overflow-hidden">
                  <div className="p-4 bg-gray-50 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <h4 className="text-sm font-medium text-gray-900">{server.name}</h4>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(server.status)}`}>
                          {getStatusIcon(server.status)}
                          <span className="ml-1">{getStatusText(server.status)}</span>
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleTestConnection(server.id)}
                          disabled={testingConnections.has(server.id)}
                          className="btn-secondary text-sm"
                        >
                          {testingConnections.has(server.id) ? 'Testing...' : 'Test'}
                        </button>
                        {server.status === 'connected' ? (
                          <button
                            onClick={() => handleDisconnectServer(server.id)}
                            className="btn-secondary text-sm"
                          >
                            Disconnect
                          </button>
                        ) : (
                          <button
                            onClick={() => handleConnectServer(server.id)}
                            className="btn-primary text-sm"
                          >
                            Connect
                          </button>
                        )}
                        <button
                          onClick={() => handleRemoveServer(server.id)}
                          className="text-red-600 hover:text-red-800 text-sm"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                    <p className="text-sm text-gray-500 mt-1">{server.url}</p>
                    {server.lastConnected && (
                      <p className="text-xs text-gray-400 mt-1">
                        Last connected: {server.lastConnected.toLocaleString()}
                      </p>
                    )}
                  </div>
                  
                  {/* Connection Test Results */}
                  {connectionResults[server.id] && (
                    <div className="p-3 bg-white border-t border-gray-200">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700">Connection Test Results:</span>
                        {connectionResults[server.id].success ? (
                          <span className="text-sm text-green-600">
                            ✓ Success ({connectionResults[server.id].responseTime}ms)
                          </span>
                        ) : (
                          <span className="text-sm text-red-600">
                            ✗ Failed: {connectionResults[server.id].error}
                          </span>
                        )}
                      </div>
                      {connectionResults[server.id].details && (
                        <div className="mt-2 text-xs text-gray-600">
                          <pre className="whitespace-pre-wrap">
                            {JSON.stringify(connectionResults[server.id].details, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* Server Configuration */}
                  <div className="p-3 bg-white border-t border-gray-200">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-gray-600">
                      <div>
                        <span className="font-medium">Timeout:</span> {server.timeout}s
                      </div>
                      <div>
                        <span className="font-medium">Retries:</span> {server.retryAttempts}
                      </div>
                      <div>
                        <span className="font-medium">Health Check:</span> {server.healthCheckInterval}s
                      </div>
                      <div>
                        <span className="font-medium">Auto-connect:</span> {server.autoConnect ? 'Yes' : 'No'}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'general' && (
        <div className="space-y-6">
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">General Settings</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Theme
                </label>
                <select
                  value={settings.theme}
                  onChange={(e) => setSettings(prev => ({ ...prev, theme: e.target.value as any }))}
                  className="input-field max-w-xs"
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="auto">Auto (System)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Language
                </label>
                <select
                  value={settings.language}
                  onChange={(e) => setSettings(prev => ({ ...prev, language: e.target.value }))}
                  className="input-field max-w-xs"
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                </select>
              </div>
              <div className="space-y-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={settings.notifications}
                    onChange={(e) => setSettings(prev => ({ ...prev, notifications: e.target.checked }))}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Enable notifications</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={settings.autoSave}
                    onChange={(e) => setSettings(prev => ({ ...prev, autoSave: e.target.checked }))}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Auto-save chat history</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={settings.autoConnectServers}
                    onChange={(e) => setSettings(prev => ({ ...prev, autoConnectServers: e.target.checked }))}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Auto-connect to MCP servers on startup</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'advanced' && (
        <div className="space-y-6">
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Advanced Settings</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Chat History Size
                </label>
                <input
                  type="number"
                  value={settings.maxHistorySize}
                  onChange={(e) => setSettings(prev => ({ ...prev, maxHistorySize: parseInt(e.target.value) }))}
                  min="10"
                  max="1000"
                  className="input-field max-w-xs"
                />
                <p className="text-xs text-gray-500 mt-1">Number of messages to keep in history</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Connection Timeout (seconds)
                </label>
                <input
                  type="number"
                  value={settings.connectionTimeout}
                  onChange={(e) => setSettings(prev => ({ ...prev, connectionTimeout: parseInt(e.target.value) }))}
                  min="5"
                  max="120"
                  className="input-field max-w-xs"
                />
                <p className="text-xs text-gray-500 mt-1">Default timeout for server connections</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Retry Attempts
                </label>
                <input
                  type="number"
                  value={settings.maxRetryAttempts}
                  onChange={(e) => setSettings(prev => ({ ...prev, maxRetryAttempts: parseInt(e.target.value) }))}
                  min="1"
                  max="10"
                  className="input-field max-w-xs"
                />
                <p className="text-xs text-gray-500 mt-1">Maximum number of connection retry attempts</p>
              </div>
              <div className="space-y-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={settings.healthCheckEnabled}
                    onChange={(e) => setSettings(prev => ({ ...prev, healthCheckEnabled: e.target.checked }))}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Enable automatic health checks</span>
                </label>
                {settings.healthCheckEnabled && (
                  <div className="ml-6">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Health Check Interval (seconds)
                    </label>
                    <input
                      type="number"
                      value={settings.healthCheckInterval}
                      onChange={(e) => setSettings(prev => ({ ...prev, healthCheckInterval: parseInt(e.target.value) }))}
                      min="30"
                      max="3600"
                      className="input-field max-w-xs"
                    />
                    <p className="text-xs text-gray-500 mt-1">How often to check server health</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Save Button */}
      <div className="mt-8 flex justify-end">
        <button 
          onClick={saveSettings}
          disabled={isSaving}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSaving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </div>
  );
};

export default Settings;
