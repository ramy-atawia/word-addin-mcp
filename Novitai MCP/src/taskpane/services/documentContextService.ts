/**
 * Document Context Service for Word Add-in
 * Builds intelligent context from document content and provides smart tool suggestions
 */

import {
  officeIntegrationService,
  DocumentMetadata,
  DocumentStats,
} from "./officeIntegrationService";

export interface DocumentContext {
  fullContent: string;
  selectedText: string;
  documentStats: DocumentStats;
  metadata: DocumentMetadata;
  contextWindow: string;
  relevantTopics: string[];
  suggestedTools: string[];
  contextualPrompts: string[];
}

export interface ToolSuggestion {
  toolName: string;
  reason: string;
  confidence: number;
  parameters: Record<string, any>;
}

export class DocumentContextService {
  private contextCache: Map<string, DocumentContext> = new Map();
  private cacheTimeout = 5 * 60 * 1000; // 5 minutes

  /**
   * Build comprehensive document context
   */
  async buildDocumentContext(): Promise<DocumentContext> {
    try {
      const cacheKey = `context_${Date.now()}`;

      // Check cache first
      if (this.contextCache.has(cacheKey)) {
        const cached = this.contextCache.get(cacheKey)!;
        if (Date.now() - parseInt(cacheKey.split("_")[1]) < this.cacheTimeout) {
          return cached;
        }
      }

      // Build fresh context
      const [content, selectedText, metadata, stats] = await Promise.all([
        officeIntegrationService.getDocumentContent(),
        officeIntegrationService.getSelectedText(),
        officeIntegrationService.getDocumentMetadata(),
        officeIntegrationService.getDocumentStatistics(),
      ]);

      const context: DocumentContext = {
        fullContent: content,
        selectedText: selectedText,
        documentStats: stats,
        metadata: metadata,
        contextWindow: this.buildContextWindow(content, selectedText),
        relevantTopics: this.extractRelevantTopics(content, selectedText),
        suggestedTools: await this.suggestRelevantTools(content, selectedText),
        contextualPrompts: this.generateContextualPrompts(content, selectedText),
      };

      // Cache the context
      this.contextCache.set(cacheKey, context);

      return context;
    } catch (error) {
      console.error("Failed to build document context:", error);
      return this.getDefaultContext();
    }
  }

  /**
   * Update context based on current selection
   */
  async updateContextFromSelection(): Promise<void> {
    try {
      const selectedText = await officeIntegrationService.getSelectedText();
      if (selectedText.trim()) {
        // Clear cache to force refresh
        this.contextCache.clear();
        console.log("Context updated from selection:", selectedText.substring(0, 100));
      }
    } catch (error) {
      console.error("Failed to update context from selection:", error);
    }
  }

  /**
   * Cache document content for performance
   */
  async cacheDocumentContent(): Promise<void> {
    try {
      const content = await officeIntegrationService.getDocumentContent();
      if (content.length > 10000) {
        console.log("Large document detected, caching content for performance");
        // For large documents, we could implement progressive loading
      }
    } catch (error) {
      console.error("Failed to cache document content:", error);
    }
  }

  /**
   * Suggest relevant tools based on document context
   */
  async suggestRelevantTools(content: string, selectedText: string): Promise<string[]> {
    const suggestions: string[] = [];

    try {
      // Analyze content for tool suggestions
      const hasWebContent = this.detectWebContentNeeds(content, selectedText);
      const hasTextProcessing = this.detectTextProcessingNeeds(content, selectedText);
      const hasDocumentAnalysis = this.detectDocumentAnalysisNeeds(content, selectedText);
      const hasDataFormatting = this.detectDataFormattingNeeds(content, selectedText);

      if (hasWebContent) {
        suggestions.push("web_content_fetcher");
      }

      if (hasTextProcessing) {
        suggestions.push("text_processor");
      }

      if (hasDocumentAnalysis) {
        suggestions.push("document_analyzer");
      }

      if (hasDataFormatting) {
        suggestions.push("data_formatter");
      }

      // Always include web search if text is selected
      if (selectedText.trim() && !suggestions.includes("web_content_fetcher")) {
        suggestions.unshift("web_content_fetcher");
      }

      return suggestions;
    } catch (error) {
      console.error("Failed to suggest relevant tools:", error);
      return ["web_content_fetcher"]; // Default fallback
    }
  }

  /**
   * Generate contextual prompts based on document content
   */
  generateContextualPrompts(content: string, selectedText: string): string[] {
    const prompts: string[] = [];

    try {
      // Generate prompts based on content analysis
      if (selectedText.trim()) {
        prompts.push(`Search for information about: "${selectedText}"`);
        prompts.push(`Find more details on: "${selectedText}"`);
        prompts.push(`Research this topic: "${selectedText}"`);
      }

      if (content.length > 1000) {
        prompts.push("Summarize this document");
        prompts.push("Analyze document readability");
        prompts.push("Extract key points from this document");
      }

      if (this.detectResearchContent(content)) {
        prompts.push("Find related research papers");
        prompts.push("Search for recent developments in this field");
        prompts.push("Find expert opinions on this topic");
      }

      if (this.detectTechnicalContent(content)) {
        prompts.push("Explain technical concepts in simple terms");
        prompts.push("Find tutorials on this topic");
        prompts.push("Search for code examples");
      }

      return prompts;
    } catch (error) {
      console.error("Failed to generate contextual prompts:", error);
      return ["How can I help you with this document?"]; // Default fallback
    }
  }

  /**
   * Build context window for AI processing
   */
  private buildContextWindow(content: string, selectedText: string): string {
    try {
      let context = "";

      // Add document statistics
      const stats = this.calculateBasicStats(content);
      context += `Document Statistics: ${stats.wordCount} words, ${stats.paragraphCount} paragraphs\n\n`;

      // Add selected text if available
      if (selectedText.trim()) {
        context += `Selected Text: "${selectedText}"\n\n`;

        // Add surrounding context
        const surroundingContext = this.getSurroundingContext(content, selectedText);
        if (surroundingContext) {
          context += `Context: ${surroundingContext}\n\n`;
        }
      }

      // Add document summary (first 200 characters)
      if (content.length > 200) {
        context += `Document Preview: ${content.substring(0, 200)}...\n\n`;
      } else {
        context += `Document Content: ${content}\n\n`;
      }

      return context;
    } catch (error) {
      console.error("Failed to build context window:", error);
      return `Document Content: ${content.substring(0, 500)}...`;
    }
  }

  /**
   * Extract relevant topics from content
   */
  private extractRelevantTopics(content: string, selectedText: string): string[] {
    try {
      const topics: string[] = [];

      // Add selected text as primary topic
      if (selectedText.trim()) {
        topics.push(selectedText.trim());
      }

      // Extract potential topics from content (simple keyword extraction)
      const words = content.toLowerCase().split(/\s+/);
      const wordCount: Record<string, number> = {};

      // Count significant words (filter out common words)
      const commonWords = new Set([
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
        "this",
        "that",
        "these",
        "those",
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "me",
        "him",
        "her",
        "us",
        "them",
      ]);

      words.forEach((word) => {
        const cleanWord = word.replace(/[^\w]/g, "");
        if (cleanWord.length > 3 && !commonWords.has(cleanWord)) {
          wordCount[cleanWord] = (wordCount[cleanWord] || 0) + 1;
        }
      });

      // Get top 5 most frequent words as topics
      const sortedWords = Object.entries(wordCount)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 5)
        .map(([word]) => word);

      topics.push(...sortedWords);

      return topics;
    } catch (error) {
      console.error("Failed to extract relevant topics:", error);
      return [];
    }
  }

  /**
   * Detect if content needs web search
   */
  private detectWebContentNeeds(content: string, _selectedText: string): boolean {
    // Always suggest web search if text is selected
    if (_selectedText.trim()) {
      return true;
    }

    // Detect research-related content
    const researchKeywords = [
      "research",
      "study",
      "investigation",
      "analysis",
      "survey",
      "findings",
      "results",
      "conclusion",
    ];
    const hasResearchContent = researchKeywords.some((keyword) =>
      content.toLowerCase().includes(keyword)
    );

    return hasResearchContent;
  }

  /**
   * Detect if content needs text processing
   */
  private detectTextProcessingNeeds(content: string, _selectedText: string): boolean {
    // Check for long content that might benefit from summarization
    if (content.length > 2000) {
      return true;
    }

    // Check for complex sentences that might need simplification
    const sentences = content.split(/[.!?]+/);
    const longSentences = sentences.filter((sentence) => sentence.split(/\s+/).length > 20);

    return longSentences.length > 2;
  }

  /**
   * Detect if content needs document analysis
   */
  private detectDocumentAnalysisNeeds(content: string, _selectedText: string): boolean {
    // Check for structured content
    const hasStructuredContent =
      content.includes("1.") || content.includes("•") || content.includes("-");

    // Check for technical content
    const hasTechnicalContent = this.detectTechnicalContent(content);

    return hasStructuredContent || hasTechnicalContent;
  }

  /**
   * Detect if content needs data formatting
   */
  private detectDataFormattingNeeds(content: string, _selectedText: string): boolean {
    // Check for tabular data
    const hasTabularData = content.includes("\t") || content.includes("|");

    // Check for list-like content
    const hasListContent = content.includes("1.") || content.includes("•") || content.includes("-");

    return hasTabularData || hasListContent;
  }

  /**
   * Detect research content
   */
  private detectResearchContent(content: string): boolean {
    const researchKeywords = [
      "research",
      "study",
      "investigation",
      "analysis",
      "survey",
      "findings",
      "results",
      "conclusion",
      "methodology",
      "hypothesis",
    ];
    return researchKeywords.some((keyword) => content.toLowerCase().includes(keyword));
  }

  /**
   * Detect technical content
   */
  private detectTechnicalContent(content: string): boolean {
    const technicalKeywords = [
      "algorithm",
      "function",
      "method",
      "class",
      "interface",
      "api",
      "protocol",
      "framework",
      "library",
      "database",
      "server",
      "client",
    ];
    return technicalKeywords.some((keyword) => content.toLowerCase().includes(keyword));
  }

  /**
   * Get surrounding context for selected text
   */
  private getSurroundingContext(content: string, selectedText: string): string {
    try {
      const index = content.indexOf(selectedText);
      if (index === -1) return "";

      const beforeText = content.substring(Math.max(0, index - 100), index);
      const afterText = content.substring(
        index + selectedText.length,
        index + selectedText.length + 100
      );

      return `${beforeText} [SELECTED] ${afterText}`;
    } catch (error) {
      return "";
    }
  }

  /**
   * Calculate basic document statistics
   */
  private calculateBasicStats(content: string): { wordCount: number; paragraphCount: number } {
    try {
      const words = content.trim().split(/\s+/);
      const paragraphs = content.split(/\n\s*\n/);

      return {
        wordCount: content.trim() ? words.length : 0,
        paragraphCount: paragraphs.length,
      };
    } catch (error) {
      return { wordCount: 0, paragraphCount: 0 };
    }
  }

  /**
   * Get default context when building fails
   */
  private getDefaultContext(): DocumentContext {
    return {
      fullContent: "",
      selectedText: "",
      documentStats: {
        wordCount: 0,
        characterCount: 0,
        paragraphCount: 0,
        lineCount: 0,
        pageCount: 0,
      },
      metadata: {
        title: "Error",
        author: "Unknown",
        createdDate: new Date(),
        modifiedDate: new Date(),
        wordCount: 0,
        characterCount: 0,
        paragraphCount: 0,
      },
      contextWindow: "Document context unavailable",
      relevantTopics: [],
      suggestedTools: ["web_content_fetcher"],
      contextualPrompts: ["How can I help you?"],
    };
  }
}

// Export singleton instance
export const documentContextService = new DocumentContextService();
