import React, { useState } from 'react';
import {
  Button, Text, Input, Label, Dialog, DialogSurface, DialogTitle, DialogBody, DialogContent, DialogActions
} from '@fluentui/react-components';
import { 
  Add24Regular, Link24Regular, Server24Regular, Key24Regular
} from '@fluentui/react-icons';
import { getApiUrl } from '../../config/backend';
import { getAccessToken } from '../../../services/authTokenStore';


interface AddServerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (serverConfig: any) => Promise<void>;
}

export const AddServerModal: React.FC<AddServerModalProps> = ({
  isOpen,
  onClose,
  onAdd
}) => {
  console.log('🚀 AddServerModal component rendered! Props:', { isOpen, onClose: !!onClose, onAdd: !!onAdd });
  
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    serverType: 'custom',
    authenticationType: 'none',
    apiKey: '',
    username: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [testResult, setTestResult] = useState<{success: boolean, message: string} | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(null);
    setSuccess(null);
  };

  const validateForm = () => {
    // Name validation
    if (!formData.name.trim()) return 'Server name is required';
    if (formData.name.length < 3) return 'Server name must be at least 3 characters';
    if (formData.name.length > 50) return 'Server name must be less than 50 characters';
    
    // URL validation
    if (!formData.url.trim()) return 'Server URL is required';
    if (!formData.url.startsWith('http://') && !formData.url.startsWith('https://')) {
      return 'URL must start with http:// or https://';
    }
    
    // URL format validation
    try {
      new URL(formData.url);
    } catch {
      return 'Please enter a valid URL';
    }
    
    // Authentication validation
    if (formData.authenticationType === 'api_key' && !formData.apiKey.trim()) {
      return 'API key is required for API key authentication';
    }
    
    if (formData.authenticationType === 'basic' && (!formData.username.trim() || !formData.password.trim())) {
      return 'Username and password are required for basic authentication';
    }
    
    return null;
  };

  const testConnection = async () => {
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsTestingConnection(true);
    setTestResult(null);
    setError(null);
    setSuccess(null);

    try {
      // Test connection directly
      const token = getAccessToken();
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const response = await fetch(getApiUrl('TEST_CONNECTION'), {
        method: 'POST',
        headers,
        body: JSON.stringify({ 
          name: formData.name,
          description: `Test connection to ${formData.url}`,
          server_url: formData.url 
        }),
      });
      
      if (response.ok) {
        setTestResult({ success: true, message: `Connection successful! Server "${formData.name}" is reachable.` });
      } else {
        setTestResult({ success: false, message: `Connection failed: Server is not reachable` });
      }
    } catch (err) {
      console.error('Connection test error:', err);
      setTestResult({ success: false, message: 'Network error. Please check your connection.' });
    } finally {
      setIsTestingConnection(false);
    }
  };

  const handleSubmit = async () => {
    console.log('🖱️ Add Server button clicked!');
    console.log('📋 Current form data:', formData);
    
    const validationError = validateForm();
    if (validationError) {
      console.log('❌ Validation error:', validationError);
      setError(validationError);
      return;
    }

    console.log('✅ Form validation passed');
    setIsLoading(true);
    setError(null);

    try {
      // Pass the form data to the parent component to handle the API call
      await onAdd(formData);
      
      setSuccess('Server added successfully!');
      
      // Close modal after a short delay
      setTimeout(() => {
        onClose();
        setFormData({
          name: '',
          url: '',
          serverType: 'custom',
          authenticationType: 'none',
          apiKey: '',
          username: '',
          password: ''
        });
        setSuccess(null);
      }, 1500);
      
    } catch (err) {
      console.error('Add server error:', err);
      
      // Provide specific error messages
      let errorMessage = 'Failed to add server. Please try again.';
      
      if (err instanceof Error) {
        if (err.message.includes('400')) {
          errorMessage = 'Invalid server data. Please check your input.';
        } else if (err.message.includes('409')) {
          errorMessage = 'Server with this name already exists.';
        } else if (err.message.includes('500')) {
          errorMessage = 'Server error. Please try again later.';
        } else if (err.message.includes('Network')) {
          errorMessage = 'Network error. Please check your connection.';
        } else {
          errorMessage = err.message;
        }
      }
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      onClose();
      setFormData({
        name: '',
        url: '',
        serverType: 'custom',
        authenticationType: 'none',
        apiKey: '',
        username: '',
        password: ''
      });
      setError(null);
      setSuccess(null);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(_, data) => !data.open && handleClose()}>
      <DialogSurface>
        <DialogTitle>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Server24Regular />
            <Text weight="semibold">Add External MCP Server</Text>
          </div>
        </DialogTitle>
        
        <DialogBody>
          <DialogContent>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '16px'
            }}>
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                <Label htmlFor="server-name" weight="semibold">
                  Server Name *
                </Label>
                <Input
                  id="server-name"
                  placeholder="e.g., GitHub MCP Server"
                  value={formData.name}
                  onChange={(_, data) => handleInputChange('name', data.value)}
                  contentBefore={<Server24Regular />}
                />
              </div>

              <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                <Label htmlFor="server-url" weight="semibold">
                  Server URL *
                </Label>
                <Input
                  id="server-url"
                  placeholder="https://mcp.deepwiki.com/mcp"
                  value={formData.url}
                  onChange={(_, data) => handleInputChange('url', data.value)}
                  contentBefore={<Link24Regular />}
                />
                <Text size={200} color="neutralSecondary">
                  For DeepWiki, use: https://mcp.deepwiki.com/mcp
                </Text>
              </div>

              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '16px'
              }}>
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px'
                }}>
                  <Label htmlFor="server-type" weight="semibold">
                    Server Type
                  </Label>
                  <Input
                    id="server-type"
                    value={formData.serverType}
                    onChange={(_, data) => handleInputChange('serverType', data.value)}
                    placeholder="custom"
                  />
                </div>

                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px'
                }}>
                  <Label htmlFor="auth-type" weight="semibold">
                    Authentication
                  </Label>
                  <Input
                    id="auth-type"
                    value={formData.authenticationType}
                    onChange={(_, data) => handleInputChange('authenticationType', data.value)}
                    placeholder="none"
                  />
                </div>
              </div>

              {formData.authenticationType === 'api_key' && (
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px'
                }}>
                  <Label htmlFor="api-key" weight="semibold">
                    API Key
                  </Label>
                  <Input
                    id="api-key"
                    type="password"
                    placeholder="Enter your API key"
                    value={formData.apiKey}
                    onChange={(_, data) => handleInputChange('apiKey', data.value)}
                    contentBefore={<Key24Regular />}
                  />
                </div>
              )}

              {formData.authenticationType === 'basic' && (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '16px'
                }}>
                  <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px'
                  }}>
                    <Label htmlFor="username" weight="semibold">
                      Username
                    </Label>
                    <Input
                      id="username"
                      placeholder="Enter username"
                      value={formData.username}
                      onChange={(_, data) => handleInputChange('username', data.value)}
                    />
                  </div>
                  <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px'
                  }}>
                    <Label htmlFor="password" weight="semibold">
                      Password
                    </Label>
                    <Input
                      id="password"
                      type="password"
                      placeholder="Enter password"
                      value={formData.password}
                      onChange={(_, data) => handleInputChange('password', data.value)}
                    />
                  </div>
                </div>
              )}

              {error && <div style={{ color: 'var(--colorPaletteRedForeground1)', fontSize: '12px', marginTop: '4px' }}>{error}</div>}
              {success && <div style={{ color: 'var(--colorPaletteGreenForeground1)', fontSize: '12px', marginTop: '4px' }}>{success}</div>}
              {testResult && (
                <div style={{ 
                  color: testResult.success ? 'var(--colorPaletteGreenForeground1)' : 'var(--colorPaletteRedForeground1)', 
                  fontSize: '12px', 
                  marginTop: '4px' 
                }}>
                  {testResult.message}
                </div>
              )}
            </div>
          </DialogContent>
        </DialogBody>

        <DialogActions>
          <div style={{
            display: 'flex',
            gap: '8px',
            justifyContent: 'flex-end'
          }}>
            <Button 
              appearance="subtle" 
              onClick={handleClose}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button 
              appearance="outline" 
              onClick={testConnection}
              disabled={isLoading || isTestingConnection}
            >
              {isTestingConnection ? 'Testing...' : 'Test Connection'}
            </Button>
            <Button 
              appearance="primary" 
              onClick={() => {
                console.log('🖱️ Add Server button onClick fired!');
                handleSubmit();
              }}
              disabled={isLoading}
              icon={<Add24Regular />}
              onMouseEnter={() => console.log('🖱️ Add Server button mouse enter')}
              onMouseLeave={() => console.log('🖱️ Add Server button mouse leave')}
            >
              {isLoading ? 'Adding...' : 'Add Server'}
            </Button>
          </div>
        </DialogActions>
      </DialogSurface>
    </Dialog>
  );
};
