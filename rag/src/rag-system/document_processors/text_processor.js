/**
 * Text Document Processor
 *
 * Processes text documents for the RAG System
 */

const { RecursiveCharacterTextSplitter } = require("langchain/text_splitter");
const BaseDocumentProcessor = require("./base");
const { createLogger } = require("../../../utils/logger");

const logger = createLogger("TextProcessor");

class TextProcessor extends BaseDocumentProcessor {
  /**
   * Initialize the text document processor
   * @param {Object} options - Configuration options
   * @param {number} options.chunkSize - Size of chunks to split text into
   * @param {number} options.chunkOverlap - Overlap between chunks
   * @param {boolean} options.normalizeLine - Normalize line endings
   * @param {boolean} options.removeExtraWhitespace - Remove extra whitespace
   */
  constructor(options = {}) {
    super(options);

    this.options = {
      ...this.options,
      chunkSize: options.chunkSize || 1000,
      chunkOverlap: options.chunkOverlap || 200,
      normalizeLine: options.normalizeLine !== false,
      removeExtraWhitespace: options.removeExtraWhitespace !== false,
    };

    // Initialize text splitter
    this.textSplitter = new RecursiveCharacterTextSplitter({
      chunkSize: this.options.chunkSize,
      chunkOverlap: this.options.chunkOverlap,
    });
  }

  /**
   * Pre-process text document
   * @param {Object} document - Document to pre-process
   * @returns {Promise<void>}
   */
  async preProcess(document) {
    await super.preProcess(document);

    // Add content type metadata
    document.metadata.contentType = "text";

    // Normalize text if configured
    if (this.options.normalizeLine) {
      document.content = this._normalizeLineEndings(document.content);
    }

    // Remove extra whitespace if configured
    if (this.options.removeExtraWhitespace) {
      document.content = this._removeExtraWhitespace(document.content);
    }
  }

  /**
   * Process text document
   * @param {Object} document - Document to process
   * @returns {Promise<Array<Object>>} - Array of document chunks
   */
  async processDocument(document) {
    logger.debug(
      `Processing text document: ${document.metadata.id || "unknown"}`
    );

    // Split text into chunks
    const textChunks = await this.textSplitter.splitText(document.content);

    // Create document chunks
    const documentChunks = textChunks.map((chunk, index) => {
      return {
        content: chunk,
        metadata: {
          ...document.metadata,
          chunk: index,
          totalChunks: textChunks.length,
        },
      };
    });

    logger.debug(`Text document split into ${documentChunks.length} chunks`);
    return documentChunks;
  }

  /**
   * Post-process text document chunks
   * @param {Array<Object>} documentChunks - Document chunks to post-process
   * @returns {Promise<void>}
   */
  async postProcess(documentChunks) {
    // Calculate statistics
    if (Array.isArray(documentChunks) && documentChunks.length > 0) {
      const totalLength = documentChunks.reduce(
        (sum, chunk) => sum + chunk.content.length,
        0
      );
      const avgChunkLength = Math.round(totalLength / documentChunks.length);

      logger.debug(
        `Post-processing complete: ${documentChunks.length} chunks, avg length: ${avgChunkLength}`
      );

      // Add statistics to each chunk
      documentChunks.forEach((chunk) => {
        chunk.metadata.chunkLength = chunk.content.length;
        chunk.metadata.avgChunkLength = avgChunkLength;
      });
    }
  }

  /**
   * Normalize line endings in text
   * @param {string} text - Text to normalize
   * @returns {string} - Text with normalized line endings
   * @private
   */
  _normalizeLineEndings(text) {
    return text.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  }

  /**
   * Remove extra whitespace in text
   * @param {string} text - Text to clean
   * @returns {string} - Cleaned text
   * @private
   */
  _removeExtraWhitespace(text) {
    return text
      .replace(/[ \t]+/g, " ") // Replace multiple spaces/tabs with single space
      .replace(/\n{3,}/g, "\n\n") // Replace 3+ newlines with 2
      .trim();
  }
}

module.exports = TextProcessor;
