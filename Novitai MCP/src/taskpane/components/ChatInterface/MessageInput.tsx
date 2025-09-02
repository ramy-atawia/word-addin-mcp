import * as React from 'react';
import { Button, Textarea, makeStyles, tokens } from '@fluentui/react-components';
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
    padding: '12px 0px', // Zero horizontal padding to fill entire width
    borderTop: `1px solid ${tokens.colorNeutralStroke1}`,
    backgroundColor: tokens.colorNeutralBackground1,
    borderRadius: '0 0 8px 8px', // Rounded bottom corners
    // Responsive design
    '@media (min-width: 768px)': {
      padding: '16px 0px',
    },
  },
  inputRow: {
    display: 'flex',
    flexDirection: 'column', // Vertical stack
    gap: '8px', // Better spacing between elements
    alignItems: 'stretch', // Stretch to full width
  },
  inputField: {
    flex: 1,
    marginBottom: '0',
    width: '100%',
    minWidth: '0', // Allow shrinking below content size
    maxWidth: '100%', // Override any max-width constraints
    boxSizing: 'border-box', // Include padding in width calculation
  },
  buttonGroup: {
    display: 'flex',
    gap: '8px', // Space between buttons
    alignItems: 'center',
    justifyContent: 'flex-end', // Align buttons to the right
    flexShrink: 0, // Prevent shrinking
  },
  sendButton: {
    minWidth: '60px', // Compact for vertical layout
    height: '36px', // Standard height
    borderRadius: '18px', // Pill shape
    padding: '0 16px',
    fontSize: '14px',
    fontWeight: '600',
    transition: 'all 0.2s ease',
    '&:hover': {
      transform: 'scale(1.02)',
    },
    '&:active': {
      transform: 'scale(0.98)',
    },
    // Responsive design
    '@media (min-width: 768px)': {
      minWidth: '70px',
      height: '40px',
      fontSize: '15px',
      borderRadius: '20px',
    },
  },
  attachButton: {
    minWidth: '36px', // Compact for vertical layout
    height: '36px', // Match send button height
    borderRadius: '50%', // Circular for contrast
    padding: '0',
    fontSize: '14px',
    opacity: 0.8,
    transition: 'all 0.2s ease',
    '&:hover': {
      opacity: 1,
      backgroundColor: tokens.colorNeutralBackground1Hover,
      transform: 'scale(1.05)',
    },
    '&:active': {
      transform: 'scale(0.95)',
    },
    // Responsive design
    '@media (min-width: 768px)': {
      minWidth: '40px',
      height: '40px',
      fontSize: '16px',
    },
  },
  textarea: {
    resize: 'vertical', // Allow vertical resize
    fontFamily: 'inherit',
    minHeight: '40px',
    maxHeight: '120px', // Prevent excessive growth
    borderRadius: '6px',
    border: `1px solid ${tokens.colorNeutralStroke1}`,
    fontSize: '14px',
    lineHeight: '1.4',
    padding: '8px 12px',
    transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
    width: '100%', // Force full width
    maxWidth: '100%', // Override any max-width constraints
    boxSizing: 'border-box', // Include padding in width calculation
  },
  helpText: {
    fontSize: '12px',
    color: tokens.colorNeutralForeground3,
    marginTop: '6px',
    textAlign: 'left', // Left align for better readability
    lineHeight: '1.3',
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
        Press Enter to send • Shift+Enter for new line • Attach files for analysis
      </div>
    </div>
  );
};

export default MessageInput;
