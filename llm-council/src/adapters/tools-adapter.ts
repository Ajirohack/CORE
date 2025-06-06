/**
 * Tools Adapter for AI Council
 *
 * This adapter connects the AI Council with the tools-packages module,
 * allowing AI specialists to discover, execute and utilize tools.
 */

import { EventEmitter } from 'events';
import { Logger } from '../utils/logger';
import { ToolExecutionResult, ToolExecutionError } from '../types';

// Interface that matches the tools-packages module's API
interface ToolsSystem {
  registerTool(toolDefinition: any): Promise<string>;
  executeTool(toolId: string, params: any): Promise<any>;
  listAvailableTools(): Promise<any[]>;
  getToolMetadata(toolId: string): Promise<any>;
}

export interface ToolsAdapterOptions {
  toolsSystemClient: ToolsSystem;
  logger?: Logger;
}

export class ToolsAdapter extends EventEmitter {
  private toolsSystem: ToolsSystem;
  private logger: Logger;
  private toolCache: Map<string, any> = new Map();

  constructor(options: ToolsAdapterOptions) {
    super();
    this.toolsSystem = options.toolsSystemClient;
    this.logger = options.logger || new Logger({ module: 'tools-adapter' });
  }

  /**
   * Initialize the adapter and fetch available tools
   */
  async initialize(): Promise<void> {
    this.logger.info('Initializing Tools Adapter');
    try {
      await this.refreshToolsCache();
      this.logger.info(`Tools Adapter initialized with ${this.toolCache.size} available tools`);
    } catch (error) {
      this.logger.error('Failed to initialize Tools Adapter', error);
      throw error;
    }
  }

  /**
   * Get a list of all available tools with their metadata
   */
  async listTools(): Promise<any[]> {
    await this.refreshToolsCache();
    return Array.from(this.toolCache.values());
  }

  /**
   * Execute a tool with the given parameters
   */
  async executeTool(toolId: string, params: any): Promise<ToolExecutionResult> {
    this.logger.debug(`Executing tool: ${toolId}`, { params });

    try {
      // Check if tool exists
      if (!this.toolCache.has(toolId)) {
        await this.refreshToolsCache();
        if (!this.toolCache.has(toolId)) {
          throw new Error(`Tool not found: ${toolId}`);
        }
      }

      const startTime = Date.now();
      const result = await this.toolsSystem.executeTool(toolId, params);
      const executionTime = Date.now() - startTime;

      this.logger.debug(`Tool executed successfully: ${toolId}`, { executionTime });
      this.emit('tool:executed', { toolId, params, executionTime });

      return {
        success: true,
        result,
        toolId,
        executionTime,
      };
    } catch (error) {
      this.logger.error(`Error executing tool: ${toolId}`, error);
      this.emit('tool:error', { toolId, params, error });

      return {
        success: false,
        error: {
          message: error.message,
          code: error.code || 'TOOL_EXECUTION_ERROR',
          details: error.details || {},
        },
        toolId,
      };
    }
  }

  /**
   * Get detailed metadata about a specific tool
   */
  async getToolMetadata(toolId: string): Promise<any> {
    if (this.toolCache.has(toolId)) {
      return this.toolCache.get(toolId);
    }

    try {
      const toolMetadata = await this.toolsSystem.getToolMetadata(toolId);
      this.toolCache.set(toolId, toolMetadata);
      return toolMetadata;
    } catch (error) {
      this.logger.error(`Error retrieving tool metadata: ${toolId}`, error);
      throw error;
    }
  }

  /**
   * Refresh the internal cache of available tools
   */
  private async refreshToolsCache(): Promise<void> {
    try {
      const tools = await this.toolsSystem.listAvailableTools();

      // Clear and repopulate cache
      this.toolCache.clear();
      for (const tool of tools) {
        this.toolCache.set(tool.id, tool);
      }

      this.logger.debug(`Tools cache refreshed with ${tools.length} tools`);
    } catch (error) {
      this.logger.error('Failed to refresh tools cache', error);
      throw error;
    }
  }
}
