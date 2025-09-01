import * as React from 'react';
import { Text, Badge } from '@fluentui/react-components';
import { Bot24Regular, Person24Regular, Warning24Regular } from '@fluentui/react-icons';
import { makeStyles, tokens } from '@fluentui/react-components';

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    toolUsed?: string;
    toolResult?: any;
    error?: string;
    aiGenerated?: boolean;
    modelUsed?: string;
    executionTime?: number;
    intent_type?: string;
    routing_decision?: string;
    reasoning?: string;
    success?: boolean;
    [key: string]: any;
  };
}

interface MessageBubbleProps {
  message: ChatMessage;
  isLastMessage?: boolean;
}

const useStyles = makeStyles({
  messageBubble: {
    maxWidth: '85%',
    padding: '16px 20px',
    borderRadius: tokens.borderRadiusLarge,
    wordWrap: 'break-word',
    marginBottom: '16px',
    position: 'relative',
    transition: 'all 0.2s ease',
    '&:hover': {
      transform: 'translateY(-2px)',
      boxShadow: tokens.shadow8,
    },
  },
  userMessage: {
    backgroundColor: tokens.colorBrandBackground,
    color: tokens.colorNeutralForegroundOnBrand,
    alignSelf: 'flex-end',
    marginLeft: 'auto',
    boxShadow: tokens.shadow4,
    '&::before': {
      content: '""',
      position: 'absolute',
      right: '-8px',
      top: '16px',
      width: 0,
      height: 0,
      borderLeft: `8px solid ${tokens.colorBrandBackground}`,
      borderTop: '8px solid transparent',
      borderBottom: '8px solid transparent',
    },
  },
  assistantMessage: {
    backgroundColor: tokens.colorNeutralBackground1,
    color: tokens.colorNeutralForeground1,
    border: `1px solid ${tokens.colorNeutralStroke1}`,
    alignSelf: 'flex-start',
    boxShadow: tokens.shadow4,
    '&::before': {
      content: '""',
      position: 'absolute',
      left: '-8px',
      top: '16px',
      width: 0,
      height: 0,
      borderRight: `8px solid ${tokens.colorNeutralBackground1}`,
      borderTop: '8px solid transparent',
      borderBottom: '8px solid transparent',
    },
  },
  systemMessage: {
    backgroundColor: tokens.colorStatusWarningBackground1,
    color: tokens.colorStatusWarningForeground1,
    border: `1px solid ${tokens.colorStatusWarningBorder1}`,
    alignSelf: 'center',
    maxWidth: '70%',
    textAlign: 'center',
    boxShadow: tokens.shadow4,
  },
  messageHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '12px',
  },
  messageContent: {
    lineHeight: '1.6',
    fontSize: '14px',
  },
  timestamp: {
    fontSize: '11px',
    opacity: 0.7,
    marginTop: '8px',
    fontStyle: 'italic',
  },
  toolResult: {
    marginTop: '12px',
    padding: '12px',
    backgroundColor: tokens.colorNeutralBackground2,
    borderRadius: tokens.borderRadiusMedium,
    border: `1px solid ${tokens.colorNeutralStroke1}`,
    position: 'relative',
    '&::before': {
      content: '""',
      position: 'absolute',
      top: '-6px',
      left: '20px',
      width: 0,
      height: 0,
      borderLeft: '6px solid transparent',
      borderRight: '6px solid transparent',
      borderBottom: `6px solid ${tokens.colorNeutralBackground2}`,
    },
  },
  errorMessage: {
    color: tokens.colorStatusDangerForeground1,
    fontSize: '14px',
    padding: '8px 12px',
    backgroundColor: tokens.colorStatusDangerBackground1,
    borderRadius: tokens.borderRadiusSmall,
    border: `1px solid ${tokens.colorStatusDangerBorder1}`,
  },
  messageIcon: {
    width: '24px',
    height: '24px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '12px',
    fontWeight: '600',
  },
  userIcon: {
    backgroundColor: tokens.colorNeutralForegroundOnBrand,
    color: tokens.colorBrandBackground,
  },
  assistantIcon: {
    backgroundColor: tokens.colorBrandBackground2,
    color: tokens.colorBrandForeground1,
  },
  systemIcon: {
    backgroundColor: tokens.colorStatusWarningBackground2,
    color: tokens.colorStatusWarningForeground1,
  },
  aiMetadata: {
    marginTop: '8px',
    padding: '8px 12px',
    backgroundColor: tokens.colorStatusSuccessBackground1,
    borderRadius: tokens.borderRadiusSmall,
    border: `1px solid ${tokens.colorStatusSuccessBorder1}`,
    fontSize: '11px',
    color: tokens.colorStatusSuccessForeground1,
  },
  intentMetadata: {
    marginTop: '8px',
    padding: '8px 12px',
    backgroundColor: tokens.colorBrandBackground2,
    borderRadius: tokens.borderRadiusSmall,
    border: `1px solid ${tokens.colorBrandStroke1}`,
    fontSize: '11px',
    color: tokens.colorBrandForeground1,
  },
  metadataGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
    gap: '8px',
    marginTop: '8px',
  },
  metadataItem: {
    fontSize: '11px',
    color: tokens.colorNeutralForeground3,
  },
});

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const styles = useStyles();

  const getMessageStyle = () => {
    switch (message.type) {
      case 'user':
        return `${styles.messageBubble} ${styles.userMessage}`;
      case 'assistant':
        return `${styles.messageBubble} ${styles.assistantMessage}`;
      case 'system':
        return `${styles.messageBubble} ${styles.systemMessage}`;
      default:
        return `${styles.messageBubble} ${styles.assistantMessage}`;
    }
  };

  const getMessageIcon = () => {
    switch (message.type) {
      case 'user':
        return 'U';
      case 'assistant':
        return 'A';
      case 'system':
        return 'S';
      default:
        return 'A';
    }
  };

  const getMessageIconStyle = () => {
    switch (message.type) {
      case 'user':
        return `${styles.messageIcon} ${styles.userIcon}`;
      case 'assistant':
        return `${styles.messageIcon} ${styles.assistantIcon}`;
      case 'system':
        return `${styles.messageIcon} ${styles.systemIcon}`;
      default:
        return `${styles.messageIcon} ${styles.assistantIcon}`;
    }
  };

  const getMessageLabel = () => {
    switch (message.type) {
      case 'user':
        return 'You';
      case 'assistant':
        return 'AI Assistant';
      case 'system':
        return 'System';
      default:
        return 'Unknown';
    }
  };

  const formatContent = (content: any) => {
    // Ensure content is a string
    if (typeof content !== 'string') {
      console.warn('MessageBubble: content is not a string:', content);
      content = String(content || '');
    }
    
    return content
      .split('\n')
      .map((line, index) => (
        <React.Fragment key={index}>
          {line}
          {index < content.split('\n').length - 1 && <br />}
        </React.Fragment>
      ));
  };

  const renderAIMetadata = () => {
    if (!message.metadata?.aiGenerated) return null;

    return (
      <div className={styles.aiMetadata}>
        <div style={{ fontWeight: '600', marginBottom: '4px' }}>🤖 AI Generated Response</div>
        <div className={styles.metadataGrid}>
          {message.metadata.modelUsed && (
            <div className={styles.metadataItem}>
              <strong>Model:</strong> {message.metadata.modelUsed}
            </div>
          )}
          {message.metadata.executionTime && (
            <div className={styles.metadataItem}>
              <strong>Time:</strong> {(message.metadata.executionTime * 1000).toFixed(0)}ms
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderIntentMetadata = () => {
    if (!message.metadata?.intent_type) return null;

    return (
      <div className={styles.intentMetadata}>
        <div style={{ fontWeight: '600', marginBottom: '4px' }}>🧠 Intent Analysis</div>
        <div className={styles.metadataGrid}>
          <div className={styles.metadataItem}>
            <strong>Intent:</strong> {message.metadata.intent_type}
          </div>
          <div className={styles.metadataItem}>
            <strong>Routing:</strong> {message.metadata.routing_decision}
          </div>
          {message.metadata.reasoning && (
            <div className={styles.metadataItem} style={{ gridColumn: '1 / -1' }}>
              <strong>Reasoning:</strong> {message.metadata.reasoning}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className={getMessageStyle()}>
      <div className={styles.messageHeader}>
        <div className={getMessageIconStyle()}>
          {getMessageIcon()}
        </div>
        <Text size={200} style={{ fontWeight: '500' }}>
          {getMessageLabel()}
        </Text>
        {message.metadata?.toolUsed && (
          <Badge appearance="tint" size="small">
            {message.metadata.toolUsed}
          </Badge>
        )}
        {message.metadata?.aiGenerated && (
          <Badge appearance="filled" size="small" style={{ backgroundColor: tokens.colorStatusSuccessBackground1 }}>
            AI
          </Badge>
        )}
      </div>
      
      <div className={styles.messageContent}>
        {formatContent(message.content)}
      </div>

      {/* AI Metadata */}
      {renderAIMetadata()}

      {/* Intent Metadata */}
      {renderIntentMetadata()}

      {message.metadata?.toolResult && (
        <div className={styles.toolResult}>
          <Text size={200} style={{ fontWeight: '600', marginBottom: '4px' }}>
            Tool Result:
          </Text>
          <Text size={200}>
            {typeof message.metadata.toolResult === 'string' 
              ? message.metadata.toolResult 
              : JSON.stringify(message.metadata.toolResult, null, 2)
            }
          </Text>
        </div>
      )}

      {message.metadata?.error && (
        <div className={styles.errorMessage}>
          <Text size={200}>
            Error: {message.metadata.error}
          </Text>
        </div>
      )}

      <div className={styles.timestamp}>
        <Text size={100}>
          {message.timestamp.toLocaleTimeString()}
        </Text>
      </div>
    </div>
  );
};

export default MessageBubble;
