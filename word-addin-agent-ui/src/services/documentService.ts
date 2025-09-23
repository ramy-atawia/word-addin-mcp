export interface TransformationChange {
  action: 'replace' | 'add' | 'remove';
  find: string;
  replaceWith: string;
  reason: string;
}

export interface TransformationPlan {
  changes: TransformationChange[];
  summary: string;
  estimatedImpact: 'low' | 'medium' | 'high';
}

export interface TransformationResult {
  success: boolean;
  message: string;
  changesApplied: number;
  errors?: string[];
}

export class DocumentService {
  /**
   * Get the current document content as text
   */
  async getDocumentContent(): Promise<string> {
    return new Promise((resolve, reject) => {
      Word.run(async (context) => {
        try {
          const paragraphs = context.document.body.paragraphs;
          paragraphs.load('text');
          await context.sync();
          
          const content = paragraphs.items.map(p => p.text).join('\n');
          resolve(content);
        } catch (error) {
          reject(new Error(`Failed to get document content: ${error}`));
        }
      });
    });
  }

  /**
   * Apply a transformation plan to the document
   */
  async applyTransformation(plan: TransformationPlan): Promise<TransformationResult> {
    return new Promise((resolve, reject) => {
      Word.run(async (context) => {
        try {
          const result: TransformationResult = {
            success: true,
            message: 'Transformation completed successfully',
            changesApplied: 0,
            errors: []
          };

          // Process each change in the plan
          for (const change of plan.changes) {
            try {
              await this.executeChange(context, change);
              result.changesApplied++;
            } catch (error) {
              const errorMsg = `Failed to apply change: ${change.reason} - ${error}`;
              result.errors = result.errors || [];
              result.errors.push(errorMsg);
              console.error(errorMsg);
            }
          }

          // Check if we had any errors
          if (result.errors && result.errors.length > 0) {
            result.success = false;
            result.message = `Transformation completed with ${result.errors.length} errors`;
          }

          await context.sync();
          resolve(result);
        } catch (error) {
          reject(new Error(`Failed to apply transformation: ${error}`));
        }
      });
    });
  }

  /**
   * Execute a single transformation change
   */
  private async executeChange(context: Word.RequestContext, change: TransformationChange): Promise<void> {
    switch (change.action) {
      case 'replace':
        await this.replaceText(context, change.find, change.replaceWith);
        break;
      case 'add':
        await this.addText(context, change.replaceWith);
        break;
      case 'remove':
        await this.removeText(context, change.find);
        break;
      default:
        throw new Error(`Unsupported action: ${change.action}`);
    }
  }

  /**
   * Replace text in the document
   */
  private async replaceText(context: Word.RequestContext, findText: string, replaceText: string): Promise<void> {
    if (!findText.trim()) {
      throw new Error('Find text cannot be empty');
    }

    const body = context.document.body;
    body.load('text');
    await context.sync();
    
    const text = body.text;
    
    // Check if the text to find exists
    if (!text.includes(findText)) {
      throw new Error(`Text to find not found: "${findText}"`);
    }
    
    const newText = text.replace(new RegExp(this.escapeRegExp(findText), 'gi'), replaceText);
    body.insertText(newText, Word.InsertLocation.replace);
  }

  /**
   * Add new text to the end of the document
   */
  async addText(text: string): Promise<void> {
    if (!text.trim()) {
      throw new Error('Text to add cannot be empty');
    }

    return new Promise((resolve, reject) => {
      Word.run(async (context) => {
        try {
          const body = context.document.body;
          body.insertParagraph(text, Word.InsertLocation.end);
          await context.sync();
          resolve();
        } catch (error) {
          reject(new Error(`Failed to add text: ${error}`));
        }
      });
    });
  }

  /**
   * Remove text from the document
   */
  private async removeText(context: Word.RequestContext, textToRemove: string): Promise<void> {
    if (!textToRemove.trim()) {
      throw new Error('Text to remove cannot be empty');
    }

    const body = context.document.body;
    body.load('text');
    await context.sync();
    
    const text = body.text;
    
    // Check if the text to remove exists
    if (!text.includes(textToRemove)) {
      throw new Error(`Text to remove not found: "${textToRemove}"`);
    }
    
    const newText = text.replace(new RegExp(this.escapeRegExp(textToRemove), 'gi'), '');
    body.insertText(newText, Word.InsertLocation.replace);
  }

  /**
   * Escape special characters in regex patterns
   */
  private escapeRegExp(string: string): string {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  /**
   * Get document statistics
   */
  async getDocumentStats(): Promise<{ paragraphs: number; characters: number; words: number }> {
    return new Promise((resolve, reject) => {
      Word.run(async (context) => {
        try {
          const paragraphs = context.document.body.paragraphs;
          paragraphs.load('text');
          await context.sync();
          
          const content = paragraphs.items.map(p => p.text).join('\n');
          const words = content.split(/\s+/).filter(word => word.length > 0).length;
          
          resolve({
            paragraphs: paragraphs.items.length,
            characters: content.length,
            words: words
          });
        } catch (error) {
          reject(new Error(`Failed to get document stats: ${error}`));
        }
      });
    });
  }

  /**
   * Check if document is empty
   */
  async isDocumentEmpty(): Promise<boolean> {
    try {
      const content = await this.getDocumentContent();
      return !content.trim();
    } catch (error) {
      console.error('Error checking if document is empty:', error);
      return true;
    }
  }

  /**
   * Create a backup of the current document state
   */
  async createBackup(): Promise<string> {
    try {
      const content = await this.getDocumentContent();
      const timestamp = new Date().toISOString();
      const backup = {
        timestamp,
        content,
        stats: await this.getDocumentStats()
      };
      
      // Store backup in localStorage (simple approach for Phase 1)
      const backupKey = `document_backup_${timestamp}`;
      localStorage.setItem(backupKey, JSON.stringify(backup));
      
      return backupKey;
    } catch (error) {
      throw new Error(`Failed to create backup: ${error}`);
    }
  }

  /**
   * Restore document from backup
   */
  async restoreFromBackup(backupKey: string): Promise<void> {
    try {
      const backupData = localStorage.getItem(backupKey);
      if (!backupData) {
        throw new Error('Backup not found');
      }
      
      const backup = JSON.parse(backupData);
      
      return new Promise((resolve, reject) => {
        Word.run(async (context) => {
          try {
            const body = context.document.body;
            body.insertText(backup.content, Word.InsertLocation.replace);
            await context.sync();
            resolve();
          } catch (error) {
            reject(new Error(`Failed to restore document: ${error}`));
          }
        });
      });
    } catch (error) {
      throw new Error(`Failed to restore from backup: ${error}`);
    }
  }
}
