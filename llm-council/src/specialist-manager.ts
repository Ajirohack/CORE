/**
 * Specialist Manager for AI Council
 *
 * This component manages the registration and execution of specialist models
 * that are part of the AI Council.
 */

import { EventEmitter } from 'events';
import * as fs from 'fs/promises';
import * as path from 'path';
import { Specialist, AICouncilConfig, SpecialistTool } from './types';
import { ModelRegistry } from './model-registry';
import { Logger } from './utils/logger';
import { SharedContext } from './shared-context';

export interface SpecialistManagerOptions {
  modelsPath?: string;
}

export class SpecialistManager extends EventEmitter {
  private specialists: Map<string, Specialist> = new Map();
  private specialistPrompts: Map<string, string> = new Map();
  private modelRegistry: ModelRegistry;
  private logger: Logger;
  private initialized: boolean = false;

  constructor(
    modelRegistry: ModelRegistry,
    logger: Logger,
    options: SpecialistManagerOptions = {}
  ) {
    super();
    this.modelRegistry = modelRegistry;
    this.logger = logger;
  }

  /**
   * Initialize the specialist manager
   */
  async initialize(config: AICouncilConfig): Promise<void> {
    if (this.initialized) {
      return;
    }

    this.logger.info('Initializing specialist manager');

    try {
      // Clear any existing specialists
      this.specialists.clear();

      // Register specialists from configuration
      await this.registerSpecialistsFromConfig(config);

      // Load specialist prompts
      await this.loadSpecialistPrompts();

      this.initialized = true;
      this.logger.info(`Specialist manager initialized with ${this.specialists.size} specialists`);
      this.emit('initialized', { specialistCount: this.specialists.size });
    } catch (error) {
      this.logger.error('Failed to initialize specialist manager', error);
      throw error;
    }
  }

  /**
   * Register specialists from configuration
   */
  private async registerSpecialistsFromConfig(config: AICouncilConfig): Promise<void> {
    // Register specialists from config
    for (const [specialistType, specialistConfig] of Object.entries(config.specialists)) {
      if (!specialistConfig.enabled) {
        continue;
      }

      // Get a reference to the model from the registry
      const modelConfigs = this.modelRegistry.findModelsByProvider(
        this.getProviderFromModel(specialistConfig.model)
      );

      if (modelConfigs.length === 0) {
        this.logger.warn(`No model found for specialist ${specialistType}`);
        continue;
      }

      // Find the exact model or use the first one from the provider
      const modelConfig =
        modelConfigs.find(model => model.modelId === specialistConfig.model) || modelConfigs[0];

      // Register one or more instances of this specialist type
      const count = specialistConfig.count || 1;
      for (let i = 0; i < count; i++) {
        const id = count > 1 ? `${specialistType}-${i + 1}` : specialistType;

        await this.registerSpecialist({
          id,
          name: this.capitalizeFirstLetter(specialistType) + (count > 1 ? ` ${i + 1}` : ''),
          specialization: specialistType,
          modelId: modelConfig.id,
          systemPrompt: specialistConfig.systemPrompt,
          enabled: true,
          parameters: {
            temperature: specialistConfig.temperature,
            maxTokens: specialistConfig.maxTokens,
          },
        });
      }
    }
  }

  /**
   * Load specialist prompts from files
   */
  private async loadSpecialistPrompts(): Promise<void> {
    const promptsDir = path.resolve(__dirname, '../prompts');

    try {
      await fs.access(promptsDir);

      // Read all files in the prompts directory
      const files = await fs.readdir(promptsDir);

      for (const file of files) {
        if (file.endsWith('.prompt')) {
          const specialistType = file.replace('.prompt', '');
          const promptPath = path.join(promptsDir, file);
          const promptText = await fs.readFile(promptPath, 'utf-8');

          this.specialistPrompts.set(specialistType, promptText);
          this.logger.debug(`Loaded prompt for specialist ${specialistType}`);
        }
      }
    } catch (error) {
      this.logger.warn('Failed to load specialist prompts', error);
      // Continue without prompts - will use defaults
    }
  }

  /**
   * Register a new specialist
   */
  async registerSpecialist(specialist: Partial<Specialist>): Promise<void> {
    try {
      if (!specialist.id) {
        throw new Error('Specialist ID is required');
      }

      // Ensure the specialist has a reference to a valid model
      if (specialist.modelId) {
        const model = this.modelRegistry.getModel(specialist.modelId);
        if (!model) {
          throw new Error(`Model ${specialist.modelId} not found in registry`);
        }
      } else {
        throw new Error('Model ID is required for specialist');
      }

      // Create a complete specialist object with defaults
      const completeSpecialist: Specialist = {
        id: specialist.id,
        name: specialist.name || specialist.id,
        specialization: specialist.specialization || 'general',
        modelId: specialist.modelId,
        systemPrompt:
          specialist.systemPrompt ||
          this.getDefaultSystemPrompt(specialist.specialization || 'general'),
        tools: specialist.tools || [],
        weight: specialist.weight || 1,
        priority: specialist.priority || 1,
        enabled: specialist.enabled !== false,
        requiredCapabilities: specialist.requiredCapabilities || [],
        parameters: specialist.parameters || {},
      };

      this.specialists.set(completeSpecialist.id, completeSpecialist);

      this.logger.debug(
        `Registered specialist ${completeSpecialist.id} (${completeSpecialist.specialization})`
      );
      this.emit('specialist:registered', { id: completeSpecialist.id });
    } catch (error) {
      this.logger.error(`Failed to register specialist ${specialist.id}`, error);
      throw error;
    }
  }

  /**
   * Get default system prompt for a specialist type
   */
  private getDefaultSystemPrompt(specialization: string): string {
    // Try to get prompt from loaded prompts
    const prompt = this.specialistPrompts.get(specialization);
    if (prompt) {
      return prompt;
    }

    // Default prompts for different specialist types
    switch (specialization) {
      case 'text':
        return `You are the Text Specialist in the AI Council. Your role is to:
1. Process and interpret natural language text from users
2. Generate high-quality, contextually appropriate text responses
3. Handle nuances of language including idioms, cultural references, and implied meanings
4. Ensure grammatical accuracy and appropriate tone in all text generation
5. Format text appropriately for its intended purpose`;

      case 'reasoning':
        return `You are the Reasoning Specialist in the AI Council. Your role is to:
1. Apply formal logic and structured reasoning to problems
2. Identify logical fallacies or inconsistencies in arguments
3. Develop step-by-step processes for solving problems
4. Evaluate the validity of conclusions based on given premises
5. Distinguish between correlation and causation in data analysis`;

      case 'thinking':
        return `You are the Thinking Specialist in the AI Council. Your role is to:
1. Analyze complex problems requiring deep thought
2. Consider multiple perspectives and potential approaches
3. Evaluate trade-offs between different solutions
4. Generate creative connections and novel ideas
5. Structure complex conceptual frameworks`;

      case 'multimodal':
        return `You are the Multimodal Specialist in the AI Council. Your role is to:
1. Process and interpret content across different modalities (text, images, audio, etc.)
2. Generate specifications for multimodal outputs
3. Create connections between information in different formats
4. Translate concepts between modalities effectively
5. Ensure coherence across different types of content`;

      default:
        return `You are a specialist in the AI Council with expertise in ${specialization}. 
Analyze the user's request and provide your specialized insights.`;
    }
  }

  /**
   * Get a specialist by ID
   */
  getSpecialist(specialistId: string): Specialist | undefined {
    return this.specialists.get(specialistId);
  }

  /**
   * Get all specialists
   */
  getSpecialists(): Specialist[] {
    return Array.from(this.specialists.values());
  }

  /**
   * Get enabled specialists
   */
  getEnabledSpecialists(): Specialist[] {
    return Array.from(this.specialists.values()).filter(specialist => specialist.enabled);
  }

  /**
   * Get specialists by specialization
   */
  getSpecialistsBySpecialization(specialization: string): Specialist[] {
    return this.getEnabledSpecialists().filter(
      specialist => specialist.specialization.toLowerCase() === specialization.toLowerCase()
    );
  }

  /**
   * Execute a specialist on input
   */
  async executeSpecialist(
    specialistId: string,
    input: any,
    sharedContext: SharedContext
  ): Promise<any> {
    const specialist = this.getSpecialist(specialistId);

    if (!specialist) {
      throw new Error(`Specialist ${specialistId} not found`);
    }

    if (!specialist.enabled) {
      throw new Error(`Specialist ${specialistId} is disabled`);
    }

    const startTime = Date.now();
    this.logger.debug(`Executing specialist ${specialistId}`, {
      input: typeof input === 'string' ? input.length : 'object',
    });

    try {
      // Get the model adapter from the registry
      const modelAdapter = this.modelRegistry.getModelAdapter(specialist.modelId);

      if (!modelAdapter) {
        throw new Error(`Model adapter for ${specialist.modelId} not found`);
      }

      // Prepare the execution context with system prompt and parameters
      const executionContext = {
        systemPrompt: specialist.systemPrompt,
        parameters: {
          ...specialist.parameters,
        },
        tools: specialist.tools,
      };

      // Execute the model
      const result = await modelAdapter.execute(input, executionContext);

      const processingTime = Date.now() - startTime;

      // Record the result in the shared context
      sharedContext.addResult(specialistId, result);

      this.logger.debug(`Specialist ${specialistId} execution completed in ${processingTime}ms`);
      this.emit('specialist:executed', {
        id: specialistId,
        processingTime,
        success: true,
      });

      return {
        specialistId,
        result,
        processingTime,
        confidence: result.confidence || 1.0,
        metadata: {
          specialist: {
            id: specialist.id,
            name: specialist.name,
            specialization: specialist.specialization,
          },
          model: specialist.modelId,
        },
      };
    } catch (error) {
      const processingTime = Date.now() - startTime;

      this.logger.error(`Failed to execute specialist ${specialistId}`, error);
      this.emit('specialist:executed', {
        id: specialistId,
        processingTime,
        success: false,
        error: error.message,
      });

      throw error;
    }
  }

  /**
   * Enable a specialist
   */
  enableSpecialist(specialistId: string): boolean {
    const specialist = this.specialists.get(specialistId);

    if (specialist) {
      specialist.enabled = true;
      this.emit('specialist:updated', { id: specialistId, enabled: true });
      return true;
    }

    return false;
  }

  /**
   * Disable a specialist
   */
  disableSpecialist(specialistId: string): boolean {
    const specialist = this.specialists.get(specialistId);

    if (specialist) {
      specialist.enabled = false;
      this.emit('specialist:updated', { id: specialistId, enabled: false });
      return true;
    }

    return false;
  }

  /**
   * Update specialist parameters
   */
  updateSpecialistParameters(specialistId: string, parameters: Record<string, any>): boolean {
    const specialist = this.specialists.get(specialistId);

    if (specialist) {
      specialist.parameters = {
        ...specialist.parameters,
        ...parameters,
      };
      this.emit('specialist:updated', { id: specialistId, parameters });
      return true;
    }

    return false;
  }

  /**
   * Update specialist system prompt
   */
  updateSpecialistSystemPrompt(specialistId: string, systemPrompt: string): boolean {
    const specialist = this.specialists.get(specialistId);

    if (specialist) {
      specialist.systemPrompt = systemPrompt;
      this.emit('specialist:updated', { id: specialistId, systemPrompt });
      return true;
    }

    return false;
  }

  /**
   * Register a tool for a specialist
   */
  registerSpecialistTool(specialistId: string, tool: SpecialistTool): boolean {
    const specialist = this.specialists.get(specialistId);

    if (!specialist) {
      return false;
    }

    if (!specialist.tools) {
      specialist.tools = [];
    }

    // Remove any existing tool with the same name
    specialist.tools = specialist.tools.filter(t => t.name !== tool.name);

    // Add the new tool
    specialist.tools.push(tool);

    this.emit('specialist:tool:registered', { specialistId, toolName: tool.name });

    return true;
  }

  /**
   * Unregister a tool from a specialist
   */
  unregisterSpecialistTool(specialistId: string, toolName: string): boolean {
    const specialist = this.specialists.get(specialistId);

    if (!specialist || !specialist.tools) {
      return false;
    }

    const initialLength = specialist.tools.length;
    specialist.tools = specialist.tools.filter(t => t.name !== toolName);

    if (specialist.tools.length < initialLength) {
      this.emit('specialist:tool:unregistered', { specialistId, toolName });
      return true;
    }

    return false;
  }

  /**
   * Helper: Extract provider from model ID
   */
  private getProviderFromModel(modelId: string): string {
    if (modelId.startsWith('gpt-')) return 'openai';
    if (modelId.startsWith('claude-')) return 'anthropic';
    if (modelId.startsWith('mistral-')) return 'mistral';
    if (modelId.startsWith('gemini-')) return 'google';

    // For other models, assume the provider is the first part of the model ID
    const parts = modelId.split('-');
    if (parts.length > 1) {
      return parts[0];
    }

    return 'unknown';
  }

  /**
   * Helper: Capitalize first letter of a string
   */
  private capitalizeFirstLetter(str: string): string {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }
}
