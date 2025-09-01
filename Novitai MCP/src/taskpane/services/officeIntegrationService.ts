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

  constructor() {
    this.initializeOffice();
  }

  /**
   * Initialize Office.js integration
   */
  private async initializeOffice(): Promise<void> {
    try {
      // Check if Office.js is available
      if (typeof Office !== 'undefined') {
        this.isOfficeReady = true;
        console.log('Office.js integration ready');
      } else {
        console.warn('Office.js not available - running in standalone mode');
        this.isOfficeReady = false;
      }
    } catch (error) {
      console.error('Failed to initialize Office.js:', error);
      this.isOfficeReady = false;
    }
  }

  /**
   * Check if Office.js is ready for use
   */
  async checkOfficeReady(): Promise<boolean> {
    return this.isOfficeReady;
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
   * Replace selected text with new content
   */
  async replaceSelectedText(text: string, options: Partial<InsertionOptions> = {}): Promise<void> {
    return this.insertText(text, { ...options, location: 'selection' });
  }

  /**
   * Get document metadata and statistics
   */
  async getDocumentMetadata(): Promise<DocumentMetadata> {
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
}

// Export singleton instance
export const officeIntegrationService = new OfficeIntegrationService();
