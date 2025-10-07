/**
 * Document Modification Service for Word Add-in
 * Handles paragraph-level document modifications with track changes
 */

export interface DocumentParagraph {
  index: number;
  text: string;
  formatting?: {
    bold?: boolean;
    italic?: boolean;
    font_size?: number;
    font_name?: string;
    color?: string;
  };
}

export interface DocumentModification {
  paragraph_index: number;
  changes: ChangeInstruction[];
}

export interface ChangeInstruction {
  action: 'replace' | 'insert' | 'delete';
  exact_find_text: string;
  replace_text: string;
  reason: string;
}

export interface ModificationResult {
  success: boolean;
  changesApplied: number;
  errors: string[];
}

export class DocumentModificationService {
  private officeIntegrationService: any;

  constructor(officeIntegrationService: any) {
    this.officeIntegrationService = officeIntegrationService;
  }

  /**
   * Get document content as paragraphs with formatting
   */
  async getDocumentParagraphs(): Promise<DocumentParagraph[]> {
    try {
      // Use the proper Office.js paragraph extraction
      const paragraphs = await this.officeIntegrationService.getDocumentParagraphs();
      
      // Convert to our interface format
      const paragraphData: DocumentParagraph[] = paragraphs.map((para: any) => ({
        index: para.index,
        text: para.text,
        formatting: para.formatting || {
          bold: false,
          italic: false,
          font_size: 11,
          font_name: 'Calibri'
        }
      }));
      
      return paragraphData;
    } catch (error) {
      console.error('Failed to get document paragraphs:', error);
      throw new Error(`Failed to get document paragraphs: ${error}`);
    }
  }

  /**
   * Apply modifications with track changes
   */
  async applyModifications(modifications: DocumentModification[]): Promise<ModificationResult> {
    const result: ModificationResult = {
      success: true,
      changesApplied: 0,
      errors: []
    };

    try {
      // Enable track changes
      await this.enableTrackChanges();
      
      // Get current document content for paragraph indexing
      const content = await this.officeIntegrationService.getDocumentContent();
      const paragraphs = content.split(/\n\s*\n/).filter(p => p.trim().length > 0);
      
      for (const modification of modifications) {
        // Validate paragraph index exists
        if (modification.paragraph_index >= paragraphs.length) {
          const error = `Paragraph index ${modification.paragraph_index} not found. Document has ${paragraphs.length} paragraphs.`;
          console.error(error);
          result.errors.push(error);
          continue;
        }
        
        const paragraphText = paragraphs[modification.paragraph_index];
        
        for (const change of modification.changes) {
          try {
            // Search for exact text within the paragraph
            const findIndex = paragraphText.indexOf(change.exact_find_text);
            
            if (findIndex === -1) {
              const error = `Text "${change.exact_find_text}" not found in paragraph ${modification.paragraph_index}`;
              console.error(error);
              result.errors.push(error);
              continue;
            }
            
            // Apply the change using Office.js
            await this.applyChange(change, modification.paragraph_index);
            
            result.changesApplied++;
            
          } catch (changeError) {
            const error = `Failed to apply change in paragraph ${modification.paragraph_index}: ${changeError}`;
            console.error(error);
            result.errors.push(error);
          }
        }
      }
      
    } catch (error) {
      console.error('Failed to apply modifications:', error);
      result.success = false;
      result.errors.push(`Failed to apply modifications: ${error}`);
    }

    return result;
  }

  /**
   * Apply a single change using Office.js
   */
  private async applyChange(change: ChangeInstruction, paragraphIndex: number): Promise<void> {
    return new Promise((resolve, reject) => {
      Word.run(async (context) => {
        try {
          // Get all paragraphs
          const paragraphs = context.document.body.paragraphs;
          paragraphs.load('text');
          await context.sync();
          
          // Get the specific paragraph
          const paragraph = paragraphs.items[paragraphIndex];
          
          // Search for the exact text in the paragraph
          const ranges = paragraph.search(change.exact_find_text, {
            matchCase: false,
            matchWholeWord: true
          });
          
          if (ranges.items.length === 0) {
            throw new Error(`Text "${change.exact_find_text}" not found in paragraph`);
          }
          
          const range = ranges.items[0];
          
          // Apply the change based on action
          switch (change.action) {
            case 'replace':
              range.insertText(change.replace_text, Word.InsertLocation.replace);
              break;
            case 'insert':
              range.insertText(change.replace_text, Word.InsertLocation.after);
              break;
            case 'delete':
              range.insertText('', Word.InsertLocation.replace);
              break;
          }
          
          // Add review comment
          range.insertComment(change.reason);
          
          await context.sync();
          resolve();
          
        } catch (error) {
          reject(error);
        }
      }).catch(reject);
    });
  }

  /**
   * Enable track changes in the document
   */
  private async enableTrackChanges(): Promise<void> {
    try {
      // Note: Office.js doesn't directly control track changes
      // This is a placeholder - user should enable track changes manually
      console.log('Please ensure track changes is enabled in Word for best results');
    } catch (error) {
      console.warn('Could not enable track changes:', error);
    }
  }
}
