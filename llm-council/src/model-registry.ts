/**
 * Model Registry for AI Council
 *
 * Manages the registration and access to AI models used by the council.
 * Provides methods for model registration, retrieval, and validation.
 */

import { EventEmitter } from "events";
import { Logger } from "./utils/logger";

export interface ModelDefinition {
  id: string;
  name: string;
  provider: string;
  endpoint?: string;
  apiKey?: string;
  modelType: "embedding" | "completion" | "vision" | "specialist" | "custom";
  contextWindow?: number;
  maxTokens?: number;
  properties?: Record<string, any>;
  capabilities?: string[];
  metadata?: Record<string, any>;
}

export interface ModelInstance {
  definition: ModelDefinition;
  instance: any; // The actual model instance or client
}

export class ModelRegistry extends EventEmitter {
  private logger: Logger;
  private models: Map<string, ModelInstance> = new Map();
  private modelsByProvider: Map<string, ModelDefinition[]> = new Map();
  private modelsByType: Map<string, ModelDefinition[]> = new Map();

  constructor(logger?: Logger) {
    super();
    this.logger = logger || new Logger("ModelRegistry");
    this.logger.info("Model Registry initialized");
  }

  /**
   * Initialize the model registry with configuration
   * @param config Configuration for model registry
   */
  async initialize(config: any): Promise<void> {
    this.logger.info("Initializing Model Registry with provided configuration");

    try {
      // Process model configurations from the provided config
      if (config?.models) {
        // Register default models from configuration
        const { models } = config;

        this.logger.debug(
          `Processing ${
            Object.keys(models.providers || {}).length
          } provider configurations`
        );

        // Additional initialization logic would go here
      }
    } catch (error) {
      this.logger.error("Failed to initialize Model Registry", {
        error: error instanceof Error ? error.message : "Unknown error",
      });
      throw error;
    }
  }

  /**
   * Initialize the model registry with configuration
   * @param config Configuration for model registry
   */
  async initialize(config: any): Promise<void> {
    this.logger.info("Initializing Model Registry with provided configuration");

    try {
      // Process model configurations from the provided config
      if (config?.models) {
        // Register default models from configuration
        const { models } = config;

        this.logger.debug(
          `Processing ${
            Object.keys(models.providers || {}).length
          } provider configurations`
        );

        // Additional initialization logic would go here
      }
    } catch (error) {
      this.logger.error("Failed to initialize Model Registry", {
        error: error instanceof Error ? error.message : "Unknown error",
      });
      throw error;
    }
  }

  /**
   * Register a new model in the registry
   *
   * @param definition The model definition
   * @param instance The actual model instance (e.g., OpenAI client, local model)
   * @returns The registered model instance
   */
  registerModel(definition: ModelDefinition, instance: any): ModelInstance {
    // Validate the model definition
    this.validateModelDefinition(definition);

    // Create the model instance
    const modelInstance: ModelInstance = {
      definition,
      instance,
    };

    // Register the model
    this.models.set(definition.id, modelInstance);

    // Add to provider index
    if (!this.modelsByProvider.has(definition.provider)) {
      this.modelsByProvider.set(definition.provider, []);
    }
    this.modelsByProvider.get(definition.provider)?.push(definition);

    // Add to type index
    if (!this.modelsByType.has(definition.modelType)) {
      this.modelsByType.set(definition.modelType, []);
    }
    this.modelsByType.get(definition.modelType)?.push(definition);

    // Log the registration
    this.logger.info(
      `Model registered: ${definition.id} (${definition.name}) - ${definition.provider}`
    );

    // Emit event
    this.emit("model:registered", definition.id, definition);

    return modelInstance;
  }

  /**
   * Validate a model definition
   *
   * @param definition The model definition to validate
   * @throws Error if the definition is invalid
   */
  private validateModelDefinition(definition: ModelDefinition): void {
    if (!definition.id) {
      throw new Error("Model ID is required");
    }

    if (this.models.has(definition.id)) {
      throw new Error(`Model with ID ${definition.id} already exists`);
    }

    if (!definition.name) {
      throw new Error("Model name is required");
    }

    if (!definition.provider) {
      throw new Error("Model provider is required");
    }

    if (!definition.modelType) {
      throw new Error("Model type is required");
    }

    // Validate model type
    const validModelTypes = [
      "embedding",
      "completion",
      "vision",
      "specialist",
      "custom",
    ];
    if (!validModelTypes.includes(definition.modelType)) {
      throw new Error(
        `Invalid model type: ${
          definition.modelType
        }. Valid types are: ${validModelTypes.join(", ")}`
      );
    }
  }

  /**
   * Get a model by ID
   *
   * @param id The model ID
   * @returns The model instance or undefined if not found
   */
  getModel(id: string): ModelInstance | undefined {
    return this.models.get(id);
  }

  /**
   * Get all models
   *
   * @returns An array of all model instances
   */
  getAllModels(): ModelInstance[] {
    return Array.from(this.models.values());
  }

  /**
   * Get models by provider
   *
   * @param provider The provider name
   * @returns An array of model definitions for the provider
   */
  getModelsByProvider(provider: string): ModelDefinition[] {
    return this.modelsByProvider.get(provider) || [];
  }

  /**
   * Get models by type
   *
   * @param modelType The model type
   * @returns An array of model definitions for the type
   */
  getModelsByType(modelType: string): ModelDefinition[] {
    return this.modelsByType.get(modelType) || [];
  }

  /**
   * Find models by capability
   *
   * @param capability The capability to search for
   * @returns An array of model definitions with the capability
   */
  findModelsByCapability(capability: string): ModelDefinition[] {
    const result: ModelDefinition[] = [];

    for (const modelInstance of this.models.values()) {
      const { capabilities } = modelInstance.definition;

      if (capabilities && capabilities.includes(capability)) {
        result.push(modelInstance.definition);
      }
    }

    return result;
  }

  /**
   * Check if a model exists by ID
   *
   * @param id The model ID
   * @returns true if the model exists, false otherwise
   */
  hasModel(id: string): boolean {
    return this.models.has(id);
  }

  /**
   * Remove a model from the registry
   *
   * @param id The model ID
   * @returns true if the model was removed, false otherwise
   */
  removeModel(id: string): boolean {
    const model = this.models.get(id);

    if (!model) {
      return false;
    }

    // Remove from main registry
    this.models.delete(id);

    // Remove from provider index
    const providerModels = this.modelsByProvider.get(model.definition.provider);
    if (providerModels) {
      const index = providerModels.findIndex((m) => m.id === id);
      if (index !== -1) {
        providerModels.splice(index, 1);
      }
    }

    // Remove from type index
    const typeModels = this.modelsByType.get(model.definition.modelType);
    if (typeModels) {
      const index = typeModels.findIndex((m) => m.id === id);
      if (index !== -1) {
        typeModels.splice(index, 1);
      }
    }

    // Log the removal
    this.logger.info(`Model removed: ${id}`);

    // Emit event
    this.emit("model:removed", id, model.definition);

    return true;
  }

  /**
   * Update a model's definition
   *
   * @param id The model ID
   * @param updates Partial model definition updates
   * @returns The updated model instance or undefined if not found
   */
  updateModel(
    id: string,
    updates: Partial<ModelDefinition>
  ): ModelInstance | undefined {
    const model = this.models.get(id);

    if (!model) {
      return undefined;
    }

    // Create updated definition
    const updatedDefinition: ModelDefinition = {
      ...model.definition,
      ...updates,
    };

    // Remove old model
    this.removeModel(id);

    // Register with updated definition
    return this.registerModel(updatedDefinition, model.instance);
  }

  /**
   * Get the count of registered models
   *
   * @returns The number of registered models
   */
  get modelCount(): number {
    return this.models.size;
  }

  /**
   * Clear all models from the registry
   */
  clear(): void {
    this.models.clear();
    this.modelsByProvider.clear();
    this.modelsByType.clear();
    this.logger.info("Model Registry cleared");
  }
}
