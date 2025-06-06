/**
 * AI Council main entry point
 *
 * The AI Council orchestrates multiple specialized AI models to work together,
 * maintains shared context, and implements the "unified consciousness" pattern.
 */

import { EventEmitter } from 'events';
import { ModelRegistry } from './model-registry';
import { CouncilOrchestrator } from './council-orchestrator';
import { SharedContext } from './shared-context';
import { SpecialistManager } from './specialist-manager';
import { MemoryManager } from './memory-manager';
import { ExecutionPlanner } from './execution-planner';
import { IntegrationLayer } from './integration-layer';
import { ConfigManager } from './config-manager';
import { Logger } from './utils/logger';

export interface AICouncilOptions {
  configPath?: string;
  modelsPath?: string;
  logger?: Logger;
}

export class AICouncil extends EventEmitter {
  private modelRegistry: ModelRegistry;
  private orchestrator: CouncilOrchestrator;
  private specialistManager: SpecialistManager;
  private memoryManager: MemoryManager;
  private executionPlanner: ExecutionPlanner;
  private integrationLayer: IntegrationLayer;
  private configManager: ConfigManager;
  private logger: Logger;
  private initialized: boolean = false;

  constructor(options: AICouncilOptions = {}) {
    super();

    // Initialize components
    this.logger = options.logger || new Logger({ module: 'ai-council' });
    this.configManager = new ConfigManager(options.configPath || './config/ai-council.json');
    this.modelRegistry = new ModelRegistry(this.logger);
    this.memoryManager = new MemoryManager();
    this.specialistManager = new SpecialistManager(this.modelRegistry, this.logger);
    this.executionPlanner = new ExecutionPlanner(this.specialistManager, this.logger);
    this.integrationLayer = new IntegrationLayer(this.logger);

    // Initialize orchestrator with all components
    this.orchestrator = new CouncilOrchestrator({
      modelRegistry: this.modelRegistry,
      specialistManager: this.specialistManager,
      memoryManager: this.memoryManager,
      executionPlanner: this.executionPlanner,
      integrationLayer: this.integrationLayer,
      logger: this.logger,
    });

    // Forward orchestrator events
    this.orchestrator.on('execution:start', data => this.emit('execution:start', data));
    this.orchestrator.on('execution:complete', data => this.emit('execution:complete', data));
    this.orchestrator.on('execution:error', error => this.emit('execution:error', error));
    this.orchestrator.on('specialist:start', data => this.emit('specialist:start', data));
    this.orchestrator.on('specialist:complete', data => this.emit('specialist:complete', data));
  }

  /**
   * Initialize the AI Council
   */
  async initialize(): Promise<void> {
    if (this.initialized) {
      return;
    }

    this.logger.info('Initializing AI Council');

    try {
      // Load configuration
      await this.configManager.initialize();

      // Initialize model registry
      await this.modelRegistry.initialize(this.configManager.getConfig());

      // Initialize specialist manager with model registry
      await this.specialistManager.initialize(this.configManager.getConfig());

      // Initialize memory manager
      await this.memoryManager.initialize();

      // Initialize orchestrator
      await this.orchestrator.initialize(this.configManager.getConfig());

      this.initialized = true;
      this.logger.info('AI Council initialized successfully');
      this.emit('initialized');
    } catch (error) {
      this.logger.error('Failed to initialize AI Council', error);
      throw error;
    }
  }

  /**
   * Process a request through the AI Council
   *
   * This is the main entry point for processing requests through the AI Council.
   */
  async processRequest(request: {
    input: string;
    context?: Record<string, any>;
    tools?: any[];
    attachments?: any[];
    userId?: string;
    sessionId?: string;
    options?: Record<string, any>;
  }): Promise<{
    response: string;
    metadata: Record<string, any>;
  }> {
    if (!this.initialized) {
      await this.initialize();
    }

    this.logger.debug('Processing request through AI Council', {
      userId: request.userId,
      inputLength: request.input.length,
      hasAttachments: request.attachments?.length > 0,
    });

    try {
      // Create a shared context for this request
      const sharedContext = new SharedContext({
        originalRequest: request,
        userId: request.userId,
        sessionId: request.sessionId || this.generateSessionId(request),
        context: request.context || {},
      });

      // Process the request through the orchestrator
      const result = await this.orchestrator.process(request, sharedContext);

      // Emit success event
      this.emit('request:complete', {
        userId: request.userId,
        sessionId: sharedContext.sessionId,
        processingTime: result.metadata.processingTime,
      });

      return result;
    } catch (error) {
      // Emit error event
      this.emit('request:error', {
        userId: request.userId,
        error: error.message,
      });

      this.logger.error('Error processing request', error);
      throw error;
    }
  }

  /**
   * Get available models in the registry
   */
  getAvailableModels(): any[] {
    return this.modelRegistry.getAvailableModels();
  }

  /**
   * Register a new model with the council
   */
  async registerModel(modelConfig: any): Promise<void> {
    await this.modelRegistry.registerModel(modelConfig);

    // If the model is a specialist, register it with the specialist manager
    if (modelConfig.specialization) {
      await this.specialistManager.registerSpecialist({
        id: modelConfig.id || modelConfig.name.toLowerCase().replace(/\s+/g, '-'),
        name: modelConfig.name,
        specialization: modelConfig.specialization,
        modelId: modelConfig.id || modelConfig.name.toLowerCase().replace(/\s+/g, '-'),
        priority: modelConfig.priority || 1,
      });
    }
  }

  /**
   * Generate a session ID for a request
   */
  private generateSessionId(request: any): string {
    const userId = request.userId || 'anonymous';
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 10);

    return `${userId}-${timestamp}-${random}`;
  }

  /**
   * Shut down the AI Council
   */
  async shutdown(): Promise<void> {
    this.logger.info('Shutting down AI Council');

    try {
      // Shut down components in reverse initialization order
      await this.orchestrator.shutdown();
      await this.memoryManager.shutdown();
      await this.modelRegistry.shutdown();

      this.logger.info('AI Council shut down successfully');
    } catch (error) {
      this.logger.error('Error shutting down AI Council', error);
      throw error;
    }
  }
}

// Export additional classes and types
export * from './model-registry';
export * from './council-orchestrator';
export * from './shared-context';
export * from './specialist-manager';
export * from './memory-manager';
export * from './execution-planner';
export * from './integration-layer';
export * from './types';
