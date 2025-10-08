/**
 * Office Integration Service for Word Add-in
 * Handles document operations, text extraction, and content insertion
 */

export interface DocumentMetadata {
  title: string;
  author: string;
  createdDate: Date;
  modifiedDate: Date;
  wordCount: number;
  characterCount: number;
  paragraphCount: number;
}

export interface DocumentStats {
  wordCount: number;
  characterCount: number;
  paragraphCount: number;
  lineCount: number;
  pageCount: number;
}

export interface InsertionOptions {
  location: 'cursor' | 'selection' | 'end' | 'newParagraph';
  format?: 'plain' | 'formatted' | 'withSource';
  source?: string;
  addFootnote?: boolean;
}

export class OfficeIntegrationService {
  private isOfficeReady: boolean = false;
  private initializationPromise: Promise<void>;

  constructor() {
    this.initializationPromise = this.initializeOffice();
  }

  /**
   * Initialize Office.js integration
   */
  private async initializeOffice(): Promise<void> {
    try {
      // Use Office.onReady() for proper initialization
      await new Promise<void>((resolve) => {
        if (typeof Office !== 'undefined' && Office.onReady) {
          Office.onReady((info) => {
            console.log('Office.onReady callback executed with info:', info);
            
            if (info.host === Office.HostType.Word) {
              this.isOfficeReady = true;
              console.log('Office.js integration ready for Word');
              resolve();
            } else {
              console.warn('Not running in Word, host type:', info.host);
              this.isOfficeReady = false;
              resolve(); // Still resolve to allow app to work
            }
          });
        } else {
          // Fallback for cases where Office.js is not available
          console.warn('Office.js not available - running in standalone mode');
          this.isOfficeReady = false;
          resolve();
        }
      });
      
    } catch (error) {
      console.error('Failed to initialize Office.js:', error);
      this.isOfficeReady = false;
    }
  }


  /**
   * Check if Office.js is ready for use
   */
  async checkOfficeReady(): Promise<boolean> {
    await this.initializationPromise;
    
    // Additional debugging
    console.log('=== Office.js Readiness Check ===');
    console.log('isOfficeReady:', this.isOfficeReady);
    console.log('Office defined:', typeof Office !== 'undefined');
    console.log('Office.context:', typeof Office !== 'undefined' && Office.context);
    console.log('Office.context.document:', typeof Office !== 'undefined' && Office.context && Office.context.document);
    
    // Safe property access with type checking
    if (typeof Office !== 'undefined' && Office.context) {
      const context = Office.context as any;
      console.log('Office.context.requirements:', context.requirements);
      console.log('Office.context.platform:', context.platform);
    }
    
    // If not ready, try to reinitialize
    if (!this.isOfficeReady && typeof Office !== 'undefined') {
      console.log('Office.js not ready, attempting reinitialization...');
      try {
        await this.initializeOffice();
        console.log('Reinitialization result:', this.isOfficeReady);
      } catch (error) {
        console.error('Reinitialization failed:', error);
      }
    }
    
    return this.isOfficeReady;
  }

  /**
   * Wait for Office.js to be ready with retry mechanism
   */
  async waitForOfficeReady(maxAttempts: number = 10): Promise<boolean> {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      console.log(`Office.js readiness check attempt ${attempt}/${maxAttempts}`);
      
      if (this.isOfficeReady) {
        console.log('Office.js is ready!');
        return true;
      }
      
      // Wait a bit before next attempt
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    console.warn(`Office.js not ready after ${maxAttempts} attempts`);
    return false;
  }

  /**
   * Get Office.js version information
   */
  async getOfficeVersion(): Promise<string> {
    if (!this.isOfficeReady) {
      return 'standalone';
    }

    try {
      return Office.context.document.url || 'unknown';
    } catch (error) {
      console.error('Failed to get Office version:', error);
      return 'unknown';
    }
  }

  /**
   * Extract full document content
   */
  async getDocumentContent(): Promise<string> {
    await this.initializationPromise;
    
    if (!this.isOfficeReady) {
      console.warn('Office.js not available, returning empty content');
      return '';
    }

    return new Promise((resolve, reject) => {
      Word.run(async (context) => {
        try {
          const body = context.document.body;
          body.load('text');
          await context.sync();
          resolve(body.text || '');
        } catch (error) {
          reject(error);
        }
      }).catch(reject);
    });
  }

  /**
   * Get currently selected text
   */
  async getSelectedText(): Promise<string> {
    await this.initializationPromise;
    
    if (!this.isOfficeReady) {
      console.warn('Office.js not available, returning empty selection');
      return '';
    }

    return new Promise((resolve, reject) => {
      Word.run(async (context) => {
        try {
          const range = context.document.getSelection();
          range.load('text');
          await context.sync();
          resolve(range.text || '');
        } catch (error) {
          reject(error);
        }
      }).catch(reject);
    });
  }

  /**
   * Insert text at specified location
   */
  async insertText(text: string, options: InsertionOptions = { location: 'cursor' }): Promise<void> {
    await this.initializationPromise;
    
    if (!this.isOfficeReady) {
      console.warn('Office.js not available, cannot insert text');
      return;
    }

    return new Promise((resolve, reject) => {
      Word.run(async (context) => {
        try {
          const { location, format, source, addFootnote } = options;
          
          let contentToInsert = text;
          
          // Format content based on options
          if (format === 'withSource' && source) {
            contentToInsert = `${text}\n\nSource: ${source}`;
          }
          
          switch (location) {
            case 'cursor':
              const cursorRange = context.document.getSelection();
              cursorRange.insertText(contentToInsert, 'After');
              break;
              
            case 'selection':
              const selectionRange = context.document.getSelection();
              selectionRange.insertText(contentToInsert, 'Replace');
              break;
              
            case 'end':
              const body = context.document.body;
              body.insertParagraph(contentToInsert, 'End');
              break;
              
            case 'newParagraph':
              const body2 = context.document.body;
              body2.insertParagraph(contentToInsert, 'End');
              break;
          }
          
          // Add footnote if requested
          if (addFootnote && source) {
            const footnoteBody = context.document.body;
            footnoteBody.insertParagraph(`Footnote: ${source}`, 'End');
          }
          
          await context.sync();
          resolve();
        } catch (error) {
          reject(error);
        }
      }).catch(reject);
    });
  }

  /**
   * Insert formatted markdown content at specified location
   */
  async insertFormattedMarkdown(markdown: string, options: InsertionOptions = { location: 'cursor' }): Promise<void> {
    await this.initializationPromise;
    
    if (!this.isOfficeReady) {
      console.warn('Office.js not available, cannot insert formatted content');
      return;
    }

    return new Promise((resolve, reject) => {
      Word.run(async (context) => {
        try {
          const { location } = options;
          
          // Convert markdown to formatted text with basic styling
          const formattedText = this.convertMarkdownToFormattedText(markdown);
          
          // Get the insertion point and insert content
          switch (location) {
            case 'cursor':
            case 'selection':
              const selectionRange = context.document.getSelection();
              selectionRange.insertText(formattedText, 'After');
              break;
            case 'end':
            case 'newParagraph':
              const body = context.document.body;
              body.insertParagraph(formattedText, 'End');
              break;
            default:
              const defaultRange = context.document.getSelection();
              defaultRange.insertText(formattedText, 'After');
          }
          
          await context.sync();
          resolve();
        } catch (error) {
          reject(error);
        }
      }).catch(reject);
    });
  }

  /**
   * Convert markdown to formatted text for Word insertion
   */
  private convertMarkdownToFormattedText(markdown: string): string {
    return markdown
      // Convert headers to bold text with line breaks
      .replace(/^# (.*$)/gm, '$1\n')
      .replace(/^## (.*$)/gm, '$1\n')
      .replace(/^### (.*$)/gm, '$1\n')
      .replace(/^#### (.*$)/gm, '$1\n')
      .replace(/^##### (.*$)/gm, '$1\n')
      .replace(/^###### (.*$)/gm, '$1\n')
      // Convert bold text (keep the ** for now, Word will handle it)
      .replace(/\*\*(.*?)\*\*/g, '$1')
      // Convert italic text
      .replace(/\*(.*?)\*/g, '$1')
      // Convert inline code
      .replace(/`(.*?)`/g, '$1')
      // Convert links to just the text
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      // Convert list items
      .replace(/^\s*[-*+]\s/gm, '• ')
      .replace(/^\s*\d+\.\s/gm, '')
      // Normalize multiple newlines
      .replace(/\n{3,}/g, '\n\n')
      // Clean up any remaining markdown syntax
      .replace(/^#+\s*/gm, '')
      .trim();
  }

  /**
   * Insert HTML content at specified location
   */
  async insertHTML(htmlContent: string, options: InsertionOptions = { location: 'cursor' }): Promise<void> {
    await this.initializationPromise;
    
    if (!this.isOfficeReady) {
      console.warn('Office.js not available, cannot insert HTML content');
      return;
    }

    return new Promise((resolve, reject) => {
      Word.run(async (context) => {
        try {
          const { location } = options;
          
          // Get the insertion point and insert HTML content
          switch (location) {
            case 'cursor':
            case 'selection':
              const selectionRange = context.document.getSelection();
              selectionRange.insertHtml(htmlContent, 'After');
              break;
            case 'end':
            case 'newParagraph':
              const body = context.document.body;
              body.insertHtml(htmlContent, 'End');
              break;
            default:
              const defaultRange = context.document.getSelection();
              defaultRange.insertHtml(htmlContent, 'After');
          }
          
          await context.sync();
          resolve();
        } catch (error) {
          reject(error);
        }
      }).catch(reject);
    });
  }

  /**
   * Replace selected text with new content
   */
  async replaceSelectedText(text: string, options: Partial<InsertionOptions> = {}): Promise<void> {
    return this.insertText(text, { ...options, location: 'selection' });
  }

  /**
   * Get document metadata and statistics
   */
  async getDocumentMetadata(): Promise<DocumentMetadata> {
    await this.initializationPromise;
    
    if (!this.isOfficeReady) {
      return {
        title: 'Standalone Mode',
        author: 'Unknown',
        createdDate: new Date(),
        modifiedDate: new Date(),
        wordCount: 0,
        characterCount: 0,
        paragraphCount: 0
      };
    }

    try {
      const content = await this.getDocumentContent();
      const stats = this.calculateDocumentStats(content);
      
      return {
        title: 'Document', // Office.js doesn't provide title easily
        author: 'Unknown', // Office.js doesn't provide author easily
        createdDate: new Date(),
        modifiedDate: new Date(),
        wordCount: stats.wordCount,
        characterCount: stats.characterCount,
        paragraphCount: stats.paragraphCount
      };
    } catch (error) {
      console.error('Failed to get document metadata:', error);
      return {
        title: 'Error',
        author: 'Unknown',
        createdDate: new Date(),
        modifiedDate: new Date(),
        wordCount: 0,
        characterCount: 0,
        paragraphCount: 0
      };
    }
  }

  /**
   * Get document statistics
   */
  async getDocumentStatistics(): Promise<DocumentStats> {
    await this.initializationPromise;
    
    if (!this.isOfficeReady) {
      return {
        wordCount: 0,
        characterCount: 0,
        paragraphCount: 0,
        lineCount: 0,
        pageCount: 0
      };
    }

    try {
      const content = await this.getDocumentContent();
      return this.calculateDocumentStats(content);
    } catch (error) {
      console.error('Failed to get document statistics:', error);
      return {
        wordCount: 0,
        characterCount: 0,
        paragraphCount: 0,
        lineCount: 0,
        pageCount: 0
      };
    }
  }

  /**
   * Calculate document statistics from content
   */
  private calculateDocumentStats(content: string): DocumentStats {
    const lines = content.split('\n');
    const paragraphs = content.split(/\n\s*\n/);
    const words = content.trim().split(/\s+/);
    
    return {
      wordCount: content.trim() ? words.length : 0,
      characterCount: content.length,
      paragraphCount: paragraphs.length,
      lineCount: lines.length,
      pageCount: Math.ceil(content.length / 2000) // Rough estimate: 2000 chars per page
    };
  }

  /**
   * Check if text is currently selected
   */
  async hasSelection(): Promise<boolean> {
    await this.initializationPromise;
    
    if (!this.isOfficeReady) {
      return false;
    }

    try {
      const selectedText = await this.getSelectedText();
      return selectedText.trim().length > 0;
    } catch (error) {
      console.error('Failed to check selection:', error);
      return false;
    }
  }

  /**
   * Get selection context (surrounding text)
   */
  async getSelectionContext(beforeWords: number = 10, afterWords: number = 10): Promise<string> {
    await this.initializationPromise;
    
    if (!this.isOfficeReady) {
      return '';
    }

    try {
      const fullContent = await this.getDocumentContent();
      const selectedText = await this.getSelectedText();
      
      if (!selectedText.trim()) {
        return '';
      }

      const selectedIndex = fullContent.indexOf(selectedText);
      if (selectedIndex === -1) {
        return selectedText;
      }

      const beforeText = fullContent.substring(0, selectedIndex);
      const afterText = fullContent.substring(selectedIndex + selectedText.length);

      const beforeWordsArray = beforeText.trim().split(/\s+/).slice(-beforeWords);
      const afterWordsArray = afterText.trim().split(/\s+/).slice(0, afterWords);

      return `${beforeWordsArray.join(' ')} [SELECTED: ${selectedText}] ${afterWordsArray.join(' ')}`;
    } catch (error) {
      console.error('Failed to get selection context:', error);
      return '';
    }
  }

  /**
   * Get document content as paragraphs with formatting
   */
  async getDocumentParagraphs(): Promise<Array<{index: number, text: string, formatting?: any}>> {
    await this.initializationPromise;
    
    if (!this.isOfficeReady) {
      console.warn('Office.js not available, returning empty paragraphs');
      return [];
    }

    return new Promise((resolve, reject) => {
      Word.run(async (context) => {
        try {
          const paragraphs = context.document.body.paragraphs;
          paragraphs.load('text,font/bold,font/italic,font/size,font/name,font/color');
          await context.sync();
          
          console.log(`Office.js found ${paragraphs.items.length} paragraphs`);
          
          const paragraphData = paragraphs.items.map((para, index) => {
            const text = para.text || '';
            console.log(`Paragraph ${index}: "${text.substring(0, 50)}${text.length > 50 ? '...' : ''}"`);
            
            return {
              index: index,
              text: text,
              formatting: {
                bold: para.font.bold,
                italic: para.font.italic,
                font_size: para.font.size,
                font_name: para.font.name,
                color: para.font.color
              }
            };
          });
          
          // Filter out empty paragraphs
          const nonEmptyParagraphs = paragraphData.filter(para => para.text.trim().length > 0);
          console.log(`Found ${nonEmptyParagraphs.length} non-empty paragraphs`);
          
          resolve(nonEmptyParagraphs);
        } catch (error) {
          console.error('Error getting document paragraphs:', error);
          reject(error);
        }
      }).catch(reject);
    });
  }

  /**
   * Search and replace text in a specific paragraph with track changes
   */
  async searchAndReplaceInParagraph(
    paragraphIndex: number, 
    findText: string, 
    replaceText: string, 
    reason: string
  ): Promise<boolean> {
    await this.initializationPromise;
    
    if (!this.isOfficeReady) {
      console.warn('Office.js not available, cannot perform search and replace');
      return false;
    }

    return new Promise((resolve) => {
      Word.run(async (context) => {
        try {
          const paragraphs = context.document.body.paragraphs;
          paragraphs.load('text');
          await context.sync();
          
          if (paragraphIndex >= paragraphs.items.length) {
            throw new Error(`Paragraph index ${paragraphIndex} not found`);
          }
          
          const paragraph = paragraphs.items[paragraphIndex];
          
          console.log(`Searching for "${findText}" in paragraph ${paragraphIndex}`);
          console.log(`Paragraph text: "${paragraph.text}"`);
          
          // Try exact match first with whole word
          let ranges = paragraph.search(findText, {
            matchCase: false,
            matchWholeWord: true
          });
          ranges.load('text');
          await context.sync();
          
          console.log(`Whole word search found ${ranges.items.length} matches`);
          
          // If no exact match, try without whole word constraint
          if (ranges.items.length === 0) {
            ranges = paragraph.search(findText, {
              matchCase: false,
              matchWholeWord: false
            });
            ranges.load('text');
            await context.sync();
            console.log(`Partial word search found ${ranges.items.length} matches`);
          }
          
          if (ranges.items.length === 0) {
            console.error(`Text "${findText}" not found in paragraph ${paragraphIndex}`);
            console.error(`Available text: "${paragraph.text}"`);
            throw new Error(`Text "${findText}" not found in paragraph ${paragraphIndex}`);
          }
          
          const range = ranges.items[0];
          
          // Replace the text
          range.insertText(replaceText, Word.InsertLocation.replace);
          
          // Add review comment
          range.insertComment(reason);
          
          await context.sync();
          resolve(true);
          
        } catch (error) {
          console.error('Search and replace failed:', error);
          resolve(false);
        }
      }).catch((error) => {
        console.error('Word.run failed:', error);
        resolve(false);
      });
    });
  }
}

// Export singleton instance
export const officeIntegrationService = new OfficeIntegrationService();

// Add global debugging function for console testing
if (typeof window !== 'undefined') {
  (window as any).debugOfficeJS = async () => {
    console.log('=== Manual Office.js Debug ===');
    console.log('Office defined:', typeof Office !== 'undefined');
    if (typeof Office !== 'undefined') {
      console.log('Office.context:', Office.context);
      console.log('Office.context.document:', Office.context?.document);
      
      // Safe property access with type checking
      const context = Office.context as any;
      console.log('Office.context.requirements:', context?.requirements);
      console.log('Office.context.platform:', context?.platform);
      console.log('Office.context.host:', context?.host);
    }
    
    const isReady = await officeIntegrationService.checkOfficeReady();
    console.log('Office.js ready:', isReady);
    return isReady;
  };
}
