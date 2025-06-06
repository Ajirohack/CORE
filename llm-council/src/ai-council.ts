/**
 * AI Council
 *
 * The central orchestrator for the AI Council architecture that coordinates
 * multiple specialist AI models to process requests and produce comprehensive responses.
 */

import path from "path";
import { EventEmitter } from "events";
import { ConfigManager } from "./config-manager";
import { ModelRegistry } from "./model-registry";
import { SpecialistManager } from "./specialist-manager";
import { ExecutionPlanner } from "./execution-planner";
import { IntegrationLayer } from "./integration-layer";
import { MemoryManager } from "./memory-manager";
import { SharedContext } from "./shared-context";
import { Logger } from "./utils/logger";
import { AICouncilConfig, AICouncilOptions, CouncilResponse } from "./types";

export class AICouncil extends EventEmitter {
  private configManager: ConfigManager;
  private modelRegistry: ModelRegistry;
  private specialistManager: SpecialistManager;
  private executionPlanner: ExecutionPlanner;
  private integrationLayer: IntegrationLayer;
  private memoryManager: MemoryManager;
  private logger: Logger;
  private config: AICouncilConfig | null = null;
  private initialized: boolean = false;

  constructor(private options: AICouncilOptions = {}) {
    super();

    // Initialize the logger
    this.logger = new Logger(options.logLevel || "info");

    // Determine config path
    const configPath =
      options.configPath ||
      path.resolve(process.cwd(), "config", "ai-council.json");

    // Initialize components
    this.configManager = new ConfigManager(configPath);
    this.modelRegistry = new ModelRegistry(this.logger);
    this.specialistManager = new SpecialistManager(
      this.modelRegistry,
      this.logger
    );
    this.executionPlanner = new ExecutionPlanner(
      this.specialistManager,
      this.logger
    );
    this.integrationLayer = new IntegrationLayer(this.logger);
    this.memoryManager = new MemoryManager();
  }

  /**
   * Initialize the AI Council
   */
  async initialize(): Promise<void> {
    if (this.initialized) {
      return;
    }

    try {
      this.logger.info("Initializing AI Council");

      // Initialize the config manager and get the config
      await this.configManager.initialize();
      this.config = this.configManager.getConfig();

      // Initialize the model registry
      await this.modelRegistry.initialize(this.config);

      // Initialize the specialist manager
      await this.specialistManager.initialize(this.config);

      // Initialize the memory manager
      await this.memoryManager.initialize(this.config);

      this.initialized = true;
      this.logger.info("AI Council initialized successfully");
      this.emit("initialized");
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error";
      this.logger.error("Failed to initialize AI Council", {
        error: errorMessage,
      });
      throw error;
    }
  }

  /**
   * Process a request and generate a response
   */
  async processRequest(request: {
    input: string;
    userId?: string;
    sessionId?: string;
    attachments?: any[];
    context?: any;
  }): Promise<CouncilResponse> {
    if (!this.initialized) {
      await this.initialize();
    }

    this.logger.info("Processing request", {
      userId: request.userId,
      sessionId: request.sessionId,
      inputLength: request.input.length,
    });

    const startTime = Date.now();

    try {
      // Create a shared context for this request
      const sharedContext = new SharedContext(request, {
        userId: request.userId,
        sessionId: request.sessionId,
        timestamp: Date.now(),
      });

      // Load relevant memory into context
      if (this.config?.memory?.enabled) {
        await this.loadMemoryIntoContext(sharedContext);
      }

      // Create an execution plan for this request
      const executionPlan = await this.executionPlanner.createPlan(
        request,
        sharedContext
      );

      // Execute the specialists
      const results = await this.executeSpecialists(
        executionPlan,
        sharedContext
      );

      // Integrate the results
      const response = await this.integrationLayer.integrate(
        results,
        sharedContext
      );

      // Store the interaction in memory
      if (this.config?.memory?.enabled) {
        await this.storeInteractionInMemory(request, response, sharedContext);
      }

      const processingTime = Date.now() - startTime;

      this.logger.info("Request processed successfully", {
        processingTime,
        specialistsUsed: results.length,
      });

      // Add processing time to metadata
      response.metadata = {
        ...response.metadata,
        totalProcessingTime: processingTime,
      };

      this.emit("request:processed", {
        processingTime,
        specialistsUsed: results.length,
      });

      return response;
    } catch (error: unknown) {
      const processingTime = Date.now() - startTime;
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error";

      this.logger.error("Error processing request", {
        error: errorMessage,
        processingTime,
      });

      this.emit("request:error", {
        error: errorMessage,
        processingTime,
      });

      throw error;
    }
  }

  /**
   * Execute specialists according to the execution plan
   */
  private async executeSpecialists(
    executionPlan: any,
    sharedContext: SharedContext
  ): Promise<any[]> {
    const results: any[] = [];
    const pendingSteps = [...executionPlan.steps];

    // Sort steps by priority (lower runs first)
    pendingSteps.sort(
      (a: any, b: any) => (a.priority || 1) - (b.priority || 1)
    );

    // Execute steps in order
    for (const step of pendingSteps) {
      // Check if all dependencies have been executed
      if (step.dependsOn && step.dependsOn.length > 0) {
        const dependenciesMet = step.dependsOn.every((dependencyId: string) =>
          results.some((result) => result.specialistId === dependencyId)
        );

        if (!dependenciesMet) {
          // Skip this step for now, will be handled by dependencySpecialists
          continue;
        }
      }

      // Execute the specialist
      try {
        // Update the input with the latest context if needed
        const input = sharedContext.prepareSpecialistInput(step.specialistId, {
          phase: step.phase,
        });

        // Execute the specialist
        const result = await this.specialistManager.executeSpecialist(
          step.specialistId,
          input,
          sharedContext
        );

        // Store the result
        results.push(result);

        this.logger.debug(`Executed specialist ${step.specialistId}`);
      } catch (error: unknown) {
        const errorMessage =
          error instanceof Error ? error.message : "Unknown error";
        this.logger.error(`Failed to execute specialist ${step.specialistId}`, {
          error: errorMessage,
        });
      }
    }

    // Execute integration specialist if present
    if (executionPlan.integrationStep) {
      try {
        // Update the input with the latest context
        const input = sharedContext.prepareSpecialistInput("integration", {
          phase: executionPlan.integrationStep.phase,
          additionalContext: { specialistResults: results },
        });

        // Execute the integration specialist
        const result = await this.specialistManager.executeSpecialist(
          "integration",
          input,
          sharedContext
        );

        // Store the result
        results.push(result);

        this.logger.debug("Executed integration specialist");
      } catch (error: unknown) {
        const errorMessage =
          error instanceof Error ? error.message : "Unknown error";
        this.logger.error("Failed to execute integration specialist", {
          error: errorMessage,
        });
      }
    }

    return results;
  }

  /**
   * Load relevant memory into the context
   */
  private async loadMemoryIntoContext(
    sharedContext: SharedContext
  ): Promise<void> {
    try {
      const { userId, sessionId } = sharedContext.metadata;

      // Load working memory for the session
      if (sessionId) {
        const workingMemory = this.memoryManager.getWorkingMemory(sessionId);
        sharedContext.setMemory("working", workingMemory);
      }

      // Load episodic memory for the user
      if (userId) {
        const episodicMemory = this.memoryManager.getEpisodicMemory(userId);
        sharedContext.setMemory("episodic", episodicMemory);
      }

      // Load semantic memory based on the request content
      if (sharedContext.originalRequest.input) {
        const semanticMemory = this.memoryManager.getSemanticMemory(
          sharedContext.originalRequest.input
        );
        sharedContext.setMemory("semantic", semanticMemory);
      }
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error";
      this.logger.error("Failed to load memory into context", {
        error: errorMessage,
      });
    }
  }

  /**
   * Store the interaction in memory
   */
  private async storeInteractionInMemory(
    request: any,
    response: CouncilResponse,
    sharedContext: SharedContext
  ): Promise<void> {
    try {
      const { userId, sessionId } = sharedContext.metadata;

      if (!userId && !sessionId) {
        return; // No user or session to store memory for
      }

      // Store the request and response as a working memory
      await this.memoryManager.storeMemory({
        type: "working",
        userId,
        sessionId,
        content: {
          request: request.input,
          response: response.response,
        },
        priority: 1, // High priority for recent interactions
        expiry: Date.now() + 24 * 60 * 60 * 1000, // Expires in 24 hours
      });

      // For important interactions, also store as episodic memory
      if (this.isImportantInteraction(request, response)) {
        await this.memoryManager.storeMemory({
          type: "episodic",
          userId,
          sessionId,
          content: {
            request: request.input,
            response: response.response,
            timestamp: Date.now(),
            importance: "high",
          },
          priority: 2, // Higher priority for important interactions
          // No expiry for episodic memories
        });
      }

      // For specific knowledge, store semantic memory
      if (this.containsSemanticKnowledge(request, response)) {
        await this.memoryManager.storeMemory({
          type: "semantic",
          content: this.extractSemanticKnowledge(request, response),
          priority: 3, // Highest priority for semantic knowledge
          // No expiry for semantic memories
        });
      }
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error";
      this.logger.error("Failed to store interaction in memory", {
        error: errorMessage,
      });
    }
  }

  /**
   * Check if an interaction is important
   */
  private isImportantInteraction(
    request: any,
    response: CouncilResponse
  ): boolean {
    // Implement logic to determine if an interaction is important
    // For now, use a simple heuristic based on length and content

    const input = request.input;
    const output = response.response;

    // Long interactions are more likely to be important
    if (input.length > 200 && output.length > 500) {
      return true;
    }

    // Interactions with specific keywords are important
    const importantKeywords = [
      "remember",
      "important",
      "critical",
      "don't forget",
      "preference",
      "always",
      "never",
      "name is",
      "my",
    ];

    for (const keyword of importantKeywords) {
      if (input.toLowerCase().includes(keyword.toLowerCase())) {
        return true;
      }
    }

    return false;
  }

  /**
   * Check if an interaction contains semantic knowledge
   */
  private containsSemanticKnowledge(
    request: any,
    response: CouncilResponse
  ): boolean {
    // Implement logic to determine if an interaction contains semantic knowledge
    // This would normally use NLP to extract entities, facts, etc.

    // For now, use a simple heuristic
    const input = request.input.toLowerCase();
    const output = response.response.toLowerCase();

    // Questions seeking factual information
    if (
      input.includes("what is") ||
      input.includes("how does") ||
      input.includes("explain")
    ) {
      return true;
    }

    // Responses containing factual statements
    if (
      output.includes("is a") ||
      output.includes("are") ||
      output.includes("defined as") ||
      output.includes("consists of")
    ) {
      return true;
    }

    return false;
  }

  /**
   * Extract semantic knowledge from an interaction
   */
  private extractSemanticKnowledge(
    request: any,
    response: CouncilResponse
  ): any {
    // This would normally use NLP to extract entities, facts, etc.
    // For now, return a simplified representation

    return {
      question: request.input,
      answer: response.response,
      extractedAt: Date.now(),
    };
  }

  /**
   * Get the configuration
   */
  getConfig(): AICouncilConfig | null {
    return this.config;
  }

  /**
   * Update the configuration
   */
  async updateConfig(config: Partial<AICouncilConfig>): Promise<void> {
    if (!this.initialized) {
      await this.initialize();
    }

    await this.configManager.updateConfig(config);
    this.config = this.configManager.getConfig();

    // Reinitialize components with the new config
    await this.modelRegistry.initialize(this.config);
    await this.specialistManager.initialize(this.config);
    await this.memoryManager.initialize(this.config);

    this.emit("config:updated");
  }

  /**
   * Register a new specialist
   */
  async registerSpecialist(specialist: any): Promise<void> {
    if (!this.initialized) {
      await this.initialize();
    }

    await this.specialistManager.registerSpecialist(specialist);
  }

  /**
   * Shutdown the AI Council
   */
  async shutdown(): Promise<void> {
    this.logger.info("Shutting down AI Council");

    // Shutdown memory manager
    await this.memoryManager.shutdown();

    this.initialized = false;
    this.emit("shutdown");
  }
}

// Export the AICouncil class as the default export
export default AICouncil;
