import axios, { AxiosInstance } from 'axios';
import { API_URL } from '../config/environment';
import { getAccessToken } from './authTokenStore';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  thoughts?: string[];
  thoughtsExpanded?: boolean; // Add this property to fix TypeScript errors
}

export interface ChatRequest {
  user_message: string;
  conversation_history: ChatMessage[];
  document_content: {
    text: string;
    paragraphs?: string[];
    selection?: any;
  };
  session_id?: string | null;
}

export interface RunResponse {
  run_id: string;
  session_id: string;
}

export interface ChatResponse {
  response: string;
  metadata: {
    should_draft_claims: boolean;
    has_claims: boolean;
    reasoning: string;
  };
  data?: {
    claims?: string[];
    num_claims?: number;
    review_comments?: Array<{
      comment: string;
      severity: string;
    }>;
  };
  session_id?: string;
}

export interface StreamEvent {
  event: string;
  data: any;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: any;
}

export type EventType = 
  | 'intent_analysis'
  | 'intent_classified'
  | 'claims_drafting_start'
  | 'claims_progress'
  | 'claims_progress_streaming'
  | 'claims_complete'
  | 'claim_generated'
  | 'prior_art_start'
  | 'prior_art_progress'
  | 'prior_art_complete'
  | 'review_start'
  | 'review_progress'
  | 'review_complete'
  | 'document_transformation'
  | 'processing'
  | 'complete'
  | 'error'
  | 'low_confidence';

class ApiService {
  private api: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = API_URL;
    this.api = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
    });

    this.api.interceptors.request.use((config) => {
      const token = getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  private handleApiError(error: any): ApiError {
    if (error.response) {
      return {
        message: error.response.data?.message || `Server error: ${error.response.status}`,
        code: error.response.status.toString(),
        details: error.response.data
      };
    } else if (error.request) {
      return {
        message: 'No response from server. Please check your connection.',
        code: 'NETWORK_ERROR'
      };
    } else {
      return {
        message: error.message || 'An unexpected error occurred',
        code: 'UNKNOWN_ERROR'
      };
    }
  }

  async startPatentRun(request: ChatRequest): Promise<RunResponse> {
    try {
      const response = await this.api.post('/api/patent/run', request);
      return response.data;
    } catch (error) {
      throw this.handleApiError(error);
    }
  }

  /**
   * Improved streaming with better error handling and event processing
   */
  async chatStream(
    request: ChatRequest,
    onChunk: (chunk: string, eventType?: string) => void,
    onComplete: (response: ChatResponse) => void,
    onError: (error: Error) => void,
    signal?: AbortSignal
  ): Promise<void> {
    try {
      // Log request details for debugging
      
      // Start the patent run
      const runResponse = await this.startPatentRun(request);
              // Patent run started
      
      // Stream the response
      const response = await fetch(`${this.baseURL}/api/patent/stream?run_id=${runResponse.run_id}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${getAccessToken() || ''}`,
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
        },
        signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body reader available');
      }

      let buffer = '';
      const decoder = new TextDecoder();
      let finalResponse: ChatResponse | null = null;
      let currentEventType = '';
      let eventCount = 0;

      try {
        while (true) {
          if (signal?.aborted) {
            throw new Error('Stream aborted by client');
          }

          const { done, value } = await reader.read();
          if (done) {
            // Stream completed
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            const trimmedLine = line.trim();
            if (!trimmedLine) continue;

            if (trimmedLine.startsWith('event: ')) {
              currentEventType = trimmedLine.slice(7).trim();
              console.log(`📡 SSE Event: ${currentEventType}`);
            } else if (trimmedLine.startsWith('data: ')) {
              const content = trimmedLine.slice(6).trim();
              eventCount++;
              
              if (content === '{}') {
                // Stream complete
                console.log('🎯 Stream completion signal received');
                if (finalResponse) {
                  (finalResponse as ChatResponse).session_id = runResponse.session_id;
                  onComplete(finalResponse);
                }
                return;
              }
              
              try {
                const parsed = JSON.parse(content);
                console.log(`🔍 Processing event ${eventCount}: ${currentEventType}`, {
                  hasText: !!parsed.text,
                  hasMessage: !!parsed.message,
                  hasResponse: !!parsed.response,
                  dataKeys: Object.keys(parsed)
                });
                
                // Process the event
                await this.processStreamEvent(
                  currentEventType,
                  parsed,
                  onChunk,
                  (response: ChatResponse) => { 
                    finalResponse = response; 
                  },
                  runResponse.session_id
                );
                
              } catch (parseError) {
                console.warn('Failed to parse streaming data:', parseError);
                console.warn('Raw content:', content.substring(0, 200));
              }
            }
          }
        }

        // Ensure completion if no explicit completion event
        if (finalResponse) {
          (finalResponse as ChatResponse).session_id = runResponse.session_id;
          onComplete(finalResponse);
        } else {
          console.warn('Stream ended without final response');
          onComplete({
            response: 'Request completed',
            metadata: {
              should_draft_claims: false,
              has_claims: false,
              reasoning: 'Stream completed without explicit response'
            },
            session_id: runResponse.session_id
          });
        }

      } finally {
        reader.releaseLock();
      }

    } catch (error) {
      console.error('🚨 Stream error:', error);
      onError(error as Error);
    }
  }

  /**
   * Process individual stream events with better error handling
   */
  private async processStreamEvent(
    eventType: string,
    data: any,
    onChunk: (chunk: string, eventType?: string) => void,
    setFinalResponse: (response: ChatResponse) => void,
    sessionId: string
  ): Promise<void> {
    try {
      switch (eventType) {
        case 'intent_analysis':
          onChunk(data.text || data.message || 'Analyzing your request...', 'intent_analysis');
          break;
          
        case 'intent_classified':
          const confidenceText = data.confidence_score ? 
            `${Math.round((data.confidence_score || 0) * 100)}% confidence` : '';
          const intentText = data.intent ? `Intent: ${data.intent}` : '';
          const combinedText = [intentText, confidenceText].filter(Boolean).join(' - ');
          onChunk(data.text || combinedText || 'Intent classified', 'intent_classified');
          break;
          
        case 'claims_drafting_start':
          onChunk(data.text || 'Starting patent claims drafting...', 'claims_drafting_start');
          break;
          
        case 'claims_progress':
          if (data.stage === 'analysis') {
            if (data.is_streaming) {
              // Streaming analysis chunk
              onChunk(data.text || '', 'claims_progress_streaming');
            } else {
              // Stage message
              onChunk(data.text || 'Analyzing invention disclosure...', 'claims_progress');
            }
          } else if (data.stage === 'feature_identification') {
            onChunk(data.text || 'Identifying key inventive features...', 'claims_progress');
          } else if (data.stage === 'drafting') {
            onChunk(data.text || 'Drafting comprehensive patent claims...', 'claims_progress');
          } else if (data.claim_number) {
            const claimText = data.text || `Processing claim ${data.claim_number}`;
            onChunk(claimText, 'claims_progress');
          } else {
            onChunk(data.text || 'Processing claims...', 'claims_progress');
          }
          break;
          
        case 'claim_generated':
          const claimText = data.text || `Generated claim ${data.claim_number || ''}`;
          onChunk(claimText, 'claim_generated');
          break;
          
        case 'claims_complete':
          const claimsMsg = data.num_claims ? 
            `Successfully drafted ${data.num_claims} patent claims` : 
            'Patent claims completed';
          onChunk(data.text || claimsMsg, 'claims_complete');
          break;
          
        case 'prior_art_start':
          onChunk(data.text || 'Starting prior art search...', 'prior_art_start');
          break;
          
        case 'prior_art_progress':
          let progressText = 'Processing prior art...';
          if (data.stage === 'searching') {
            progressText = 'Searching patent databases...';
          } else if (data.stage === 'analyzing') {
            progressText = 'Analyzing search results for relevance...';
          } else if (data.stage === 'reporting') {
            progressText = 'Generating comprehensive prior art report...';
          }
          onChunk(data.text || progressText, 'prior_art_progress');
          break;
          
        case 'prior_art_complete':
          const patentsMsg = data.patents_found ? 
            `Prior art search completed - found ${data.patents_found} relevant patents` : 
            'Prior art search completed';
          onChunk(data.text || patentsMsg, 'prior_art_complete');
          break;
          
        case 'review_start':
          onChunk(data.text || 'Starting patent claim review...', 'review_start');
          break;
          
        case 'review_progress':
          let reviewText = 'Reviewing claims...';
          if (data.stage === 'analysis') {
            reviewText = 'Analyzing claim structure and language...';
          } else if (data.stage === 'compliance_check') {
            reviewText = 'Checking USPTO compliance...';
          }
          onChunk(data.text || reviewText, 'review_progress');
          break;
          
        case 'review_complete':
          const reviewMsg = data.review_comments?.length ? 
            `Claim review completed - found ${data.review_comments.length} issues to address` : 
            'Claim review completed';
          onChunk(data.text || reviewMsg, 'review_complete');
          break;
          
        case 'processing':
          onChunk(data.message || data.text || 'Processing your request...', 'processing');
          break;
          
        case 'complete':
          // Final completion with results
          const response: ChatResponse = {
            response: data.response || 'Process completed',
            metadata: data.metadata || {
              should_draft_claims: false,
              has_claims: false,
              reasoning: data.message || 'Process completed'
            },
            data: data.data,
            session_id: sessionId
          };
          
          // Handle different types of completions
          if (data.claims) {
            response.data = {
              ...response.data,
              claims: data.claims,
              num_claims: data.num_claims || data.claims.length
            };
            response.metadata.should_draft_claims = true;
            response.metadata.has_claims = true;
          }
          
          if (data.review_comments) {
            response.data = {
              ...response.data,
              review_comments: data.review_comments
            };
          }
          
          console.log('🎯 Final response prepared:', {
            hasResponse: !!response.response,
            hasClaims: !!response.data?.claims,
            hasReviewComments: !!response.data?.review_comments,
            metadata: response.metadata
          });
          
          setFinalResponse(response);
          onChunk(data.response || 'Process completed', 'complete');
          break;
          
        case 'error':
          const errorMsg = data.error || data.message || 'An error occurred';
          onChunk(`❌ ${errorMsg}`, 'error');
          throw new Error(errorMsg);
          
        case 'low_confidence':
          const clarificationMsg = data.message || 'I need more information to help you effectively.';
          onChunk(`❓ ${clarificationMsg}`, 'low_confidence');
          break;
          
        // Legacy event types for backward compatibility
        case 'status':
        case 'reasoning':
          onChunk(data.message || data.text || 'Processing...', eventType);
          break;
          
        case 'search_progress':
        case 'report_progress':
          const progressMsg = data.message || data.text || 'Processing...';
          onChunk(progressMsg, eventType);
          break;
          
        case 'tool_call':
          const toolMsg = data.tool ? 
            `🛠️ Using ${data.tool}...` : 
            '🛠️ Executing tool...';
          onChunk(data.message || data.text || toolMsg, 'tool_call');
          break;
          
        case 'tool_result':
          onChunk(data.message || data.text || '✅ Tool execution completed', 'tool_result');
          break;
          
        case 'results':
          // Legacy results event - treat as completion
          const legacyResponse: ChatResponse = {
            response: data.response || 'Process completed',
            metadata: data.metadata || {
              should_draft_claims: false,
              has_claims: false,
              reasoning: 'Process completed'
            },
            data: data.data,
            session_id: sessionId
          };
          setFinalResponse(legacyResponse);
          onChunk(data.response || 'Results ready', 'results');
          break;
          
        case 'thoughts':
          // Handle AI thinking process
          const thoughtContent = data.content || data.text || 'Processing...';
          onChunk(thoughtContent, 'thoughts');
          break;
          
        case 'done':
          // Legacy done event - handled by stream completion
          console.log('🎯 Legacy done event received');
          break;
          
        default:
          // Handle unknown event type gracefully
          console.warn('⚠️ Unknown event type:', eventType, data);
          
          const unknownMsg = data.text || data.message || data.response || `Unknown event: ${eventType}`;
          onChunk(unknownMsg, 'unknown');
          break;
      }
    } catch (error) {
      console.error(`Error processing event ${eventType}:`, error);
      throw error;
    }
  }

  /**
   * Legacy method for backward compatibility
   */
  async chat(request: { 
    message: string; 
    document_content?: string; 
    session_id?: string | null; 
    conversation_history?: ChatMessage[] 
  }): Promise<ChatResponse> {
    const patentRequest: ChatRequest = {
      user_message: request.message,
      conversation_history: request.conversation_history || [],
      document_content: {
        text: request.document_content || '',
        paragraphs: request.document_content ? [request.document_content] : undefined,
        selection: undefined
      },
      session_id: request.session_id
    };
    
    return new Promise((resolve, reject) => {
      let finalResponse: ChatResponse | null = null;
      
      this.chatStream(
        patentRequest,
        () => {}, // Don't need chunks for non-streaming version
        (response) => {
          resolve(response);
        },
        (error) => {
          reject(error);
        }
      );
    });
  }

  /**
   * Check if the backend is healthy and accessible
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${getAccessToken() || ''}`,
        },
      });
      return response.ok;
    } catch (error) {
      console.warn('Health check failed:', error);
      return false;
    }
  }

  /**
   * Get backend status and version information
   */
  async getBackendStatus(): Promise<any> {
    try {
      const response = await this.api.get('/');
      return response.data;
    } catch (error) {
      console.warn('Failed to get backend status:', error);
      return null;
    }
  }

  /**
   * List all active sessions
   */
  async getSessions(): Promise<any> {
    try {
      const response = await this.api.get('/api/sessions');
      return response.data;
    } catch (error) {
      console.warn('Failed to get sessions:', error);
      return null;
    }
  }

  /**
   * Get detailed information about a specific session
   */
  async getSessionDetails(sessionId: string): Promise<any> {
    try {
      const response = await this.api.get(`/api/debug/session/${sessionId}`);
      return response.data;
    } catch (error) {
      console.warn('Failed to get session details:', error);
      return null;
    }
  }

  /**
   * Transform document using LLM analysis
   */
  async transformDocument(request: {
    user_request: string;
    document_content: string;
    session_id?: string;
  }): Promise<{
    success: boolean;
    message: string;
    data?: any;
    error?: string;
  }> {
    try {
      const response = await this.api.post('/transform-document', request);
      return response.data;
    } catch (error) {
      console.error('Document transformation failed:', error);
      throw this.handleApiError(error);
    }
  }

  /**
   * Get document transformation service status
   */
  async getTransformationStatus(): Promise<any> {
    try {
      const response = await this.api.get('/transform-document/status');
      return response.data;
    } catch (error) {
      console.warn('Failed to get transformation status:', error);
      return null;
    }
  }
}

export const apiService = new ApiService();
export default apiService;