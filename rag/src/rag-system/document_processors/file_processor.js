/**
 * File Document Processor
 *
 * Processes file-based documents for the RAG System
 */

const fs = require("fs").promises;
const path = require("path");
const { TextLoader } = require("langchain/document_loaders/fs/text");
const { CSVLoader } = require("langchain/document_loaders/fs/csv");
const { PDFLoader } = require("langchain/document_loaders/fs/pdf");
const { DocxLoader } = require("langchain/document_loaders/fs/docx");
const { JSONLoader } = require("langchain/document_loaders/fs/json");
const { MarkdownLoader } = require("langchain/document_loaders/fs/markdown");

const BaseDocumentProcessor = require("./base");
const TextProcessor = require("./text_processor");
const { createLogger } = require("../../../utils/logger");
const { NotFoundError } = require("../../../utils/errors");

const logger = createLogger("FileProcessor");

class FileProcessor extends BaseDocumentProcessor {
  /**
   * Initialize the file document processor
   * @param {Object} options - Configuration options
   * @param {Object} options.textProcessorOptions - Options to pass to the TextProcessor
   * @param {boolean} options.extractMetadata - Whether to extract metadata from files
   * @param {Array<string>} options.supportedExtensions - List of supported file extensions
   */
  constructor(options = {}) {
    super(options);

    this.options = {
      ...this.options,
      textProcessorOptions: options.textProcessorOptions || {},
      extractMetadata: options.extractMetadata !== false,
      supportedExtensions: options.supportedExtensions || [
        ".txt",
        ".md",
        ".pdf",
        ".docx",
        ".csv",
        ".json",
      ],
    };

    // Initialize text processor for processing extracted text
    this.textProcessor = new TextProcessor(this.options.textProcessorOptions);
  }

  /**
   * Process a file
   * @param {string} filePath - Path to the file to process
   * @returns {Promise<Array<Object>>} - Array of document chunks
   */
  async processFile(filePath) {
    logger.debug(`Processing file: ${filePath}`);

    try {
      // Check if file exists
      await fs.access(filePath);

      // Get file stats
      const stats = await fs.stat(filePath);

      // Extract file metadata
      const metadata = await this._extractFileMetadata(filePath, stats);

      // Load file content
      const content = await this._loadFileContent(filePath, metadata.extension);

      // Create document object
      const document = {
        content,
        metadata,
      };

      // Process the document
      return await this.process(document);
    } catch (error) {
      if (error.code === "ENOENT") {
        throw new NotFoundError(`File not found: ${filePath}`);
      }
      logger.error(`Error processing file ${filePath}: ${error.message}`, {
        error,
      });
      throw error;
    }
  }

  /**
   * Override the process method to handle file-specific processing
   * @param {Object} document - Document to process
   * @returns {Promise<Array<Object>>} - Array of document chunks
   */
  async process(document) {
    if (!document.metadata.extension) {
      throw new Error("Invalid document: missing file extension in metadata");
    }

    // Process with parent method
    return await super.process(document);
  }

  /**
   * Process document through text processor
   * @param {Object} document - Document to process
   * @returns {Promise<Array<Object>>} - Array of document chunks
   */
  async processDocument(document) {
    // TextProcessor will handle the chunking
    return await this.textProcessor.process(document);
  }

  /**
   * Extract metadata from a file
   * @param {string} filePath - Path to the file
   * @param {Object} stats - File stats
   * @returns {Promise<Object>} - File metadata
   * @private
   */
  async _extractFileMetadata(filePath, stats) {
    const parsedPath = path.parse(filePath);

    const metadata = {
      source: filePath,
      filename: parsedPath.base,
      extension: parsedPath.ext.toLowerCase(),
      directory: parsedPath.dir,
      fileSize: stats.size,
      created: stats.birthtime,
      modified: stats.mtime,
    };

    // Check if file extension is supported
    metadata.supported = this.options.supportedExtensions.includes(
      metadata.extension
    );

    return metadata;
  }

  /**
   * Load content from a file
   * @param {string} filePath - Path to the file
   * @param {string} extension - File extension
   * @returns {Promise<string>} - File content
   * @private
   */
  async _loadFileContent(filePath, extension) {
    let loader;
    let content = "";

    // Select appropriate loader based on file extension
    switch (extension.toLowerCase()) {
      case ".txt":
        loader = new TextLoader(filePath);
        break;
      case ".csv":
        loader = new CSVLoader(filePath);
        break;
      case ".pdf":
        loader = new PDFLoader(filePath);
        break;
      case ".docx":
        loader = new DocxLoader(filePath);
        break;
      case ".json":
        loader = new JSONLoader(filePath, "/text");
        break;
      case ".md":
        loader = new MarkdownLoader(filePath);
        break;
      default:
        // Default to text loader
        loader = new TextLoader(filePath);
    }

    try {
      // Load documents
      const docs = await loader.load();

      // Combine all document pages/parts into a single text
      content = docs.map((doc) => doc.pageContent).join("\n\n");
    } catch (error) {
      logger.error(`Error loading file ${filePath}: ${error.message}`, {
        error,
      });

      // Fall back to loading as plain text
      try {
        content = await fs.readFile(filePath, "utf-8");
        logger.debug(`Loaded ${filePath} as plain text after loader failed`);
      } catch (fallbackError) {
        throw new Error(`Failed to load file ${filePath}: ${error.message}`);
      }
    }

    return content;
  }
}

module.exports = FileProcessor;
