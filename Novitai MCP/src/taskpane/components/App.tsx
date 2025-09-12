import React from 'react';
import { AuthProvider } from '../../contexts/AuthContext';
import MCPToolManager from './MCPToolManager';

const App: React.FC = () => {
  return (
    <AuthProvider>
      <MCPToolManager />
    </AuthProvider>
  );
};

export default App;
