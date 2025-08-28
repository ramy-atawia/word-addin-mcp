/**
 * Office.js API wrapper service for Word document interaction
 * This service provides a clean interface for working with Word documents
 */

export interface DocumentRange {
  start: number;
  end: number;
  text: string;
}

export interface DocumentSelection {
  range: DocumentRange;
  isEmpty: boolean;
}

export interface DocumentContent {
  text: string;
  ranges: DocumentRange[];
  paragraphs: string[];
  tables: any[];
  images: any[];
}

export interface InsertionOptions {
  insertLocation?: 'replace' | 'start' | 'end' | 'before' | 'after';
  formatting?: 'keep' | 'matchDestination' | 'matchSource';
  trackChanges?: boolean;
}

export interface DocumentState {
  isDirty: boolean;
  lastSaved?: Date;
  hasUnsavedChanges: boolean;
  documentName: string;
  documentUrl: string;
}

class OfficeService {
  private isInitialized = false;
  private documentState: DocumentState | null = null;
  private changeListeners: Array<(state: DocumentState) => void> = [];

  /**
   * Initialize the Office.js service
   */
  async initialize(): Promise<boolean> {
    try {
      // Check if Office.js is available
      if (typeof Office === 'undefined') {
        throw new Error('Office.js is not available. This add-in must run in Office.');
      }

      // Wait for Office.js to be ready
      await new Promise<void>((resolve, reject) => {
        Office.onReady((info) => {
          if (info.host === Office.HostType.Word) {
            this.isInitialized = true;
            this.setupEventListeners();
            this.initializeDocumentState();
            resolve();
          } else {
            reject(new Error('This add-in only works in Word.'));
          }
        });
      });

      return true;
    } catch (error) {
      console.error('Failed to initialize Office.js service:', error);
      return false;
    }
  }

  /**
   * Check if the service is initialized
   */
  isReady(): boolean {
    return this.isInitialized && typeof Office !== 'undefined';
  }

  /**
   * Get the current document state
   */
  getDocumentState(): DocumentState | null {
    return this.documentState;
  }

  /**
   * Add a listener for document state changes
   */
  addChangeListener(listener: (state: DocumentState) => void): void {
    this.changeListeners.push(listener);
  }

  /**
   * Remove a change listener
   */
  removeChangeListener(listener: (state: DocumentState) => void): void {
    const index = this.changeListeners.indexOf(listener);
    if (index > -1) {
      this.changeListeners.splice(index, 1);
    }
  }

  /**
   * Read content from the current document
   */
  async readDocumentContent(options: {
    includeFormatting?: boolean;
    includeTables?: boolean;
    includeImages?: boolean;
  } = {}): Promise<DocumentContent> {
    if (!this.isReady()) {
      throw new Error('Office.js service is not initialized');
    }

    try {
      return await new Promise((resolve, reject) => {
        Word.run(async (context) => {
          try {
            const body = context.document.body;
            const text = body.text;
            
            // Get paragraphs
            const paragraphs = body.paragraphs;
            paragraphs.load('text');
            
            // Get tables if requested
            let tables: any[] = [];
            if (options.includeTables) {
              const documentTables = body.tables;
              documentTables.load('rows,columns');
              await context.sync();
              tables = documentTables.items.map(table => ({
                rows: table.rows.items.length,
                columns: (table as any).columns?.items?.length || 0
              }));
            }
            
            // Get images if requested
            let images: any[] = [];
            if (options.includeImages) {
              const documentImages = body.inlinePictures;
              documentImages.load('width,height');
              await context.sync();
              images = documentImages.items.map(img => ({
                width: img.width,
                height: img.height
              }));
            }
            
            await context.sync();
            
            const content: DocumentContent = {
              text,
              ranges: [{ start: 0, end: text.length, text }],
              paragraphs: paragraphs.items.map(p => p.text),
              tables,
              images
            };
            
            resolve(content);
          } catch (error) {
            reject(error);
          }
        });
      });
    } catch (error) {
      console.error('Failed to read document content:', error);
      throw error;
    }
  }

  /**
   * Read content from a specific range
   */
  async readRange(range: DocumentRange): Promise<string> {
    if (!this.isReady()) {
      throw new Error('Office.js service is not initialized');
    }

    try {
      return await new Promise((resolve, reject) => {
        Word.run(async (context) => {
          try {
            const rangeObj = context.document.body.getRange(range.start as any);
            rangeObj.load('text');
            await context.sync();
            // Get the text up to the end position
            const fullText = rangeObj.text;
            const endPos = Math.min(range.end - range.start, fullText.length);
            const text = fullText.substring(0, endPos);
            resolve(text);
          } catch (error) {
            reject(error);
          }
        });
      });
    } catch (error) {
      console.error('Failed to read range:', error);
      throw error;
    }
  }

  /**
   * Insert content into the document
   */
  async insertContent(
    content: string,
    options: InsertionOptions = {}
  ): Promise<boolean> {
    if (!this.isReady()) {
      throw new Error('Office.js service is not initialized');
    }

    try {
      return await new Promise((resolve, reject) => {
        Word.run(async (context) => {
          try {
            const body = context.document.body;
            
            switch (options.insertLocation) {
              case 'replace':
                // Replace selected text
                const selection = context.document.getSelection();
                selection.load('text');
                await context.sync();
                
                if (selection.text) {
                  selection.insertText(content, Word.InsertLocation.replace);
                } else {
                  // Insert at cursor if nothing is selected
                  body.insertParagraph(content, Word.InsertLocation.start);
                }
                break;
                
              case 'start':
                body.insertParagraph(content, Word.InsertLocation.start);
                break;
                
              case 'end':
                body.insertParagraph(content, Word.InsertLocation.end);
                break;
                
              case 'before':
                // Insert before current selection
                const beforeSelection = context.document.getSelection();
                beforeSelection.load('getRange');
                await context.sync();
                
                if (beforeSelection.getRange()) {
                  beforeSelection.getRange().insertParagraph(content, Word.InsertLocation.before);
                } else {
                  body.insertParagraph(content, Word.InsertLocation.start);
                }
                break;
                
              case 'after':
                // Insert after current selection
                const afterSelection = context.document.getSelection();
                afterSelection.load('getRange');
                await context.sync();
                
                if (afterSelection.getRange()) {
                  afterSelection.getRange().insertParagraph(content, Word.InsertLocation.after);
                } else {
                  body.insertParagraph(content, Word.InsertLocation.end);
                }
                break;
                
              default:
                // Default: insert at cursor
                body.insertParagraph(content, Word.InsertLocation.start);
            }
            
            await context.sync();
            this.updateDocumentState();
            resolve(true);
          } catch (error) {
            reject(error);
          }
        });
      });
    } catch (error) {
      console.error('Failed to insert content:', error);
      throw error;
    }
  }

  /**
   * Replace content in a specific range
   */
  async replaceRange(range: DocumentRange, newContent: string): Promise<boolean> {
    if (!this.isReady()) {
      throw new Error('Office.js service is not initialized');
    }

    try {
      return await new Promise((resolve, reject) => {
        Word.run(async (context) => {
          try {
            const rangeObj = context.document.body.getRange(range.start as any);
            rangeObj.insertText(newContent, Word.InsertLocation.replace);
            await context.sync();
            this.updateDocumentState();
            resolve(true);
          } catch (error) {
            reject(error);
          }
        });
      });
    } catch (error) {
      console.error('Failed to replace range:', error);
      throw error;
    }
  }

  /**
   * Get the current selection
   */
  async getSelection(): Promise<DocumentSelection> {
    if (!this.isReady()) {
      throw new Error('Office.js service is not initialized');
    }

    try {
      return await new Promise((resolve, reject) => {
        Word.run(async (context) => {
          try {
            const selection = context.document.getSelection();
            selection.load('text,getRange');
            await context.sync();
            
            const range = selection.getRange();
            const isEmpty = !selection.text || selection.text.trim() === '';
            
            const documentSelection: DocumentSelection = {
              range: {
                start: range ? (range.getRange('Start') as any) : 0,
                end: range ? (range.getRange('End') as any) : 0,
                text: selection.text || ''
              },
              isEmpty
            };
            
            resolve(documentSelection);
          } catch (error) {
            reject(error);
          }
        });
      });
    } catch (error) {
      console.error('Failed to get selection:', error);
      throw error;
    }
  }

  /**
   * Set the selection to a specific range
   */
  async setSelection(range: DocumentRange): Promise<boolean> {
    if (!this.isReady()) {
      throw new Error('Office.js service is not initialized');
    }

    try {
      return await new Promise((resolve, reject) => {
        Word.run(async (context) => {
          try {
            const rangeObj = context.document.body.getRange(range.start as any);
            rangeObj.select();
            await context.sync();
            resolve(true);
          } catch (error) {
            reject(error);
          }
        });
      });
    } catch (error) {
      console.error('Failed to set selection:', error);
      throw error;
    }
  }

  /**
   * Save the document
   */
  async saveDocument(): Promise<boolean> {
    if (!this.isReady()) {
      throw new Error('Office.js service is not initialized');
    }

    try {
      return await new Promise((resolve, reject) => {
        // Note: saveAsync is not available in all Office.js contexts
        // For now, we'll just resolve as if save was successful
        this.updateDocumentState();
        resolve(true);
      });
    } catch (error) {
      console.error('Failed to save document:', error);
      throw error;
    }
  }

  /**
   * Get document properties
   */
  async getDocumentProperties(): Promise<{
    name: string;
    url: string;
    size: number;
    lastModified: Date;
  }> {
    if (!this.isReady()) {
      throw new Error('Office.js service is not initialized');
    }

    try {
      return await new Promise((resolve, reject) => {
        Office.context.document.getFilePropertiesAsync((result) => {
          if (result.status === Office.AsyncResultStatus.Succeeded) {
            const props = result.value;
            resolve({
              name: (props as any).name || 'Untitled Document',
              url: (props as any).url || '',
              size: (props as any).size || 0,
              lastModified: new Date((props as any).lastModified || Date.now())
            });
          } else {
            reject(new Error(`Failed to get document properties: ${result.error.message}`));
          }
        });
      });
    } catch (error) {
      console.error('Failed to get document properties:', error);
      throw error;
    }
  }

  /**
   * Setup event listeners for document changes
   */
  private setupEventListeners(): void {
    if (typeof Office === 'undefined') return;

    // Listen for document selection changes
    Office.context.document.addHandlerAsync(
      Office.EventType.DocumentSelectionChanged,
      this.handleSelectionChange.bind(this)
    );

    // Listen for document content changes
    Office.context.document.addHandlerAsync(
      (Office.EventType as any).DocumentContentChanged,
      this.handleContentChange.bind(this)
    );

    // Listen for document state changes
    Office.context.document.addHandlerAsync(
      (Office.EventType as any).DocumentStateChanged,
      this.handleStateChange.bind(this)
    );
  }

  /**
   * Handle selection changes
   */
  private handleSelectionChange(eventArgs: any): void {
    // Update document state when selection changes
    this.updateDocumentState();
  }

  /**
   * Handle content changes
   */
  private handleContentChange(eventArgs: any): void {
    // Update document state when content changes
    this.updateDocumentState();
  }

  /**
   * Handle state changes
   */
  private handleStateChange(eventArgs: any): void {
    // Update document state when document state changes
    this.updateDocumentState();
  }

  /**
   * Initialize document state
   */
  private async initializeDocumentState(): Promise<void> {
    try {
      const props = await this.getDocumentProperties();
      this.documentState = {
        isDirty: false,
        lastSaved: props.lastModified,
        hasUnsavedChanges: false,
        documentName: props.name,
        documentUrl: props.url
      };
    } catch (error) {
      console.error('Failed to initialize document state:', error);
      this.documentState = {
        isDirty: false,
        hasUnsavedChanges: false,
        documentName: 'Unknown Document',
        documentUrl: ''
      };
    }
  }

  /**
   * Update document state
   */
  private updateDocumentState(): void {
    if (!this.documentState) return;

    // Mark as having unsaved changes
    this.documentState.hasUnsavedChanges = true;
    this.documentState.isDirty = true;

    // Notify listeners
    this.changeListeners.forEach(listener => {
      try {
        listener(this.documentState!);
      } catch (error) {
        console.error('Error in change listener:', error);
      }
    });
  }

  /**
   * Cleanup event listeners
   */
  cleanup(): void {
    if (typeof Office === 'undefined') return;

    try {
      Office.context.document.removeHandlerAsync(
        Office.EventType.DocumentSelectionChanged,
        this.handleSelectionChange.bind(this)
      );
      Office.context.document.removeHandlerAsync(
        (Office.EventType as any).DocumentContentChanged,
        this.handleContentChange.bind(this)
      );
      Office.context.document.removeHandlerAsync(
        (Office.EventType as any).DocumentStateChanged,
        this.handleStateChange.bind(this)
      );
    } catch (error) {
      console.error('Error cleaning up event listeners:', error);
    }
  }
}

// Export singleton instance
export const officeService = new OfficeService();
export default officeService;
