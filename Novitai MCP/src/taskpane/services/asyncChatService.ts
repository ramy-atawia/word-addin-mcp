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
  result?: any;
  completed_at?: string;
}

export interface AsyncChatCallbacks {
  onProgress: (status: JobStatus) => void;
  onComplete: (result: JobResult) => void;
  onError: (error: Error) => void;
}

export class AsyncChatService {
  private baseURL: string;
  private basePollingInterval: number = 1000; // 1 second base
  private maxPollingInterval: number = 10000; // 10 seconds max
  private maxPollingAttempts: number = 300; // 10 minutes max
  private backoffMultiplier: number = 1.5; // Exponential backoff multiplier
  private activePollingTimeouts: Set<NodeJS.Timeout> = new Set();
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
   * Poll for job completion with adaptive polling and exponential backoff
   */
  async pollJobCompletion(
    jobId: string,
    callbacks: AsyncChatCallbacks
  ): Promise<void> {
    if (this.isDestroyed) {
      callbacks.onError(new Error('Service has been destroyed'));
      return;
    }

    let attempts = 0;
    let currentInterval = this.basePollingInterval;
    let consecutiveErrors = 0;
    const maxConsecutiveErrors = 3;

    const poll = async () => {
      // Check if service is destroyed before each poll
      if (this.isDestroyed) {
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
          throw new Error('Job was cancelled');
        }

        // Adaptive polling based on job status and progress
        if (status.status === 'processing' && status.progress > 0) {
          // Job is actively processing, poll more frequently
          currentInterval = Math.max(this.basePollingInterval, currentInterval * 0.8);
        } else if (status.status === 'pending') {
          // Job is pending, use exponential backoff
          currentInterval = Math.min(
            this.maxPollingInterval,
            currentInterval * this.backoffMultiplier
          );
        }

        // Continue polling with adaptive interval - track timeout for cleanup
        const timeoutId = setTimeout(poll, Math.round(currentInterval));
        this.activePollingTimeouts.add(timeoutId);
        
      } catch (error) {
        consecutiveErrors++;
        
        if (consecutiveErrors >= maxConsecutiveErrors) {
          callbacks.onError(new Error(`Too many consecutive polling errors: ${error}`));
          return;
        }
        
        // Exponential backoff on errors
        currentInterval = Math.min(
          this.maxPollingInterval,
          currentInterval * this.backoffMultiplier * 2
        );
        
        console.warn(`Polling error (${consecutiveErrors}/${maxConsecutiveErrors}):`, error);
        
        // Continue polling with increased interval - track timeout for cleanup
        const timeoutId = setTimeout(poll, Math.round(currentInterval));
        this.activePollingTimeouts.add(timeoutId);
      }
    };

    // Start polling
    poll();
  }

  /**
   * Clean up all active polling timeouts
   */
  cleanup(): void {
    this.isDestroyed = true;
    this.activePollingTimeouts.forEach(timeoutId => {
      clearTimeout(timeoutId);
    });
    this.activePollingTimeouts.clear();
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
