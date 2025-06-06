/**
 * Base Document Processor
 *
 * Defines the interface and common functionality for document processors in the RAG System
 */

const { createLogger } = require("../../../utils/logger");
const logger = createLogger("BaseDocumentProcessor");

class BaseDocumentProcessor {
  /**
   * Initialize the document processor
   * @param {Object} options - Configuration options
   */
  constructor(options = {}) {
    this.options = {
      // Default options
      addTimestamp: true,
      addSourceInfo: true,
      generateIds: true,
      ...options,
    };
  }

  /**
   * Process a document
   * @param {Object} document - Document to process
   * @param {string} document.content - Document content
   * @param {Object} document.metadata - Document metadata
   * @returns {Promise<Object>} - Processed document
   */
  async process(document) {
    if (!document || !document.content) {
      throw new Error("Invalid document: document must have content");
    }

    try {
      // Initialize metadata if not present
      if (!document.metadata) {
        document.metadata = {};
      }

      // Pre-processing
      await this.preProcess(document);

      // Core processing
      const processedDocument = await this.processDocument(document);

      // Post-processing
      await this.postProcess(processedDocument);

      return processedDocument;
    } catch (error) {
      logger.error(`Error processing document: ${error.message}`, { error });
      throw error;
    }
  }

  /**
   * Pre-processing steps
   * @param {Object} document - Document to pre-process
   * @returns {Promise<void>}
   */
  async preProcess(document) {
    // Add timestamp if configured
    if (this.options.addTimestamp) {
      document.metadata.processedAt = new Date().toISOString();
    }

    // Add document ID if configured
    if (this.options.generateIds && !document.metadata.id) {
      document.metadata.id = this._generateDocumentId();
    }

    // Subclasses should override this method for additional pre-processing
  }

  /**
   * Core document processing - this must be implemented by subclasses
   * @param {Object} document - Document to process
   * @returns {Promise<Object>} - Processed document
   */
  async processDocument(document) {
    // Base implementation does nothing, should be overridden by subclasses
    return document;
  }

  /**
   * Post-processing steps
   * @param {Object} document - Document to post-process
   * @returns {Promise<void>}
   */
  async postProcess(document) {
    // Subclasses should override this method for post-processing
  }

  /**
   * Generate a unique document ID
   * @returns {string} - Unique document ID
   * @private
   */
  _generateDocumentId() {
    return `doc_${Date.now()}_${Math.random().toString(36).substring(2, 10)}`;
  }
}

module.exports = BaseDocumentProcessor;
