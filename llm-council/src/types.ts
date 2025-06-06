/**
 * Type definitions for AI Council
 *
 * Contains the core interfaces and types used across the AI Council module.
 */

/**
 * Configuration options for the AI Council
 */
export interface AICouncilConfig {
  /**
   * Module configuration
   */
  module: {
    name: string;
    version: string;
    description?: string;
  };

  /**
   * Memory system configuration
   */
  memory?: {
    enabled: boolean;
    storage?: {
      type: "local" | "redis" | "mongodb" | "custom";
      options?: Record<string, any>;
    };
    limits?: {
      maxWorkingMemorySize: number;
      maxEpisodicMemorySize: number;
      maxSemanticMemorySize: number;
    };
  };

  /**
   * Model registry configuration
   */
  models: {
    defaultProvider: string;
    providers: {
      [provider: string]: {
        apiKey?: string;
        apiEndpoint?: string;
        apiVersion?: string;
        options?: Record<string, any>;
      };
    };
    defaults: {
      embedding: string;
      chat: string;
      completion: string;
    };
  };

  /**
   * Specialist configuration
   */
  specialists: {
    [specialistId: string]: {
      name: string;
      description?: string;
      model: string;
      systemPrompt?: string;
      temperature?: number;
      maxTokens?: number;
      capabilities?: string[];
      domains?: string[];
      contextWindow?: number;
      enabled: boolean;
      options?: Record<string, any>;
    };
  };

  /**
   * Security configuration
   */
  security?: {
    rateLimit?: {
      enabled: boolean;
      requestsPerMinute: number;
    };
    contentFilters?: {
      enabled: boolean;
      filterTypes: ("toxicity" | "hate" | "sexual" | "violence")[];
    };
  };

  /**
   * Logging configuration
   */
  logging?: {
    level: "debug" | "info" | "warn" | "error";
    storage?: {
      enabled: boolean;
      type: "local" | "cloud" | "custom";
      options?: Record<string, any>;
    };
  };
}

/**
 * Represents a response from the AI Council
 */
export interface CouncilResponse {
  response: string;
  metadata?: Record<string, any>;
}

/**
 * Represents the result of a specialist execution
 */
export interface SpecialistResult {
  specialistId: string;
  result: any;
  confidence?: number;
  processingTime: number;
  metadata?: Record<string, any>;
}

/**
 * Represents a specialist model
 */
export interface Specialist {
  id: string;
  name: string;
  description?: string;
  capabilities: string[];
  domains: string[];

  // Additional properties required by execution-planner
  specialization?: string;
  priority?: number;
  modelId?: string;
  enabled?: boolean;

  /**
   * Execute the specialist with the given input
   */
  execute(input: any, context: any): Promise<SpecialistResult>;

  /**
   * Check if the specialist can handle a given request
   */
  canHandle?(request: any): Promise<{
    can: boolean;
    confidence?: number;
    reason?: string;
  }>;
}

/**
 * Represents an execution plan for processing a request
 */
export interface ExecutionPlan {
  requestId?: string;
  steps: ExecutionStep[];
  integrationStep?: ExecutionStep;
  context?: any; // Add this property to fix type errors
}

/**
 * Represents a step in an execution plan
 */
export interface ExecutionStep {
  specialistId: string;
  phase: ProcessingPhase; // Use our newly defined type
  priority?: number;
  dependsOn?: string[];
  input?: any; // Add this property to fix type errors
  options?: Record<string, any>; // Add options property
}

/**
 * Represents a memory item
 */
export interface MemoryItem {
  id?: string;
  type: "working" | "episodic" | "semantic";
  userId?: string;
  sessionId?: string;
  content: any;
  priority?: number;
  timestamp?: number;
  expiry?: number;
  metadata?: Record<string, any>;
}

/**
 * Represents a processing phase in the AI Council execution flow
 */
export type ProcessingPhase =
  | "analysis"
  | "processing"
  | "generation"
  | "refinement"
  | "integration";

/**
 * Constructor options for the AI Council
 */
export interface AICouncilOptions {
  configPath?: string;
  logLevel?: "debug" | "info" | "warn" | "error";
}
