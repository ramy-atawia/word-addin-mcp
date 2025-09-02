import * as React from 'react';
import { useState, useEffect } from 'react';
import { 
  TabList, 
  Tab, 
  makeStyles,
  tokens,
  Text,
  Badge,
  Button
} from '@fluentui/react-components';
import { 
  Chat24Regular,
  Toolbox24Regular,
  History24Regular,
  Settings24Regular,
  Add24Regular,
  ArrowClockwise24Regular
} from '@fluentui/react-icons';

// Import our new modular components
import ChatInterface from './ChatInterface/ChatInterface';
import ToolLibrary from './ToolLibrary/ToolLibrary';

import { ExternalMCPServerManager } from './ExternalMCPServerManager';
import { MCPTool, MCPToolExecutionResult, MCPConnectionStatus } from '../services/types';
import { AddServerModal } from './ExternalMCPServerManager/AddServerModal';
import ServerToolsList from './ServerToolsList/ServerToolsList';
import mcpToolService from '../services/mcpToolService';
import { getApiUrl } from '../../config/backend';

const useStyles = makeStyles({
  root: {
    padding: '12px', // Reduced from 16px for mobile
    maxWidth: '100%',
    height: '100vh', // Fixed height for proper containment
    backgroundColor: tokens.colorNeutralBackground1,
    overflow: 'hidden', // Prevent scrolling on main container
    display: 'flex', // Enable flexbox
    flexDirection: 'column', // Stack children vertically
    minHeight: 0, // Allow container to shrink
    // Responsive design
    '@media (min-width: 768px)': {
      padding: '16px',
    },
    '@media (min-width: 1024px)': {
      padding: '20px',
    },
  },
  header: {
    marginBottom: '16px', // Reduced from 24px
    textAlign: 'center',
    padding: '12px', // Reduced from 16px for mobile
    background: `linear-gradient(135deg, ${tokens.colorBrandBackground} 0%, ${tokens.colorBrandBackground2} 100%)`,
    borderRadius: tokens.borderRadiusLarge,
    color: tokens.colorNeutralForegroundOnBrand,
    // Responsive design
    '@media (min-width: 768px)': {
      padding: '16px',
    },
  },

  headerTitle: {
    fontSize: '20px', // Reduced from 24px for mobile
    fontWeight: '700',
    marginBottom: '8px',
    // Responsive design
    '@media (min-width: 768px)': {
      fontSize: '24px',
    },
  },
  headerSubtitle: {
    fontSize: '12px', // Reduced from 14px for mobile
    opacity: 0.9,
    lineHeight: '1.5',
    // Responsive design
    '@media (min-width: 768px)': {
      fontSize: '14px',
    },
  },
  tabContainer: {
    marginBottom: '16px', // Reduced from 24px
    backgroundColor: tokens.colorNeutralBackground2,
    borderRadius: tokens.borderRadiusMedium,
    padding: '4px', // Reduced from 6px for mobile
    boxShadow: tokens.shadow4,
    // Responsive design
    '@media (min-width: 768px)': {
      padding: '6px',
    },
  },
  tabContent: {
    flex: 1, // Take remaining space
    backgroundColor: tokens.colorNeutralBackground1,
    borderRadius: tokens.borderRadiusMedium,
    border: `1px solid ${tokens.colorNeutralStroke1}`,
    overflow: 'hidden', // Let child components handle scrolling
    display: 'flex', // Enable flexbox for proper height distribution
    flexDirection: 'column', // Stack children vertically
    minHeight: 0, // Allow container to shrink below content size
    // Responsive design - removed fixed heights
  },
  statsBar: {
    display: 'flex',
    justifyContent: 'center',
    gap: '20px', // Reduced from 40px for mobile
    marginBottom: '20px',
    padding: '12px', // Reduced from 16px for mobile
    backgroundColor: tokens.colorNeutralBackground2,
    borderRadius: tokens.borderRadiusMedium,
    border: `1px solid ${tokens.colorNeutralStroke1}`,
    // Responsive design
    '@media (min-width: 768px)': {
      gap: '40px',
      padding: '16px',
    },
  },
  statItem: {
    textAlign: 'center',
  },
  statNumber: {
    fontSize: '20px',
    fontWeight: '600',
    color: tokens.colorBrandForeground1,
  },
  statLabel: {
    fontSize: '12px',
    color: tokens.colorNeutralForeground2,
    marginTop: '4px',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  historyContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
    height: '100%', // Take full height
    overflow: 'hidden', // Prevent scrolling on container
  },
});

// Add CSS animations
const globalStyles = `
  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-5px); }
    75% { transform: translateX(5px); }
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }
`;

type TabValue = 'chat' | 'history' | 'settings';

const MCPToolManager: React.FC = () => {
  const styles = useStyles();
  const [selectedTab, setSelectedTab] = useState<TabValue>('chat');
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);
  const [loading, setLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<MCPConnectionStatus | null>(null);
  const [executionHistory, setExecutionHistory] = useState<Array<{
    tool: string;
    parameters: any;
    result: any; // Change type to any or a more generic interface
    timestamp: Date;
  }>>([]);
  // currentExecution is removed as direct tool execution from UI is deprecated
  // const [currentExecution, setCurrentExecution] = useState<{
  //   tool: string;
  //   parameters: any;
  //   result: MCPToolExecutionResult | null;
  // } | null>(null);
  
  // Chat state moved to parent to persist across tab switches
  const [chatMessages, setChatMessages] = useState<Array<{
    id: string;
    type: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: Date;
    metadata?: any;
  }>>([]);
  const [chatLoading, setChatLoading] = useState(false);

  // Using mcpToolService directly
  
  // Background auto-refresh functionality (always on)
  useEffect(() => {
    const interval = setInterval(() => {
      // Complete data refresh - load both tools and servers
      const refreshData = async () => {
        try {
          // Load tools first
          const toolsResponse = await fetch('https://localhost:9000/api/v1/mcp/tools');
          if (toolsResponse.ok) {
            const toolsData = await toolsResponse.json();
            if (toolsData.tools) {
              setTools(toolsData.tools);
            }
          }

          // Add internal server
          const internalServer = {
            id: 'internal',
            name: 'Internal Server',
            url: 'localhost:9000',
            status: 'healthy',
            connected: true,
            toolCount: 0
          };

          // Load external servers
          const serversResponse = await fetch('https://localhost:9000/api/v1/mcp/external/servers');
          if (serversResponse.ok) {
            const serversData = await serversResponse.json();
            if (serversData.servers) {
              const externalServers = serversData.servers.map((serverInfo: any) => ({
                id: serverInfo.server_id,
                name: serverInfo.name,
                url: serverInfo.url,
                status: serverInfo.status,
                connected: serverInfo.connected,
                toolCount: 0
              }));
              setServers([internalServer, ...externalServers]);
            } else {
              setServers([internalServer]);
            }
          } else {
            setServers([internalServer]);
          }

          // Also refresh connection status
          checkConnection(mcpToolService);
        } catch (error) {
          console.error('Background auto-refresh failed:', error);
        }
      };
      refreshData();
    }, 30000); // Refresh every 30 seconds

    return () => {
      clearInterval(interval);
    };
  }, []); // Run once on mount, no dependencies

  useEffect(() => {
    // Initialize with mcpToolService
    mcpToolService.setBaseUrl('https://localhost:9000');
    checkConnection(mcpToolService);
    loadTools(mcpToolService);
  }, []);

  const checkConnection = async (service: any) => {
    const status = await service.testConnection();
    setConnectionStatus(status);
  };

  const loadTools = async (service: any) => {
    setLoading(true);
    try {
      console.log('Loading MCP tools...');
      const availableTools = await service.discoverTools();
      console.log('Available tools received:', availableTools);
      setTools(availableTools);
    } catch (error) {
      console.error('Error loading tools:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToolSelect = (tool: MCPTool) => {
    setSelectedTool(tool);
    // No longer switching to an execution tab directly, as agent handles execution
    // setSelectedTab('settings'); // Removed
    // setCurrentExecution commented out as it is no longer needed after removing ToolExecution component
    // setCurrentExecution({
    //   tool: tool.name,
    //   parameters: {},
    //   result: null
    // });
  };

  // handleToolExecute is removed as agent handles execution

  const handleBackToTools = () => {
    setSelectedTab('settings');
    setSelectedTool(null);
    // setCurrentExecution(null); // Removed
  };

  // Chat message handlers
  const handleChatMessage = (message: {
    id: string;
    type: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: Date;
    metadata?: any;
  }) => {
    setChatMessages(prev => [...prev, message]);
  };

  const handleChatLoading = (loading: boolean) => {
    setChatLoading(loading);
  };

  const renderChatTab = () => (
    <ChatInterface 
      onToolSelect={handleToolSelect}
      messages={chatMessages}
      onMessage={handleChatMessage}
      loading={chatLoading}
      onLoadingChange={handleChatLoading}
    />
  );

  const renderToolsTab = () => (
    <ToolLibrary
      tools={tools}
      loading={loading}
      selectedTool={selectedTool}
      onToolSelect={handleToolSelect}
    />
  );

  // renderExecutionTab is removed as direct tool execution from UI is deprecated

  const renderHistoryTab = () => (
    <div style={{ padding: '24px' }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '12px', 
        marginBottom: '24px' 
      }}>
        <History24Regular />
        <Text size={500} style={{ fontWeight: '600' }}>
          Chat History
        </Text>
      </div>
      
      <div style={{ 
        textAlign: 'center', 
        padding: '60px 20px', 
        color: tokens.colorNeutralForeground3 
      }}>
        <History24Regular style={{ fontSize: '48px', marginBottom: '16px' }} />
        <Text size={400} style={{ marginBottom: '8px' }}>
          Chat History Coming Soon
        </Text>
        <Text size={200}>
          This tab will display your previous chat conversations and AI interactions
        </Text>
        <Text size={200} style={{ marginTop: '16px', opacity: 0.7 }}>
          Features planned:
        </Text>
        <ul style={{ 
          textAlign: 'left', 
          display: 'inline-block', 
          marginTop: '8px',
          opacity: 0.7 
        }}>
          <li>Previous chat sessions</li>
          <li>Tool execution history</li>
          <li>Document processing history</li>
          <li>Search and filter capabilities</li>
        </ul>
      </div>
    </div>
  );

  const [showAddModal, setShowAddModal] = useState(false);
  const [servers, setServers] = useState<any[]>([]); // State to hold connected servers
  const [isLoading, setIsLoading] = useState(true);

  // Enhanced tool interface with server information
  interface EnhancedTool extends MCPTool {
    server_name?: string;
    server_id?: string;
    source?: string;
  }

  // Load servers and tools from the correct endpoints
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      try {
        // Load tools first
        const toolsResponse = await fetch('https://localhost:9000/api/v1/mcp/tools');
        if (toolsResponse.ok) {
          const toolsData = await toolsResponse.json();
          if (toolsData.tools) {
            setTools(toolsData.tools);
          }
        }

        // Add internal server
        const internalServer = {
          id: 'internal',
          name: 'Internal Server',
          url: 'localhost:9000',
          status: 'healthy',
          connected: true,
          toolCount: 0 // Will be updated after tools are loaded
        };

        // Load external servers
        const serversResponse = await fetch('https://localhost:9000/api/v1/mcp/external/servers');
        if (serversResponse.ok) {
          const serversData = await serversResponse.json();
          if (serversData.servers) {
            const externalServers = serversData.servers.map((serverInfo: any) => ({
              id: serverInfo.server_id,
              name: serverInfo.name,
              url: serverInfo.url,
              status: serverInfo.status,
              connected: serverInfo.connected,
              toolCount: 0 // Will be updated after tools are loaded
            }));
            setServers([internalServer, ...externalServers]);
          } else {
            setServers([internalServer]);
          }
        } else {
          setServers([internalServer]);
        }
      } catch (error) {
        console.error('Failed to load data:', error);
        // Fallback to just internal server
        setServers([{
          id: 'internal',
          name: 'Internal Server',
          url: 'localhost:9000',
          status: 'healthy',
          connected: true,
          toolCount: 0
        }]);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadData();
  }, []);

  // Update tool counts when tools are loaded
  useEffect(() => {
    if (tools.length > 0 && servers.length > 0) {
      const updatedServers = servers.map(server => {
        if (server.name === 'Internal Server') {
          return {
            ...server,
            toolCount: tools.filter(tool => (tool as EnhancedTool).source === 'internal').length
          };
        } else {
          return {
            ...server,
            toolCount: tools.filter(tool => (tool as EnhancedTool).server_id === server.id).length
          };
        }
      });
      setServers(updatedServers);
    }
  }, [tools, servers.length]);

  const handleAddServer = async (newServer: any) => {
    try {
      console.log('🚀 Adding server to backend:', newServer);
      
      const requestBody = {
        name: newServer.name,
        server_url: newServer.url,  // Backend expects 'server_url' not 'url'
        description: newServer.description || '',
        server_type: newServer.serverType || 'custom',
        authentication_type: newServer.authenticationType || 'none'
      };
      
      console.log('📤 Request body being sent:', requestBody);
      console.log('📤 JSON stringified:', JSON.stringify(requestBody));
      
      const response = await fetch(getApiUrl('EXTERNAL_SERVERS'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('✅ Server added successfully:', result);
      
      // Add server to frontend state with backend response data
      setServers(prev => [...prev, {
        id: result.server_id,
        name: result.name,
        url: result.server_url || result.url, // Handle both field names
        status: result.server_info?.status || 'connected',
        connected: result.server_info?.connected || true,
        toolCount: 0,
        lastSeen: new Date().toISOString()
      }]);
      
      // Immediately refresh data to get updated tool counts and server status
      const refreshData = async () => {
        try {
          // Load tools first
          const toolsResponse = await fetch('https://localhost:9000/api/v1/mcp/tools');
          if (toolsResponse.ok) {
            const toolsData = await toolsResponse.json();
            if (toolsData.tools) {
              setTools(toolsData.tools);
            }
          }

          // Add internal server
          const internalServer = {
            id: 'internal',
            name: 'Internal Server',
            url: 'localhost:9000',
            status: 'healthy',
            connected: true,
            toolCount: 0
          };

          // Load external servers
          const serversResponse = await fetch('https://localhost:9000/api/v1/mcp/external/servers');
          if (serversResponse.ok) {
            const serversData = await serversResponse.json();
            if (serversData.servers) {
              const externalServers = serversData.servers.map((serverInfo: any) => ({
                id: serverInfo.server_id,
                name: serverInfo.name,
                url: serverInfo.url,
                status: serverInfo.status,
                connected: serverInfo.connected,
                toolCount: 0
              }));
              setServers([internalServer, ...externalServers]);
            } else {
              setServers([internalServer]);
            }
          } else {
            setServers([internalServer]);
          }
        } catch (error) {
          console.error('Post-add refresh failed:', error);
        }
      };
      refreshData();
      
      setShowAddModal(false);
      
    } catch (error) {
      console.error('❌ Failed to add server:', error);
      throw error; // Re-throw to show error in modal
    }
  };

  const renderSettingsTab = () => (
    <div style={{ padding: '24px' }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '12px', 
        marginBottom: '24px' 
      }}>
        <Settings24Regular />
        <Text size={500} style={{ fontWeight: '600' }}>
          MCP Servers & Tools
        </Text>
      </div>
      
      {/* Loading State */}
      {isLoading && (
        <div style={{
          textAlign: 'center',
          padding: '40px',
          color: tokens.colorNeutralForeground2
        }}>
          <Text size={400}>Loading MCP servers and tools...</Text>
        </div>
      )}

      {/* Server List with Expandable Tools */}
      {!isLoading && (
        <div style={{
          backgroundColor: tokens.colorNeutralBackground2,
          borderRadius: tokens.borderRadiusMedium,
          border: `1px solid ${tokens.colorNeutralStroke1}`,
          overflow: 'hidden'
        }}>
        {/* Header */}
        <div style={{
          padding: '20px',
          borderBottom: `1px solid ${tokens.colorNeutralStroke1}`,
          backgroundColor: tokens.colorNeutralBackground1
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <Text size={400} style={{ fontWeight: '600', marginBottom: '4px' }}>
                Connected MCP Servers
              </Text>
              <Text size={200} style={{ color: tokens.colorNeutralForeground2 }}>
                {servers.length} servers • {tools.length} total tools
              </Text>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <Button 
                appearance="outline"
                onClick={() => {
                  // Refresh data
                  setTools([]);
                  setServers([]);
                  setTimeout(() => {
                    const loadData = async () => {
                      try {
                        // Load tools first
                        const toolsResponse = await fetch('https://localhost:9000/api/v1/mcp/tools');
                        if (toolsResponse.ok) {
                          const toolsData = await toolsResponse.json();
                          if (toolsData.tools) {
                            setTools(toolsData.tools);
                          }
                        }

                        // Add internal server
                        const internalServer = {
                          id: 'internal',
                          name: 'Internal Server',
                          url: 'localhost:9000',
                          status: 'healthy',
                          connected: true,
                          toolCount: 0
                        };

                        // Load external servers
                        const serversResponse = await fetch('https://localhost:9000/api/v1/mcp/external/servers');
                        if (serversResponse.ok) {
                          const serversData = await serversResponse.json();
                          if (serversData.servers) {
                            const externalServers = serversData.servers.map((serverInfo: any) => ({
                              id: serverInfo.server_id,
                              name: serverInfo.name,
                              url: serverInfo.url,
                              status: serverInfo.status,
                              connected: serverInfo.connected,
                              toolCount: 0
                            }));
                            setServers([internalServer, ...externalServers]);
                          } else {
                            setServers([internalServer]);
                          }
                        } else {
                          setServers([internalServer]);
                        }
                      } catch (error) {
                        console.error('Failed to refresh data:', error);
                      }
                    };
                    loadData();
                  }, 100);
                }}
                icon={<ArrowClockwise24Regular />}
              >
                Refresh
              </Button>
              <Button 
                appearance="outline"
                onClick={() => setShowAddModal(true)}
                icon={<Add24Regular />}
              >
                Add Server
              </Button>
            </div>
          </div>
        </div>

        {/* Server List */}
        <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
          {servers.length === 0 ? (
            <div style={{
              padding: '40px 20px',
              textAlign: 'center',
              color: tokens.colorNeutralForeground3
            }}>
              <Text size={300} style={{ marginBottom: '8px' }}>
                No MCP servers connected
              </Text>
              <Text size={200}>
                Add your first MCP server to get started
              </Text>
            </div>
          ) : (
            servers.map((server, index) => {
              // Filter tools by server ID for external servers, or by source for internal server
              const serverTools = server.name === 'Internal Server' 
                ? tools.filter(tool => (tool as EnhancedTool).source === 'internal')
                : tools.filter(tool => (tool as EnhancedTool).server_id === server.id);
              
              // Debug logging
              console.log(`Server: ${server.name} (${server.id})`, {
                totalTools: tools.length,
                serverTools: serverTools.length,
                toolNames: serverTools.map(t => t.name)
              });
              
              return (
                <ServerToolsList 
                  key={server.id}
                  server={server}
                  tools={serverTools}
                  isLast={index === servers.length - 1}
                />
              );
            })
          )}
        </div>
        </div>
      )}

      {/* Add Server Modal */}
      {showAddModal && (
        <AddServerModal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          onAdd={handleAddServer}
        />
      )}
    </div>
  );

  return (
    <div className={styles.root}>
      <div className={styles.header}>
        <div className={styles.headerTitle}>Novitai MCP - Word Add-in</div>
        <div className={styles.headerSubtitle}>
          AI-powered document processing and research tools
        </div>
      </div>

      <div className={styles.tabContainer}>
        <TabList 
          selectedValue={selectedTab} 
          onTabSelect={(_, data) => setSelectedTab(data.value as TabValue)}
        >
          <Tab value="chat" icon={<Chat24Regular />}>AI Chat</Tab>
          <Tab value="history" icon={<History24Regular />}>History</Tab>
          <Tab value="settings" icon={<Settings24Regular />}>Settings</Tab>
        </TabList>
      </div>

      <div className={styles.tabContent}>
        {selectedTab === 'chat' && (
          <div style={{ 
            height: '100%', 
            overflow: 'hidden' // Let ChatInterface handle its own scrolling
          }}>
            {renderChatTab()}
          </div>
        )}
        {/* Tools Library moved to Settings tab */}
        {selectedTab === 'history' && (
          <div className={styles.historyContainer}>
            <div className={styles.statsBar}>
              <div className={styles.statItem}>
                <div className={styles.statNumber}>{tools.length}</div>
                <div className={styles.statLabel}>AI Tools</div>
              </div>
              <div className={styles.statItem}>
                <div className={styles.statNumber}>{executionHistory.length}</div>
                <div className={styles.statLabel}>Executions</div>
              </div>
              <div className={styles.statItem}>
                <div className={styles.statNumber}>
                  {executionHistory.filter(e => e.result.success).length}
                </div>
                <div className={styles.statLabel}>Successful</div>
              </div>
              <div className={styles.statItem}>
                <div className={styles.statNumber}>
                  {connectionStatus === 'connected' ? 'Online' : 'Offline'}
                </div>
                <div className={styles.statLabel}>Status</div>
              </div>
            </div>
            <div style={{ 
              flex: 1, 
              overflowY: 'auto', 
              padding: '16px',
              paddingRight: '8px' // Space for scrollbar
            }}>
              {renderHistoryTab()}
            </div>
          </div>
        )}

        {selectedTab === 'settings' && (
          <div style={{ 
            height: '100%', 
            overflowY: 'auto', 
            padding: '16px',
            paddingRight: '8px' // Space for scrollbar
          }}>
            {renderSettingsTab()}
          </div>
        )}
      </div>
    </div>
  );
};

export default MCPToolManager;
