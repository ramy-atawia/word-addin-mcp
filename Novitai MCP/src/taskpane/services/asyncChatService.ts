/**
 * Async Chat Service
 * Handles asynchronous chat requests using job-based processing
 */

import { getAccessToken } from '../../services/authTokenStore';

export interface AsyncJobResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  estimated_duration?: number;
  error?: string;
}

export interface JobResult {
  job_id: string;
  status: string;
  response?: string;
  intent_type?: string;
  tool_name?: string;
  execution_time?: number;
  success?: boolean;
  error?: string;
  workflow_metadata?: any;
  completed_at?: string;
}

export interface AsyncChatCallbacks {
  onProgress: (status: JobStatus) => void;
  onComplete: (result: JobResult) => void;
  onError: (error: Error) => void;
}

export class AsyncChatService {
  private baseURL: string;
  private basePollingInterval: number = 500; // 500ms base for faster initial response
  private maxPollingInterval: number = 5000; // 5 seconds max
  private minPollingInterval: number = 200; // 200ms minimum for active processing
  private maxPollingAttempts: number = 600; // 10 minutes max (600 * 500ms avg)
  private backoffMultiplier: number = 1.3; // Gentler exponential backoff
  private activePollingTimeouts: Set<NodeJS.Timeout> = new Set();
  
  // Polling strategy configuration
  private pollingStrategies = {
    // Fast polling for active processing
    active: { interval: 200, maxInterval: 1000 },
    // Medium polling for pending jobs
    pending: { interval: 1000, maxInterval: 3000 },
    // Slow polling for long-running jobs
    longRunning: { interval: 2000, maxInterval: 5000 },
    // Error recovery polling
    error: { interval: 2000, maxInterval: 5000 }
  };
  private isDestroyed: boolean = false;

  constructor() {
    this.baseURL = (window as any).BACKEND_URL || 'http://localhost:9000';
  }

  setBaseUrl(url: string) {
    this.baseURL = url;
  }

  getBaseUrl(): string {
    return this.baseURL;
  }

  /**
   * Submit a document modification request for asynchronous processing
   */
  async submitDocumentModificationRequest(params: {
    user_request: string;
    paragraphs: Array<{
      index: number;
      text: string;
      formatting?: any;
    }>;
    sessionId: string;
  }): Promise<AsyncJobResponse> {
    try {
      const token = getAccessToken();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${this.baseURL}/api/v1/async/chat/submit`, {
        method: 'POST',
        headers,
        body: JSON.stringify(params)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const result: AsyncJobResponse = await response.json();
      return result;
    } catch (error) {
      console.error('Failed to submit document modification request:', error);
      throw error;
    }
  }

  /**
   * Submit a chat request for asynchronous processing
   */
  async submitChatRequest(params: {
    message: string;
    context: {
      document_content: string;
      chat_history: string;
      available_tools: string;
    };
    sessionId: string;
  }): Promise<AsyncJobResponse> {
    try {
      const token = getAccessToken();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${this.baseURL}/api/v1/async/chat/submit`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message: params.message,
          context: {
            document_content: params.context.document_content,
            chat_history: params.context.chat_history,
            available_tools: params.context.available_tools
          }
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to submit async chat request:', error);
      throw error;
    }
  }

  /**
   * Get job status
   */
  async getJobStatus(jobId: string): Promise<JobStatus> {
    try {
      const token = getAccessToken();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${this.baseURL}/api/v1/async/chat/status/${jobId}`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get job status:', error);
      throw error;
    }
  }

  /**
   * Get job result
   */
  async getJobResult(jobId: string): Promise<JobResult> {
    try {
      const token = getAccessToken();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${this.baseURL}/api/v1/async/chat/result/${jobId}`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get job result:', error);
      throw error;
    }
  }

  /**
   * Cancel a job
   */
  async cancelJob(jobId: string): Promise<void> {
    try {
      const token = getAccessToken();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${this.baseURL}/api/v1/async/chat/cancel/${jobId}`, {
        method: 'DELETE',
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Failed to cancel job:', error);
      throw error;
    }
  }

  /**
   * Poll for job completion with optimized adaptive polling strategy
   */
  async pollJobCompletion(
    jobId: string,
    callbacks: AsyncChatCallbacks
  ): Promise<void> {
    let attempts = 0;
    let currentInterval = this.basePollingInterval;
    let consecutiveErrors = 0;
    let lastProgress = 0;
    let lastStatus = 'pending';
    let jobStartTime = Date.now();
    const maxConsecutiveErrors = 3;

    const poll = async () => {
      // Check if service is destroyed before each poll
      if (this.isDestroyed) {
        console.log('AsyncChatService: Polling stopped - service destroyed');
        return;
      }

      try {
        attempts++;
        
        if (attempts > this.maxPollingAttempts) {
          throw new Error('Job polling timeout - maximum attempts reached');
        }

        const status = await this.getJobStatus(jobId);
        callbacks.onProgress(status);

        // Reset error count on successful poll
        consecutiveErrors = 0;

        if (status.status === 'completed') {
          const result = await this.getJobResult(jobId);
          callbacks.onComplete(result);
          return;
        }

        if (status.status === 'failed') {
          throw new Error(status.error || 'Job failed');
        }

        if (status.status === 'cancelled') {
          console.log('Job cancelled detected in polling', jobId);
          throw new Error('Job was cancelled');
        }

        // Smart polling strategy based on job state and progress
        const elapsedTime = Date.now() - jobStartTime;
        const progressDelta = status.progress - lastProgress;
        const statusChanged = status.status !== lastStatus;

        // Determine polling strategy
        let strategy = 'pending';
        
        if (status.status === 'processing' && status.progress > 0) {
          // Job is actively processing with progress
          if (progressDelta > 0 || statusChanged) {
            strategy = 'active'; // Fast polling for active progress
          } else if (elapsedTime > 30000) { // 30 seconds
            strategy = 'longRunning'; // Slower polling for long jobs
          } else {
            strategy = 'active';
          }
        } else if (status.status === 'processing' && elapsedTime > 10000) {
          // Processing but no progress for 10+ seconds
          strategy = 'longRunning';
        } else if (status.status === 'pending') {
          strategy = 'pending';
        }

        // Calculate next interval based on strategy
        const strategyConfig = this.pollingStrategies[strategy as keyof typeof this.pollingStrategies];
        let nextInterval = strategyConfig.interval;

        // Apply adaptive adjustments
        if (strategy === 'active' && progressDelta > 0) {
          // Very fast polling when making progress
          nextInterval = this.minPollingInterval;
        } else if (strategy === 'pending') {
          // Exponential backoff for pending jobs
          nextInterval = Math.min(
            strategyConfig.maxInterval,
            currentInterval * this.backoffMultiplier
          );
        } else if (strategy === 'longRunning') {
          // Steady polling for long-running jobs
          nextInterval = Math.min(
            strategyConfig.maxInterval,
            Math.max(strategyConfig.interval, currentInterval)
          );
        }

        // Ensure interval is within bounds
        currentInterval = Math.max(
          this.minPollingInterval,
          Math.min(this.maxPollingInterval, nextInterval)
        );

        // Update tracking variables
        lastProgress = status.progress;
        lastStatus = status.status;

        // Continue polling with optimized interval
        if (!this.isDestroyed) {
          const timeoutId = setTimeout(() => {
            this.activePollingTimeouts.delete(timeoutId);
            poll();
          }, Math.round(currentInterval));
          this.activePollingTimeouts.add(timeoutId);
        }
        
      } catch (error) {
        // Check if service was destroyed during error handling
        if (this.isDestroyed) {
          console.log('AsyncChatService: Polling stopped - service destroyed during error');
          return;
        }
        
        // Handle cancellation differently from other errors
        if (error instanceof Error && error.message === 'Job was cancelled') {
          console.log('Job cancellation detected, stopping polling');
          callbacks.onError(error);
          return;
        }
        
        consecutiveErrors++;
        
        if (consecutiveErrors >= maxConsecutiveErrors) {
          callbacks.onError(new Error(`Too many consecutive polling errors: ${error}`));
          return;
        }
        
        // Use error strategy for recovery
        const errorStrategy = this.pollingStrategies.error;
        currentInterval = Math.min(
          errorStrategy.maxInterval,
          currentInterval * this.backoffMultiplier * 1.5
        );
        
        console.warn(`Polling error (${consecutiveErrors}/${maxConsecutiveErrors}):`, error);
        
        // Continue polling with error recovery interval
        if (!this.isDestroyed) {
          const timeoutId = setTimeout(() => {
            this.activePollingTimeouts.delete(timeoutId);
            poll();
          }, Math.round(currentInterval));
          this.activePollingTimeouts.add(timeoutId);
        }
      }
    };

    // Start polling
    poll();
  }

  /**
   * Clean up all active polling timeouts
   */
  cleanup(): void {
    console.log('AsyncChatService: Starting cleanup...');
    this.activePollingTimeouts.forEach(timeoutId => {
      clearTimeout(timeoutId);
    });
    this.activePollingTimeouts.clear();
    // Don't set isDestroyed = true here to allow graceful completion
    console.log('AsyncChatService: Cleanup completed');
  }

  /**
   * Force destroy the service (use only when absolutely necessary)
   */
  destroy(): void {
    console.log('AsyncChatService: Force destroying service...');
    this.isDestroyed = true;
    this.cleanup();
  }

  /**
   * Process chat request asynchronously with real-time updates
   */
  async processChatAsync(
    params: {
      message: string;
      context: {
        document_content: string;
        chat_history: string;
        available_tools: string;
      };
      sessionId: string;
    },
    callbacks: AsyncChatCallbacks
  ): Promise<void> {
    try {
      // Submit the job
      const jobResponse = await this.submitChatRequest(params);
      console.log('Job submitted:', jobResponse);

      // Start polling for completion
      await this.pollJobCompletion(jobResponse.job_id, callbacks);
    } catch (error) {
      callbacks.onError(error as Error);
    }
  }

  /**
   * Get job statistics
   */
  async getJobStats(): Promise<any> {
    try {
      const token = getAccessToken();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${this.baseURL}/api/v1/async/chat/stats`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get job stats:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const asyncChatService = new AsyncChatService();
export default asyncChatService;
