import React, { Component, ErrorInfo, ReactNode } from 'react';
import { makeStyles, tokens } from '@fluentui/react-components';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

const useStyles = makeStyles({
  errorContainer: {
    padding: '20px',
    backgroundColor: '#fef2f2',
    border: '1px solid #fecaca',
    borderRadius: '8px',
    margin: '10px',
    color: '#dc2626',
  },
  errorTitle: {
    fontSize: '18px',
    fontWeight: '600',
    marginBottom: '8px',
  },
  errorMessage: {
    fontSize: '14px',
    marginBottom: '16px',
    lineHeight: '1.5',
  },
  retryButton: {
    background: '#dc2626',
    color: 'white',
    border: 'none',
    padding: '8px 16px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500',
    transition: 'background-color 0.2s ease',
    '&:hover': {
      backgroundColor: '#b91c1c',
    },
  },
});

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || <ErrorFallback onRetry={() => this.setState({ hasError: false, error: undefined })} />;
    }

    return this.props.children;
  }
}

const ErrorFallback: React.FC<{ onRetry: () => void }> = ({ onRetry }) => {
  const styles = useStyles();
  
  return (
    <div className={styles.errorContainer}>
      <div className={styles.errorTitle}>Something went wrong</div>
      <div className={styles.errorMessage}>
        An error occurred while processing your request. Please try again.
      </div>
      <button
        onClick={onRetry}
        className={styles.retryButton}
      >
        Try Again
      </button>
    </div>
  );
};

export default ErrorBoundary;
