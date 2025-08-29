import * as React from 'react';
import { useState, useEffect } from 'react';
import { 
  Button, 
  Field, 
  Textarea, 
  Select, 
  TabList, 
  Tab, 
  makeStyles,
  tokens,
  Spinner,
  MessageBar,
  Card,
  CardHeader,
  CardPreview,
  Text,
  Badge
} from '@fluentui/react-components';
import { 
  Search24Regular, 
  DocumentText24Regular, 
  Globe24Regular,
  Play24Regular,
  Checkmark24Regular,
  ErrorCircle24Regular
} from '@fluentui/react-icons';
import MCPService, { MCPTool, MCPToolExecutionRequest, MCPToolExecutionResult, MCPConnectionStatus } from '../services/mcpService';

const useStyles = makeStyles({
  root: {
    padding: '20px',
    maxWidth: '100%',
    minHeight: '100vh',
  },
  header: {
    marginBottom: '20px',
    textAlign: 'center',
  },
  connectionStatus: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '20px',
    justifyContent: 'center',
  },
  tabContainer: {
    marginBottom: '20px',
  },
  toolCard: {
    marginBottom: '16px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    '&:hover': {
      transform: 'translateY(-2px)',
      boxShadow: tokens.shadow16,
    },
  },
  toolExecution: {
    padding: '20px',
    border: `1px solid ${tokens.colorNeutralStroke1}`,
    borderRadius: tokens.borderRadiusMedium,
    marginTop: '20px',
  },
  inputField: {
    marginBottom: '16px',
  },
  buttonGroup: {
    display: 'flex',
    gap: '12px',
    marginTop: '16px',
  },
  resultContainer: {
    marginTop: '20px',
    padding: '16px',
    backgroundColor: tokens.colorNeutralBackground2,
    borderRadius: tokens.borderRadiusMedium,
    border: `1px solid ${tokens.colorNeutralStroke1}`,
  },
  loadingContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '40px',
  },
  errorContainer: {
    marginTop: '16px',
  },
  successBadge: {
    backgroundColor: tokens.colorStatusSuccessBackground1,
    color: tokens.colorStatusSuccessForeground1,
  },
  errorBadge: {
    backgroundColor: tokens.colorStatusDangerBackground1,
    color: tokens.colorStatusDangerForeground1,
  },
});

type TabValue = 'tools' | 'execution' | 'history' | 'settings';

const MCPToolManager: React.FC = () => {
  const styles = useStyles();
  const [selectedTab, setSelectedTab] = useState<TabValue>('tools');
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);
  const [loading, setLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<MCPConnectionStatus | null>(null);
  const [executionHistory, setExecutionHistory] = useState<Array<{
    tool: string;
    parameters: any;
    result: MCPToolExecutionResult;
    timestamp: Date;
  }>>([]);
  const [currentExecution, setCurrentExecution] = useState<{
    tool: string;
    parameters: any;
    result: MCPToolExecutionResult | null;
  } | null>(null);

  const mcpService = new MCPService();

  useEffect(() => {
    checkConnection();
    loadTools();
  }, []);

  const checkConnection = async () => {
    const status = await mcpService.testConnection();
    setConnectionStatus(status);
  };

  const loadTools = async () => {
    setLoading(true);
    try {
      console.log('Loading MCP tools...');
      const availableTools = await mcpService.getAvailableTools();
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
    setSelectedTab('execution');
    setCurrentExecution({
      tool: tool.name,
      parameters: {},
      result: null
    });
  };

  const handleExecuteTool = async () => {
    if (!currentExecution || !selectedTool) return;

    setLoading(true);
    try {
      const result = await mcpService.executeTool({
        tool_name: selectedTool.name,
        parameters: currentExecution.parameters
      });

      const newExecution = {
        ...currentExecution,
        result,
        timestamp: new Date()
      };

      setCurrentExecution(newExecution);
      setExecutionHistory(prev => [newExecution, ...prev]);

      // If successful and result contains text, insert into Word document
      if (result.success && result.data && typeof result.data === 'string') {
        await mcpService.insertText(`\n\n--- ${selectedTool.name} Result ---\n${result.data}`);
      }
    } catch (error) {
      console.error('Error executing tool:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleParameterChange = (key: string, value: any) => {
    if (!currentExecution) return;
    
    setCurrentExecution(prev => prev ? {
      ...prev,
      parameters: {
        ...prev.parameters,
        [key]: value
      }
    } : null);
  };

  const renderToolCard = (tool: MCPTool) => (
    <Card 
      key={tool.name} 
      className={styles.toolCard}
      onClick={() => handleToolSelect(tool)}
    >
      <CardHeader
        header={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {tool.name === 'web_content_fetcher' && <Globe24Regular />}
            {tool.name === 'text_processor' && <DocumentText24Regular />}
            {tool.name === 'web_search' && <Search24Regular />}
            <Text>{tool.name}</Text>
          </div>
        }
        description={tool.description}
      />
    </Card>
  );

  const renderExecutionTab = () => (
    <div>
      {selectedTool ? (
        <div className={styles.toolExecution}>
          <h3>Execute: {selectedTool.name}</h3>
          <p>{selectedTool.description}</p>
          
          {selectedTool.parameters && Object.keys(selectedTool.parameters).length > 0 ? (
            <div>
              {Object.entries(selectedTool.parameters).map(([key, param]: [string, any]) => (
                <Field key={key} label={key} className={styles.inputField}>
                  {param.type === 'string' ? (
                    <Textarea
                      value={currentExecution?.parameters[key] || ''}
                      onChange={(e) => handleParameterChange(key, e.target.value)}
                      placeholder={`Enter ${key}`}
                    />
                  ) : (
                    <Select
                      value={currentExecution?.parameters[key] || ''}
                      onChange={(_, data) => handleParameterChange(key, data.value)}
                    >
                      {param.enum?.map((option: string) => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </Select>
                  )}
                </Field>
              ))}
            </div>
          ) : (
            <p>No parameters required for this tool.</p>
          )}

          <div className={styles.buttonGroup}>
            <Button 
              appearance="primary" 
              icon={<Play24Regular />}
              onClick={handleExecuteTool}
              disabled={loading}
            >
              Execute Tool
            </Button>
            <Button 
              appearance="secondary"
              onClick={() => setSelectedTab('tools')}
            >
              Back to Tools
            </Button>
          </div>

          {currentExecution?.result && (
            <div className={styles.resultContainer}>
              <h4>Execution Result:</h4>
              <Badge 
                appearance={currentExecution.result.success ? 'filled' : 'tint'}
                className={currentExecution.result.success ? styles.successBadge : styles.errorBadge}
              >
                {currentExecution.result.success ? 'Success' : 'Failed'}
              </Badge>
              
              {currentExecution.result.data && (
                <div style={{ marginTop: '12px' }}>
                  <Text>Data:</Text>
                  <pre style={{ 
                    whiteSpace: 'pre-wrap', 
                    backgroundColor: tokens.colorNeutralBackground1,
                    padding: '8px',
                    borderRadius: tokens.borderRadiusSmall,
                    marginTop: '8px'
                  }}>
                    {typeof currentExecution.result.data === 'string' 
                      ? currentExecution.result.data 
                      : JSON.stringify(currentExecution.result.data, null, 2)
                    }
                  </pre>
                </div>
              )}
              
              {currentExecution.result.error && (
                <div className={styles.errorContainer}>
                  <Text>Error:</Text>
                  <Text>{currentExecution.result.error}</Text>
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Text>Select a tool from the Tools tab to execute it.</Text>
        </div>
      )}
    </div>
  );

  const renderHistoryTab = () => (
    <div>
      <h3>Execution History</h3>
      {executionHistory.length === 0 ? (
        <p>No executions yet. Execute a tool to see history.</p>
      ) : (
        executionHistory.map((execution, index) => (
          <Card key={index} className={styles.toolCard}>
            <CardHeader
              header={
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Text>{execution.tool}</Text>
                  <Badge 
                    appearance={execution.result.success ? 'filled' : 'tint'}
                    className={execution.result.success ? styles.successBadge : styles.errorBadge}
                  >
                    {execution.result.success ? 'Success' : 'Failed'}
                  </Badge>
                </div>
              }
              description={execution.timestamp.toLocaleString()}
            />
            <CardPreview>
              <div style={{ padding: '12px' }}>
                <Text>
                  Parameters: {JSON.stringify(execution.parameters)}
                </Text>
                {execution.result.data && (
                  <div style={{ marginTop: '8px' }}>
                    <Text>Result:</Text>
                    <Text>
                      {typeof execution.result.data === 'string' 
                        ? execution.result.data.substring(0, 100) + '...'
                        : JSON.stringify(execution.result.data).substring(0, 100) + '...'
                      }
                    </Text>
                  </div>
                )}
              </div>
            </CardPreview>
          </Card>
        ))
      )}
    </div>
  );

  const renderSettingsTab = () => (
    <div>
      <h3>Settings</h3>
      <div className={styles.connectionStatus}>
        <Text>MCP Server Status:</Text>
        {connectionStatus ? (
          <>
            {connectionStatus.connected ? (
              <Checkmark24Regular style={{ color: tokens.colorStatusSuccessForeground1 }} />
            ) : (
              <ErrorCircle24Regular style={{ color: tokens.colorStatusDangerForeground1 }} />
            )}
            <Text>{connectionStatus.connected ? 'Connected' : 'Disconnected'}</Text>
            <Text>({connectionStatus.server_url})</Text>
          </>
        ) : (
          <Spinner size="tiny" />
        )}
      </div>
      
      <Button 
        appearance="secondary" 
        onClick={checkConnection}
        disabled={loading}
      >
        Test Connection
      </Button>
      
      <div style={{ marginTop: '20px' }}>
        <Text>Configuration:</Text>
        <pre style={{ 
          backgroundColor: tokens.colorNeutralBackground1,
          padding: '8px',
          borderRadius: tokens.borderRadiusSmall,
          marginTop: '8px'
        }}>
          {JSON.stringify(mcpService.getConfiguration(), null, 2)}
        </pre>
      </div>
    </div>
  );

  if (loading && !tools.length) {
    return (
      <div className={styles.loadingContainer}>
        <Spinner size="large" label="Loading MCP tools..." />
      </div>
    );
  }

  return (
    <div className={styles.root}>
      <div className={styles.header}>
        <h2>Novitai MCP - Word Add-in</h2>
        <p>AI-powered document processing and research tools</p>
      </div>

      <div className={styles.connectionStatus}>
        {connectionStatus && (
          <>
            {connectionStatus.connected ? (
              <Checkmark24Regular style={{ color: tokens.colorStatusSuccessForeground1 }} />
            ) : (
              <ErrorCircle24Regular style={{ color: tokens.colorStatusDangerForeground1 }} />
            )}
            <Text>
              {connectionStatus.connected ? 'Connected to MCP Server' : 'Disconnected from MCP Server'}
            </Text>
          </>
        )}
      </div>

      <div className={styles.tabContainer}>
        <TabList selectedValue={selectedTab} onTabSelect={(_, data) => setSelectedTab(data.value as TabValue)}>
          <Tab value="tools">Available Tools</Tab>
          <Tab value="execution">Execute Tool</Tab>
          <Tab value="history">History</Tab>
          <Tab value="settings">Settings</Tab>
        </TabList>
      </div>

      {selectedTab === 'tools' && (
        <div>
          <h3>Available MCP Tools</h3>
          {tools.length === 0 ? (
            <MessageBar intent="warning">
              No MCP tools available. Please check your connection to the MCP server.
            </MessageBar>
          ) : (
            tools.map(renderToolCard)
          )}
        </div>
      )}

      {selectedTab === 'execution' && renderExecutionTab()}
      {selectedTab === 'history' && renderHistoryTab()}
      {selectedTab === 'settings' && renderSettingsTab()}
    </div>
  );
};

export default MCPToolManager;
