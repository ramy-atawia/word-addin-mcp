import * as React from 'react';
import { Button, Textarea, Label, makeStyles, tokens } from '@fluentui/react-components';
import { Send24Regular, Attach24Regular } from '@fluentui/react-icons';

interface MessageInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: (content: string) => void;
  onAttach?: () => void;
  disabled?: boolean;
  loading?: boolean;
  placeholder?: string;
}

const useStyles = makeStyles({
  container: {
    padding: '4px 8px', // Ultra-minimal padding to maximize input width
    borderTop: `1px solid ${tokens.colorNeutralStroke1}`,
    backgroundColor: tokens.colorNeutralBackground1,
    // Responsive design
    '@media (min-width: 768px)': {
      padding: '6px 12px',
    },
  },
  inputRow: {
    display: 'flex',
    gap: '2px', // Ultra-minimal gap to maximize text input width
    alignItems: 'flex-end',
  },
  inputField: {
    flex: 1,
    marginBottom: '0',
    width: '100%', // Ensure full width
    minWidth: '0', // Allow shrinking below content size
  },
  buttonGroup: {
    display: 'flex',
    gap: '1px', // Ultra-minimal gap between buttons
  },
  sendButton: {
    minWidth: '24px', // Tiny button
    height: '16px', // Very small height
    fontSize: '8px', // Tiny font
    padding: '0 2px', // Minimal padding
    // Responsive design
    '@media (min-width: 768px)': {
      minWidth: '28px',
      height: '18px',
      fontSize: '9px',
    },
  },
  attachButton: {
    minWidth: '16px', // Tiny attach button
    height: '16px', // Very small height
    fontSize: '8px', // Tiny font
    padding: '0 1px', // Minimal padding
    // Responsive design
    '@media (min-width: 768px)': {
      minWidth: '18px',
      height: '18px',
      fontSize: '9px',
    },
  },
  textarea: {
    resize: 'none',
    fontFamily: 'inherit',
  },
  helpText: {
    fontSize: '11px', // Reduced from 12px
    color: tokens.colorNeutralForeground3,
    marginTop: '2px', // Reduced from 8px to 2px
    textAlign: 'center',
  },
});

const MessageInput: React.FC<MessageInputProps> = ({
  value,
  onChange,
  onSend,
  onAttach,
  disabled = false,
  loading = false,
  placeholder = "Type your message here..."
}) => {
  const styles = useStyles();

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend(value);
    }
  };

  const handleSend = () => {
    if (value.trim() && !disabled && !loading) {
      onSend(value);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.inputRow}>
        <div className={styles.inputField}>
          <Label htmlFor="chat-input">Message</Label>
          <Textarea
            id="chat-input"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            rows={2}
            onKeyPress={handleKeyPress}
            disabled={disabled}
            className={styles.textarea}
          />
        </div>
        
        <div className={styles.buttonGroup}>
          {onAttach && (
            <Button
              appearance="outline"
              icon={<Attach24Regular />}
              onClick={onAttach}
              disabled={disabled}
              className={styles.attachButton}
              title="Attach file or document"
            />
          )}
          
          <Button
            appearance="primary"
            icon={<Send24Regular />}
            onClick={handleSend}
            disabled={!value.trim() || disabled || loading}
            className={styles.sendButton}
          >
            {loading ? 'Sending...' : 'Send'}
          </Button>
        </div>
      </div>
      
      <div className={styles.helpText}>
        Press Enter to send, Shift+Enter for new line
      </div>
    </div>
  );
};

export default MessageInput;
