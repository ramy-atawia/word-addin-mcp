import React, { useState } from 'react';
import { 
  Text, 
  Button, 
  Badge,
  tokens 
} from '@fluentui/react-components';
import { 
  ChevronDown24Regular,
  ChevronRight24Regular,
  Server24Regular,
  Toolbox24Regular
} from '@fluentui/react-icons';
import { getStatusColor, getStatusText } from '../../utils/statusUtils';

interface ServerToolsListProps {
  server: {
    id: string;
    name: string;
    url: string;
    status: string;
    connected: boolean;
    toolCount: number;
  };
  tools: any[];
  isLast: boolean;
}

const ServerToolsList: React.FC<ServerToolsListProps> = ({ server, tools, isLast }) => {
  const [isExpanded, setIsExpanded] = useState(false);



  return (
    <div style={{
      borderBottom: isLast ? 'none' : `1px solid ${tokens.colorNeutralStroke1}`
    }}>
      {/* Server Header */}
      <div 
        style={{
          padding: '16px 20px',
          cursor: 'pointer',
          backgroundColor: isExpanded ? tokens.colorNeutralBackground1 : 'transparent',
          transition: 'background-color 0.2s ease',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          flex: 1
        }}>
          <Server24Regular />
          <div style={{ flex: 1 }}>
            <Text size={400} style={{ fontWeight: '600', marginBottom: '2px' }}>
              {server.name}
            </Text>
            <Text size={200} style={{ color: tokens.colorNeutralForeground2 }}>
              {server.url}
            </Text>
          </div>
        </div>
        
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <Badge 
            appearance="filled" 
            color={getStatusColor(server.status, server.connected)}
          >
            {getStatusText(server.status, server.connected)}
          </Badge>
          
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            color: tokens.colorNeutralForeground2
          }}>
            <Toolbox24Regular />
            <Text size={200}>{tools.length}</Text>
          </div>
          
          {isExpanded ? <ChevronDown24Regular /> : <ChevronRight24Regular />}
        </div>
      </div>

      {/* Tools List */}
      {isExpanded && (
        <div style={{
          backgroundColor: tokens.colorNeutralBackground1,
          borderTop: `1px solid ${tokens.colorNeutralStroke1}`,
          padding: '16px 20px 16px 52px'
        }}>
          {tools.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: '20px',
              color: tokens.colorNeutralForeground3
            }}>
              <Text size={200}>No tools discovered from this server</Text>
            </div>
          ) : (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '12px'
            }}>
              {tools.map((tool, index) => (
                <div 
                  key={index}
                  style={{
                    padding: '12px',
                    backgroundColor: tokens.colorNeutralBackground2,
                    borderRadius: tokens.borderRadiusSmall,
                    border: `1px solid ${tokens.colorNeutralStroke1}`,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = tokens.colorNeutralBackground3;
                    e.currentTarget.style.borderColor = tokens.colorNeutralStroke2;
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = tokens.colorNeutralBackground2;
                    e.currentTarget.style.borderColor = tokens.colorNeutralStroke1;
                  }}
                >
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    marginBottom: '8px'
                  }}>
                    <Toolbox24Regular />
                    <Text size={300} style={{ fontWeight: '600' }}>
                      {tool.name}
                    </Text>
                  </div>
                  
                  <Text size={200} style={{ 
                    color: tokens.colorNeutralForeground2,
                    lineHeight: '1.4'
                  }}>
                    {tool.description}
                  </Text>
                  
                  {tool.source && (
                    <div style={{
                      marginTop: '8px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}>
                      <Badge appearance="tint" size="small">
                        {tool.source}
                      </Badge>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ServerToolsList;
