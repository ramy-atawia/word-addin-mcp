/**
 * Shared utility functions for status mapping and common operations
 */

// Helper function to map backend status to frontend status
export const mapBackendStatusToFrontend = (backendStatus: string, connected: boolean): 'connected' | 'disconnected' | 'connecting' | 'error' => {
  if (connected) return 'connected';
  if (backendStatus === 'degraded') return 'connecting';
  if (backendStatus === 'failed' || backendStatus === 'unhealthy') return 'error';
  return 'disconnected';
};

// Helper function to get status color for UI components
export const getStatusColor = (status: string, connected: boolean): 'success' | 'warning' | 'danger' => {
  if (connected) return 'success';
  if (status === 'connecting' || status === 'degraded') return 'warning';
  return 'danger';
};

// Helper function to get status text for UI components
export const getStatusText = (status: string, connected: boolean): string => {
  if (connected) return 'Connected';
  if (status === 'connecting') return 'Connecting';
  if (status === 'degraded') return 'Degraded';
  return 'Disconnected';
};
