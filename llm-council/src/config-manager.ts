/**
 * Configuration Manager for AI Council
 *
 * This component loads, validates, and provides access to the AI Council configuration.
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { AICouncilConfig } from './types';

export class ConfigManager {
  private configPath: string;
  private config: AICouncilConfig | null = null;
  private defaultConfig: AICouncilConfig = {
    decisionMaker: {
      model: 'gpt-4',
      temperature: 0.7,
      maxTokens: 2000,
    },
    specialists: {
      text: {
        enabled: true,
        model: 'gpt-3.5-turbo',
        temperature: 0.7,
        maxTokens: 1000,
      },
      reasoning: {
        enabled: true,
        model: 'claude-3-sonnet',
        temperature: 0.2,
        maxTokens: 3000,
      },
      thinking: {
        enabled: true,
        model: 'claude-3-opus',
        temperature: 0.5,
        maxTokens: 4000,
      },
      multimodal: {
        enabled: true,
        model: 'gpt-4-vision',
        temperature: 0.7,
        maxTokens: 2000,
      },
    },
    memory: {
      enabled: true,
      persistenceEnabled: false,
    },
    providers: {
      openai: {
        apiKey: process.env.OPENAI_API_KEY,
      },
      anthropic: {
        apiKey: process.env.ANTHROPIC_API_KEY,
      },
    },
  };

  constructor(configPath: string) {
    this.configPath = configPath;
  }

  /**
   * Initialize configuration manager by loading config
   */
  async initialize(): Promise<void> {
    try {
      // Check if config file exists
      try {
        await fs.access(this.configPath);
      } catch (error) {
        // Create directory if it doesn't exist
        const configDir = path.dirname(this.configPath);
        try {
          await fs.mkdir(configDir, { recursive: true });
        } catch (mkdirError) {
          // Ignore if directory already exists
        }

        // Create default config file
        await fs.writeFile(this.configPath, JSON.stringify(this.defaultConfig, null, 2));
      }

      // Load config file
      const configData = await fs.readFile(this.configPath, 'utf-8');
      const loadedConfig = JSON.parse(configData);

      // Merge with default config to ensure all required fields exist
      this.config = this.mergeConfigs(this.defaultConfig, loadedConfig);

      // Apply environment variable overrides
      this.applyEnvironmentOverrides();

      // Validate config
      this.validateConfig(this.config);
    } catch (error) {
      console.error('Failed to initialize config manager:', error);
      // Fall back to default config
      this.config = this.defaultConfig;
      throw error;
    }
  }

  /**
   * Get the loaded configuration
   */
  getConfig(): AICouncilConfig {
    if (!this.config) {
      return this.defaultConfig;
    }
    return this.config;
  }

  /**
   * Update configuration
   */
  async updateConfig(newConfig: Partial<AICouncilConfig>): Promise<void> {
    if (!this.config) {
      this.config = this.defaultConfig;
    }

    // Merge new config with existing config
    this.config = this.mergeConfigs(this.config, newConfig);

    // Validate config
    this.validateConfig(this.config);

    // Save config to file
    await fs.writeFile(this.configPath, JSON.stringify(this.config, null, 2));
  }

  /**
   * Merge configs, with second config overriding values in first config
   */
  private mergeConfigs(baseConfig: any, overrideConfig: any): any {
    // Create a deep copy of the base config
    const result = JSON.parse(JSON.stringify(baseConfig));

    // Helper function to recursively merge objects
    const mergeObjects = (target: any, source: any) => {
      Object.keys(source).forEach(key => {
        if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
          // If property is an object and exists in target, merge recursively
          if (!target[key]) target[key] = {};
          mergeObjects(target[key], source[key]);
        } else {
          // Otherwise, override the target property
          target[key] = source[key];
        }
      });
    };

    // Merge the override config into the result
    mergeObjects(result, overrideConfig);

    return result;
  }

  /**
   * Apply environment variable overrides to the config
   */
  private applyEnvironmentOverrides(): void {
    if (!this.config) return;

    // Override provider API keys with environment variables
    Object.keys(this.config.providers).forEach(provider => {
      const envKey = `${provider.toUpperCase()}_API_KEY`;
      if (process.env[envKey]) {
        this.config!.providers[provider].apiKey = process.env[envKey];
      }
    });

    // Override other config values as needed
    if (process.env.AI_COUNCIL_MEMORY_ENABLED) {
      this.config.memory.enabled = process.env.AI_COUNCIL_MEMORY_ENABLED === 'true';
    }

    if (process.env.AI_COUNCIL_MEMORY_PERSISTENCE_ENABLED) {
      this.config.memory.persistenceEnabled =
        process.env.AI_COUNCIL_MEMORY_PERSISTENCE_ENABLED === 'true';
    }

    if (process.env.AI_COUNCIL_MEMORY_PERSISTENCE_PATH) {
      this.config.memory.persistencePath = process.env.AI_COUNCIL_MEMORY_PERSISTENCE_PATH;
    }
  }

  /**
   * Validate the configuration
   */
  private validateConfig(config: AICouncilConfig): void {
    // Check decision maker configuration
    if (!config.decisionMaker) {
      throw new Error('AI Council configuration must include a decisionMaker section');
    }

    if (!config.decisionMaker.model) {
      throw new Error('AI Council configuration must include a model for the decision maker');
    }

    // Check that at least one specialist is enabled
    let hasEnabledSpecialist = false;
    for (const specialist of Object.values(config.specialists)) {
      if (specialist.enabled) {
        hasEnabledSpecialist = true;
        break;
      }
    }

    if (!hasEnabledSpecialist) {
      throw new Error('AI Council configuration must have at least one enabled specialist');
    }

    // Check that required providers are configured
    const requiredProviders = new Set<string>();

    // Add decision maker provider
    const decisionMakerProvider = this.getProviderFromModel(config.decisionMaker.model);
    if (decisionMakerProvider) {
      requiredProviders.add(decisionMakerProvider);
    }

    // Add specialists providers
    for (const specialist of Object.values(config.specialists)) {
      if (specialist.enabled) {
        const specialistProvider = this.getProviderFromModel(specialist.model);
        if (specialistProvider) {
          requiredProviders.add(specialistProvider);
        }
      }
    }

    // Check that all required providers are configured
    for (const provider of requiredProviders) {
      if (!config.providers[provider]) {
        throw new Error(`Provider '${provider}' is required but not configured`);
      }

      if (!config.providers[provider].apiKey) {
        throw new Error(`API key for provider '${provider}' is required but not configured`);
      }
    }
  }

  /**
   * Extract provider name from model ID
   */
  private getProviderFromModel(modelId: string): string | null {
    if (modelId.startsWith('gpt-')) return 'openai';
    if (modelId.startsWith('claude-')) return 'anthropic';
    if (modelId.startsWith('mistral-')) return 'mistral';
    if (modelId.startsWith('gemini-')) return 'google';

    // For other models, assume the provider is the first part of the model ID
    const parts = modelId.split('-');
    if (parts.length > 1) {
      return parts[0];
    }

    return null;
  }
}
