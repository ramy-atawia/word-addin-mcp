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
      
      // Validate and convert to our interface format
      const paragraphData: DocumentParagraph[] = paragraphs
        .map((para: any) => this.validateParagraph(para))
        .filter((para): para is DocumentParagraph => para !== null);
      
      if (paragraphData.length === 0) {
        throw new Error('No valid paragraphs found in document');
      }
      
      return paragraphData;
    } catch (error) {
      console.error('Failed to get document paragraphs:', error);
      throw new Error(`Failed to get document paragraphs: ${error}`);
    }
  }

  /**
   * Validate paragraph structure
   */
  private validateParagraph(para: any): DocumentParagraph | null {
    if (!para || typeof para.index !== 'number' || typeof para.text !== 'string') {
      console.warn('Invalid paragraph structure:', para);
      return null;
    }
    
    return {
      index: para.index,
      text: para.text,
      formatting: para.formatting || {
        bold: false,
        italic: false,
        font_size: 11,
        font_name: 'Calibri'
      }
    };
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
      
      // Get current document paragraphs using Office.js
      const paragraphs = await this.officeIntegrationService.getDocumentParagraphs();
      console.log(`Found ${paragraphs.length} paragraphs for modification`);
      
      for (const modification of modifications) {
        console.log(`Processing modification for paragraph ${modification.paragraph_index}`);
        
        // Validate paragraph index exists
        if (modification.paragraph_index >= paragraphs.length) {
          const error = `Paragraph index ${modification.paragraph_index} not found. Document has ${paragraphs.length} paragraphs.`;
          console.error(error);
          result.errors.push(error);
          continue;
        }
        
        const paragraph = paragraphs[modification.paragraph_index];
        console.log(`Paragraph ${modification.paragraph_index} text: "${paragraph.text}"`);
        
        for (const change of modification.changes) {
          try {
            console.log(`Applying change: "${change.exact_find_text}" -> "${change.replace_text}"`);
            
            // Use Office.js search and replace
            console.log(`Calling searchAndReplaceInParagraph with:`);
            console.log(`  paragraphIndex: ${modification.paragraph_index}`);
            console.log(`  findText: "${change.exact_find_text}"`);
            console.log(`  replaceText: "${change.replace_text}"`);
            console.log(`  reason: "${change.reason}"`);
            
            const success = await this.officeIntegrationService.searchAndReplaceInParagraph(
              modification.paragraph_index,
              change.exact_find_text,
              change.replace_text,
              change.reason
            );
            
            console.log(`searchAndReplaceInParagraph returned: ${success}`);
            
            if (success) {
              result.changesApplied++;
              console.log(`Successfully applied change in paragraph ${modification.paragraph_index}`);
            } else {
              const error = `Failed to apply change in paragraph ${modification.paragraph_index}`;
              console.error(error);
              result.errors.push(error);
            }
            
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
