import * as React from "react";
import { Spinner, Text, makeStyles, tokens } from "@fluentui/react-components";
import MessageBubble, { ChatMessage } from "./MessageBubble";

interface MessageListProps {
  messages: ChatMessage[];
  loading?: boolean;
  onScrollToBottom?: () => void;
}

const useStyles = makeStyles({
  container: {
    flex: 1,
    overflowY: "auto", // Enable scrolling only for messages
    padding: "0", // Remove padding since parent handles it
    display: "flex",
    flexDirection: "column",
    gap: "12px", // Standardized gap
    scrollBehavior: "smooth",
    backgroundColor: "transparent", // Let parent handle background
    // Ensure proper scroll containment
    minHeight: 0, // Allow container to shrink below content size
    height: "100%", // Take full height of parent
  },
  emptyState: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    height: "100%",
    color: tokens.colorNeutralForeground3,
    textAlign: "center",
    padding: "60px 40px",
  },
  loadingContainer: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    justifyContent: "center",
    padding: "32px",
    color: tokens.colorNeutralForeground2,
  },
  welcomeMessage: {
    textAlign: "center",
    padding: "32px 24px",
    backgroundColor: tokens.colorNeutralBackground2,
    borderRadius: tokens.borderRadiusLarge,
    border: `1px solid ${tokens.colorNeutralStroke1}`,
    marginBottom: "24px",
    boxShadow: tokens.shadow4,
    position: "relative",
    "&::before": {
      content: '""',
      position: "absolute",
      top: 0,
      left: 0,
      right: 0,
      height: "4px",
      background: `linear-gradient(90deg, ${tokens.colorBrandBackground} 0%, ${tokens.colorBrandBackground2} 100%)`,
      borderRadius: `${tokens.borderRadiusLarge} ${tokens.borderRadiusLarge} 0 0`,
    },
  },
  welcomeTitle: {
    fontSize: "20px",
    fontWeight: "700",
    marginBottom: "12px",
    color: tokens.colorNeutralForeground1,
  },
  welcomeText: {
    fontSize: "16px",
    color: tokens.colorNeutralForeground2,
    lineHeight: "1.6",
    marginBottom: "16px",
  },
  welcomeFeatures: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
    gap: "12px",
    marginTop: "16px",
  },
  featureItem: {
    fontSize: "14px",
    color: tokens.colorNeutralForeground2,
    padding: "8px 12px",
    backgroundColor: tokens.colorNeutralBackground1,
    borderRadius: tokens.borderRadiusSmall,
    border: `1px solid ${tokens.colorNeutralStroke1}`,
    textAlign: "center",
  },
  scrollToBottom: {
    position: "sticky",
    bottom: "20px",
    alignSelf: "flex-end",
    zIndex: 10,
  },
  newMessageIndicator: {
    position: "sticky",
    top: "20px",
    alignSelf: "center",
    zIndex: 10,
    padding: "8px 16px",
    backgroundColor: tokens.colorBrandBackground,
    color: tokens.colorNeutralForegroundOnBrand,
    borderRadius: tokens.borderRadiusMedium,
    fontSize: "12px",
    fontWeight: "600",
    boxShadow: tokens.shadow8,
    animation: "fadeInDown 0.3s ease-out",
  },
});

const MessageList: React.FC<MessageListProps> = ({ messages, loading = false }) => {
  const styles = useStyles();
  const containerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages]);

  // Welcome message is now handled in ChatInterface component
  const renderWelcomeMessage = () => null;

  const renderEmptyState = () => (
    <div className={styles.emptyState}>
      <Text size={400} style={{ marginBottom: "8px" }}>
        Start a conversation
      </Text>
      <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
        Type a message below to begin chatting with your AI assistant
      </Text>
    </div>
  );

  const renderLoadingIndicator = () => (
    <div className={styles.loadingContainer}>
      <Spinner size="tiny" />
      <Text size={200}>AI is thinking...</Text>
    </div>
  );

  return (
    <div className={styles.container} ref={containerRef}>
      {messages.length === 0 ? (
        renderEmptyState()
      ) : (
        <>
          {messages.map((message, index) => (
            <MessageBubble
              key={message.id}
              message={message}
              isLastMessage={index === messages.length - 1}
            />
          ))}

          {loading && renderLoadingIndicator()}
        </>
      )}
    </div>
  );
};

export default MessageList;
