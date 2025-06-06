/**
 * Shared Context for AI Council
 *
 * Maintains a shared state between different specialists during request processing.
 * Provides methods for accessing and manipulating the context data.
 */

import { v4 as uuidv4 } from 'uuid';

export class SharedContext {
  /**
   * Unique identifier for this context
   */
  public readonly id: string;

  /**
   * Original request that initiated this context
   */
  public readonly originalRequest: any;

  /**
   * Metadata about the context
   */
  public readonly metadata: {
    userId?: string;
    sessionId?: string;
    timestamp: number;
    [key: string]: any;
  };

  /**
   * Map of specialist results
   */
  private specialistResults: Map<string, any> = new Map();

  /**
   * Map of memory data
   */
  private memoryData: Map<string, any> = new Map();

  /**
   * Map of context variables
   */
  private variables: Map<string, any> = new Map();

  /**
   * Processing history
   */
  private processingHistory: {
    timestamp: number;
    phase: string;
    specialistId?: string;
    action: string;
    data?: any;
  }[] = [];

  constructor(
    request: any,
    metadata: {
      userId?: string;
      sessionId?: string;
      timestamp?: number;
      [key: string]: any;
    } = {}
  ) {
    this.id = uuidv4();
    this.originalRequest = request;
    this.metadata = {
      ...metadata,
      timestamp: metadata.timestamp || Date.now(),
    };

    // Initialize with request context if provided
    if (request.context) {
      this.initializeFromRequestContext(request.context);
    }

    // Record creation in history
    this.addToHistory('system', 'context:created');
  }

  /**
   * Initialize context from the request context
   */
  private initializeFromRequestContext(requestContext: any): void {
    if (typeof requestContext !== 'object') {
      return;
    }

    // Import variables from request context
    if (requestContext.variables) {
      for (const [key, value] of Object.entries(requestContext.variables)) {
        this.setVariable(key, value);
      }
    }

    // Import memory data if provided
    if (requestContext.memory) {
      for (const [type, data] of Object.entries(requestContext.memory)) {
        this.setMemory(type, data);
      }
    }
  }

  /**
   * Prepare input for a specialist with relevant context
   */
  prepareSpecialistInput(
    specialistId: string,
    options: {
      phase?: string;
      includeMemory?: boolean;
      includeVariables?: boolean;
      includeHistory?: boolean;
      additionalContext?: any;
    } = {}
  ): any {
    const phase = options.phase || 'processing';

    // Add to history
    this.addToHistory(phase, 'specialist:input:prepared', specialistId);

    // Start with the original input
    const input = {
      ...this.originalRequest,
      contextId: this.id,
      metadata: { ...this.metadata },
    };

    // Add memory data if requested
    if (options.includeMemory !== false) {
      input.memory = {};
      for (const [type, data] of this.memoryData.entries()) {
        input.memory[type] = data;
      }
    }

    // Add variables if requested
    if (options.includeVariables !== false) {
      input.variables = {};
      for (const [key, value] of this.variables.entries()) {
        input.variables[key] = value;
      }
    }

    // Add processing history if requested
    if (options.includeHistory) {
      input.processingHistory = [...this.processingHistory];
    }

    // Add other specialist results if needed
    const specialistResults: Record<string, any> = {};
    for (const [id, result] of this.specialistResults.entries()) {
      if (id !== specialistId) {
        specialistResults[id] = result;
      }
    }

    if (Object.keys(specialistResults).length > 0) {
      input.specialistResults = specialistResults;
    }

    // Add any additional context
    if (options.additionalContext) {
      input.additionalContext = options.additionalContext;
    }

    return input;
  }

  /**
   * Set a specialist result in the context
   */
  setSpecialistResult(specialistId: string, result: any): void {
    this.specialistResults.set(specialistId, result);
    this.addToHistory('processing', 'specialist:result:stored', specialistId, {
      resultType: typeof result,
      timestamp: Date.now(),
    });
  }

  /**
   * Get a specialist result from the context
   */
  getSpecialistResult(specialistId: string): any {
    return this.specialistResults.get(specialistId);
  }

  /**
   * Get all specialist results
   */
  getAllSpecialistResults(): Map<string, any> {
    return new Map(this.specialistResults);
  }

  /**
   * Set memory data
   */
  setMemory(type: string, data: any): void {
    this.memoryData.set(type, data);
    this.addToHistory('memory', 'memory:stored', undefined, {
      type,
      timestamp: Date.now(),
    });
  }

  /**
   * Get memory data
   */
  getMemory(type: string): any {
    return this.memoryData.get(type);
  }

  /**
   * Get all memory data
   */
  getAllMemory(): Map<string, any> {
    return new Map(this.memoryData);
  }

  /**
   * Set a context variable
   */
  setVariable(key: string, value: any): void {
    this.variables.set(key, value);
  }

  /**
   * Get a context variable
   */
  getVariable(key: string): any {
    return this.variables.get(key);
  }

  /**
   * Check if a variable exists
   */
  hasVariable(key: string): boolean {
    return this.variables.has(key);
  }

  /**
   * Get all variables
   */
  getAllVariables(): Map<string, any> {
    return new Map(this.variables);
  }

  /**
   * Add an entry to the processing history
   */
  addToHistory(phase: string, action: string, specialistId?: string, data?: any): void {
    this.processingHistory.push({
      timestamp: Date.now(),
      phase,
      specialistId,
      action,
      data,
    });
  }

  /**
   * Get the processing history
   */
  getHistory(): any[] {
    return [...this.processingHistory];
  }

  /**
   * Create a snapshot of the context
   */
  createSnapshot(): any {
    return {
      id: this.id,
      timestamp: Date.now(),
      metadata: { ...this.metadata },
      specialistResults: Object.fromEntries(this.specialistResults),
      memoryData: Object.fromEntries(this.memoryData),
      variables: Object.fromEntries(this.variables),
      processingHistory: [...this.processingHistory],
    };
  }

  /**
   * Apply a snapshot to restore context
   */
  applySnapshot(snapshot: any): void {
    if (!snapshot) {
      return;
    }

    // Restore specialist results
    if (snapshot.specialistResults) {
      for (const [id, result] of Object.entries(snapshot.specialistResults)) {
        this.specialistResults.set(id, result);
      }
    }

    // Restore memory data
    if (snapshot.memoryData) {
      for (const [type, data] of Object.entries(snapshot.memoryData)) {
        this.memoryData.set(type, data);
      }
    }

    // Restore variables
    if (snapshot.variables) {
      for (const [key, value] of Object.entries(snapshot.variables)) {
        this.variables.set(key, value);
      }
    }

    // Add history entry
    this.addToHistory('system', 'context:restored');
  }
}
