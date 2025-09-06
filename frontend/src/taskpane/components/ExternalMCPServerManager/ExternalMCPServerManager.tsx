import React, { useState, useEffect } from 'react';
import {
  Button, Text, Badge, Spinner
} from '@fluentui/react-components';
import { 
  Add24Regular, Delete24Regular, Settings24Regular, Warning24Regular,
  CheckmarkCircle24Regular, ErrorCircle24Regular, Info24Regular
} from '@fluentui/react-icons';
import { AddServerModal } from './AddServerModal';
import { getApiUrl } from '../../../config/backend';

export interface ExternalMCPServer {
  id: string;
  name: string;
  url: string;
  status: 'connected' | 'disconnected' | 'connecting' | 'error';
  toolCount: number;
  lastSeen: string;
  health: {
    status: string;
    response_time?: number;
    error_message?: string;
    uptime?: string;
  };
}

export interface ServerHealthStatus {
  status: string;
  response_time?: number;
  error_message?: string;
  uptime?: string;
}

import { mapBackendStatusToFrontend } from '../../utils/statusUtils';

export const ExternalMCPServerManager: React.FC = () => {
  console.log('🚀 ExternalMCPServerManager component rendered!');
  
  const [servers, setServers] = useState<ExternalMCPServer[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [isHealthMonitoring, setIsHealthMonitoring] = useState(false);
  const [healthData, setHealthData] = useState<any>({});

  console.log('📊 Current state:', { 
    serversCount: servers.length, 
    isLoading, 
    showAddModal,
    error: !!error,
    success: !!success 
  });

  useEffect(() => {
    console.log('🔄 useEffect: loadServers called');
    loadServers();
  }, []);

  const loadServers = async () => {
    setIsLoading(true);
    try {
      console.log('Loading servers from:', getApiUrl('EXTERNAL_SERVERS'));
      
      // Call backend API to get real server list
      const response = await fetch(getApiUrl('EXTERNAL_SERVERS'), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);

      if (response.ok) {
        const responseData = await response.json();
        console.log('Raw server list from backend:', responseData);
        
        // Extract the servers array from the response
        const serverList = responseData.servers || [];
        console.log('Extracted server list:', serverList);
        
        // Convert backend format to frontend format
        const convertedServers: ExternalMCPServer[] = serverList.map((serverInfo: any) => ({
          id: serverInfo.server_id,
          name: serverInfo.name,
          url: serverInfo.url,
          status: mapBackendStatusToFrontend(serverInfo.status, serverInfo.connected),
          toolCount: 0, // Backend doesn't provide tools_count yet
          lastSeen: serverInfo.last_health_check ? new Date(serverInfo.last_health_check * 1000).toISOString() : new Date().toISOString(),
          health: {
            status: serverInfo.status,
            response_time: null,
            error_message: null,
            uptime: null
          }
        }));
        
        console.log('Converted servers:', convertedServers);
        setServers(convertedServers);
        setError(null);
      } else {
        const errorText = await response.text();
        console.error('Backend error response:', errorText);
        setError('Failed to load servers from backend');
      }
    } catch (err) {
      console.error('Error loading servers:', err);
      setError('Failed to load servers');
    } finally {
      setIsLoading(false);
    }
  };

  const getTotalToolsCount = () => {
    return servers.reduce((total, server) => total + server.toolCount, 0);
  };

  const getConnectedServersCount = () => {
    return servers.filter(server => server.status === 'connected').length;
  };

  const clearMessages = () => {
    setError(null);
    setSuccess(null);
  };

  const startHealthMonitoring = async () => {
    setIsHealthMonitoring(true);
    try {
      // Start monitoring all servers
      const healthPromises = servers.map(async (server) => {
        try {
          const response = await fetch(getApiUrl('TEST_CONNECTION'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ server_id: server.id })
          });
          
          if (response.ok) {
            const result = await response.json();
            return { serverId: server.id, status: 'success', data: result };
          } else {
            return { serverId: server.id, status: 'error', error: response.statusText };
          }
        } catch (err) {
          return { serverId: server.id, status: 'error', error: 'Connection failed' };
        }
      });

      const results = await Promise.all(healthPromises);
      const healthMap = results.reduce((acc, result) => {
        acc[result.serverId] = result;
        return acc;
      }, {} as any);
      
      setHealthData(healthMap);
      setSuccess('Health check completed for all servers');
    } catch (err) {
      setError('Failed to perform health check');
    } finally {
      setIsHealthMonitoring(false);
    }
  };

  const stopHealthMonitoring = () => {
    setIsHealthMonitoring(false);
    setHealthData({});
  };

  const handleAddServer = async (serverConfig: any) => {
    try {
      // Add server to backend
      const response = await fetch(getApiUrl('EXTERNAL_SERVERS'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: serverConfig.name,
          description: `External MCP Server: ${serverConfig.name}`,
          server_url: serverConfig.url,
          server_type: 'custom',
          authentication_type: 'NONE',
          api_key: null,
          username: null,
          password: null,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Server add result:', result);
        setSuccess(`Server "${serverConfig.name}" added successfully!`);
        
        // Reload servers to get updated data from backend
        console.log('Reloading servers after adding...');
        await loadServers();
        
        // Force a re-render by updating state
        setTimeout(() => {
          console.log('Forcing re-render...');
          setServers(prev => [...prev]);
        }, 100);
      } else {
        const errorData = await response.json();
        setError(`Failed to add server: ${errorData.detail?.message || response.statusText}`);
      }
    } catch (err) {
      console.error('Error adding server:', err);
      setError('Failed to add server');
    }
  };

  return (
    <>
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        height: '100%',
        padding: '16px'
      }}>
        <div style={{
          backgroundColor: 'var(--colorNeutralBackground1)',
          border: '1px solid var(--colorNeutralStroke1)',
          borderRadius: 'var(--borderRadiusMedium)',
          padding: '20px'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}>
              <Text size={600} weight="semibold">External MCP Servers</Text>
              <Badge appearance="filled" color="brand">{servers.length} Servers</Badge>
            </div>
            <div style={{
              display: 'flex',
              gap: '8px'
            }}>
              <Button 
                icon={<Settings24Regular />} 
                onClick={startHealthMonitoring} 
                appearance="subtle"
                disabled={isHealthMonitoring}
              >
                {isHealthMonitoring ? 'Monitoring...' : 'Health Monitor'}
              </Button>
              <Button 
                icon={<Add24Regular />} 
                onClick={() => {
                  console.log('🖱️ PARENT "Add Server" button clicked! Opening modal...');
                  setShowAddModal(true);
                }} 
                appearance="primary"
                onMouseEnter={() => console.log('🖱️ PARENT "Add Server" button mouse enter')}
              >
                Add Server
              </Button>
            </div>
          </div>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
            gap: '16px'
          }}>
            <div style={{
              textAlign: 'center',
              padding: '12px',
              backgroundColor: 'var(--colorNeutralBackground2)',
              borderRadius: 'var(--borderRadiusSmall)',
              border: '1px solid var(--colorNeutralStroke2)'
            }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{servers.length}</div>
              <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)' }}>Total Servers</div>
            </div>
            <div style={{
              textAlign: 'center',
              padding: '12px',
              backgroundColor: 'var(--colorNeutralBackground2)',
              borderRadius: 'var(--borderRadiusSmall)',
              border: '1px solid var(--colorNeutralStroke2)'
            }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{getConnectedServersCount()}</div>
              <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)' }}>Connected</div>
            </div>
            <div style={{
              textAlign: 'center',
              padding: '12px',
              backgroundColor: 'var(--colorNeutralBackground2)',
              borderRadius: 'var(--borderRadiusSmall)',
              border: '1px solid var(--colorNeutralStroke2)'
            }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{getTotalToolsCount()}</div>
              <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)' }}>Total Tools</div>
            </div>
            <div style={{
              textAlign: 'center',
              padding: '12px',
              backgroundColor: 'var(--colorNeutralBackground2)',
              borderRadius: 'var(--borderRadiusSmall)',
              border: '1px solid var(--colorNeutralStroke2)'
            }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                {servers.length > 0 ? Math.round((getConnectedServersCount() / servers.length) * 100) : 0}%
              </div>
              <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)' }}>Uptime</div>
            </div>
          </div>
        </div>

        {/* Health Monitoring Results */}
        {isHealthMonitoring && Object.keys(healthData).length > 0 && (
          <div style={{
            backgroundColor: 'var(--colorNeutralBackground1)',
            border: '1px solid var(--colorNeutralStroke1)',
            borderRadius: 'var(--borderRadiusMedium)',
            padding: '20px',
            marginBottom: '16px'
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '16px'
            }}>
              <Text size={500} weight="semibold">Health Monitoring Results</Text>
              <Button 
                appearance="outline" 
                onClick={stopHealthMonitoring}
                size="small"
              >
                Stop Monitoring
              </Button>
            </div>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '12px'
            }}>
              {servers.map(server => {
                const health = healthData[server.id];
                return (
                  <div key={server.id} style={{
                    padding: '12px',
                    backgroundColor: 'var(--colorNeutralBackground2)',
                    borderRadius: 'var(--borderRadiusSmall)',
                    border: `1px solid ${health?.status === 'success' ? 'var(--colorPaletteGreenBorder1)' : 'var(--colorPaletteRedBorder1)'}`
                  }}>
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '8px'
                    }}>
                      <Text size={300} weight="semibold">{server.name}</Text>
                      <Badge 
                        appearance="filled" 
                        color={health?.status === 'success' ? 'success' : 'danger'}
                      >
                        {health?.status || 'pending'}
                      </Badge>
                    </div>
                    
                    {health?.status === 'success' && (
                      <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground2)' }}>
                        <div>Response: {health.data?.response_time || 'N/A'}ms</div>
                        <div>Status: {health.data?.status || 'N/A'}</div>
                      </div>
                    )}
                    
                    {health?.status === 'error' && (
                      <div style={{ fontSize: '12px', color: 'var(--colorPaletteRedForeground1)' }}>
                        Error: {health.error || 'Unknown error'}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {error && (
          <div style={{
            padding: '12px 16px',
            borderRadius: 'var(--borderRadiusMedium)',
            border: '1px solid var(--colorNeutralStroke2)',
            backgroundColor: 'var(--colorNeutralBackground2)'
          }}>
            <Text color="danger">{error}</Text>
          </div>
        )}
        
        {success && (
          <div style={{
            padding: '12px 16px',
            borderRadius: 'var(--borderRadiusMedium)',
            border: '1px solid var(--colorNeutralStroke2)',
            backgroundColor: 'var(--colorNeutralBackground2)'
          }}>
            <Text color="success">{success}</Text>
          </div>
        )}

        <div style={{
          backgroundColor: 'var(--colorNeutralBackground1)',
          border: '1px solid var(--colorNeutralStroke1)',
          borderRadius: 'var(--borderRadiusMedium)',
          padding: '20px',
          flex: 1
        }}>
          <Text size={500} weight="semibold" style={{ marginBottom: '16px' }}>
            Connected Servers
          </Text>
          
          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '16px' }}>
              <Spinner size="large" label="Loading external servers..." />
            </div>
          ) : servers.length === 0 ? (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '40px 20px',
              textAlign: 'center'
            }}>
              <Info24Regular style={{
                fontSize: '48px',
                color: 'var(--colorNeutralForeground3)',
                marginBottom: '16px'
              }} />
              <Text size={500} color="neutralSecondary">
                No external MCP servers configured
              </Text>
              <Text size={300} color="neutralTertiary" style={{ marginBottom: '16px' }}>
                Add your first external MCP server to expand your tool library
              </Text>
              <Button 
                icon={<Add24Regular />} 
                onClick={() => setShowAddModal(true)}
              >
                Add Your First Server
              </Button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {servers.map(server => (
                <div key={server.id} style={{
                  backgroundColor: 'var(--colorNeutralBackground2)',
                  border: '1px solid var(--colorNeutralStroke2)',
                  borderRadius: 'var(--borderRadiusMedium)',
                  padding: '16px'
                }}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <div>
                      <Text size={500} weight="semibold">{server.name}</Text>
                      <div style={{
                        fontSize: '14px',
                        color: 'var(--colorNeutralForeground3)',
                        fontFamily: 'monospace',
                        marginTop: '4px'
                      }}>
                        {server.url}
                      </div>
                    </div>
                    <Badge 
                      appearance="filled" 
                      color={server.status === 'connected' ? 'success' : server.status === 'connecting' ? 'warning' : 'danger'}
                    >
                      {server.status}
                    </Badge>
                  </div>
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(80px, 1fr))',
                    gap: '12px',
                    marginTop: '12px'
                  }}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '16px', fontWeight: 'bold' }}>{server.toolCount}</div>
                      <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)' }}>Tools</div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                        {new Date(server.lastSeen).toLocaleDateString()}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--colorNeutralForeground3)' }}>Last Seen</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <AddServerModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onAdd={handleAddServer}
      />
    </>
  );
};
