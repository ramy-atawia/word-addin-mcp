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
        
        // Validate modifications array
        if (!modifications || !Array.isArray(modifications)) {
            result.success = false;
            result.errors.push('Invalid modifications array provided');
            return result;
        }
        
        if (modifications.length === 0) {
            result.errors.push('No modifications to apply');
            return result;
        }
        
        console.log(`Applying ${modifications.length} modifications`);

        try {
            // Enable track changes
            await this.enableTrackChanges();
            
            // Get current document paragraphs using Office.js
            let paragraphs;
            try {
              paragraphs = await this.officeIntegrationService.getDocumentParagraphs();
            } catch (officeError) {
              console.error('Office.js error getting paragraphs:', officeError);
              throw new Error(`Office.js failed to get paragraphs: ${officeError}`);
            }
            
            // Validate paragraphs array
            if (!paragraphs || !Array.isArray(paragraphs)) {
              console.error('Invalid paragraphs response:', paragraphs);
              throw new Error('Failed to get document paragraphs: Invalid response from Office.js');
            }
            
            console.log(`Successfully got ${paragraphs.length} paragraphs from Office.js`);
      
      for (const modification of modifications) {
        
        // Validate paragraph index exists
        if (modification.paragraph_index >= paragraphs.length) {
          const error = `Paragraph index ${modification.paragraph_index} not found. Document has ${paragraphs.length} paragraphs.`;
          result.errors.push(error);
          continue;
        }
        
        const paragraph = paragraphs[modification.paragraph_index];
        
        for (const change of modification.changes) {
          try {
            const success = await this.officeIntegrationService.searchAndReplaceInParagraph(
              modification.paragraph_index,
              change.exact_find_text,
              change.replace_text,
              change.reason
            );
            
            if (success) {
              result.changesApplied++;
            } else {
              const error = `Failed to apply change in paragraph ${modification.paragraph_index}`;
              result.errors.push(error);
            }
          } catch (changeError) {
            const error = `Failed to apply change in paragraph ${modification.paragraph_index}: ${changeError}`;
            result.errors.push(error);
          }
        }
      }
      
    } catch (error) {
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
    } catch (error) {
      // Track changes enablement is optional
    }
  }
}
