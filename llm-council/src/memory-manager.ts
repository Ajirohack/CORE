/**
 * Memory Manager for AI Council
 *
 * This component manages the persistent memory system that allows the AI Council
 * to maintain context across different sessions and users.
 */

import { EventEmitter } from 'events';
import * as fs from 'fs/promises';
import * as path from 'path';
import { MemoryEntry, AICouncilConfig } from './types';

export class MemoryManager extends EventEmitter {
  private memories: Map<string, MemoryEntry> = new Map();
  private persistencePath: string | null = null;
  private persistenceEnabled: boolean = false;
  private memoryEnabled: boolean = true;
  private initialized: boolean = false;
  private memoryLoadPromise: Promise<void> | null = null;

  constructor() {
    super();
  }

  /**
   * Initialize the memory system
   */
  async initialize(config?: AICouncilConfig): Promise<void> {
    if (this.initialized) {
      return;
    }

    // Apply configuration if provided
    if (config) {
      this.memoryEnabled = config.memory?.enabled !== false;
      this.persistenceEnabled = config.memory?.persistenceEnabled === true;

      if (config.memory?.persistencePath) {
        this.persistencePath = config.memory.persistencePath;
      }
    }

    // If memory is disabled, don't proceed with initialization
    if (!this.memoryEnabled) {
      this.initialized = true;
      return;
    }

    // Clear any existing memories
    this.memories.clear();

    // Load memories from persistence if enabled
    if (this.persistenceEnabled && this.persistencePath) {
      this.memoryLoadPromise = this.loadMemories();
      await this.memoryLoadPromise;
    }

    this.initialized = true;
    this.emit('initialized');
  }

  /**
   * Store a memory entry
   */
  async storeMemory(entry: Omit<MemoryEntry, 'id' | 'timestamp'>): Promise<string> {
    // Generate a unique ID for this memory
    const id = `mem_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

    const memoryEntry: MemoryEntry = {
      ...entry,
      id,
      timestamp: Date.now(),
    };

    // Store the memory
    this.memories.set(id, memoryEntry);

    // Persist the memory if enabled
    if (this.persistenceEnabled && this.persistencePath) {
      await this.saveMemory(memoryEntry);
    }

    this.emit('memory:stored', { id });

    return id;
  }

  /**
   * Get a memory by ID
   */
  getMemory(id: string): MemoryEntry | undefined {
    return this.memories.get(id);
  }

  /**
   * Delete a memory
   */
  async deleteMemory(id: string): Promise<boolean> {
    const memory = this.memories.get(id);

    if (!memory) {
      return false;
    }

    this.memories.delete(id);

    // Delete from persistence if enabled
    if (this.persistenceEnabled && this.persistencePath) {
      try {
        const filePath = path.join(this.persistencePath, `${id}.json`);
        await fs.unlink(filePath);
      } catch (error) {
        // Ignore file not found errors
      }
    }

    this.emit('memory:deleted', { id });

    return true;
  }

  /**
   * Find memories by criteria
   */
  findMemories(criteria: {
    userId?: string;
    sessionId?: string;
    type?: 'working' | 'episodic' | 'semantic' | 'procedural';
    minPriority?: number;
    maxPriority?: number;
    fromTimestamp?: number;
    toTimestamp?: number;
    limit?: number;
  }): MemoryEntry[] {
    // Wait for memories to be loaded if loading is in progress
    if (!this.initialized && this.memoryLoadPromise) {
      // This is not ideal but a simple way to handle the case where memories are still loading
      console.warn('Attempting to find memories before initialization is complete');
    }

    // Filter memories based on criteria
    const filtered = Array.from(this.memories.values()).filter(memory => {
      if (criteria.userId && memory.userId !== criteria.userId) {
        return false;
      }

      if (criteria.sessionId && memory.sessionId !== criteria.sessionId) {
        return false;
      }

      if (criteria.type && memory.type !== criteria.type) {
        return false;
      }

      if (criteria.minPriority !== undefined && memory.priority < criteria.minPriority) {
        return false;
      }

      if (criteria.maxPriority !== undefined && memory.priority > criteria.maxPriority) {
        return false;
      }

      if (criteria.fromTimestamp !== undefined && memory.timestamp < criteria.fromTimestamp) {
        return false;
      }

      if (criteria.toTimestamp !== undefined && memory.timestamp > criteria.toTimestamp) {
        return false;
      }

      // Check if memory has expired
      if (memory.expiry !== undefined && memory.expiry < Date.now()) {
        return false;
      }

      return true;
    });

    // Sort by timestamp (newest first) and priority (highest first)
    const sorted = filtered.sort((a, b) => {
      // First by priority (higher first)
      if (b.priority !== a.priority) {
        return b.priority - a.priority;
      }

      // Then by timestamp (newer first)
      return b.timestamp - a.timestamp;
    });

    // Apply limit if specified
    if (criteria.limit !== undefined && criteria.limit > 0) {
      return sorted.slice(0, criteria.limit);
    }

    return sorted;
  }

  /**
   * Get working memory for a session
   */
  getWorkingMemory(sessionId: string): MemoryEntry[] {
    return this.findMemories({
      sessionId,
      type: 'working',
    });
  }

  /**
   * Get episodic memory for a user
   */
  getEpisodicMemory(userId: string, limit = 10): MemoryEntry[] {
    return this.findMemories({
      userId,
      type: 'episodic',
      limit,
    });
  }

  /**
   * Get semantic memory by relevance
   */
  getSemanticMemory(query: string, limit = 5): MemoryEntry[] {
    // In a real implementation, this would use a vector database or similar
    // to find semantic memories relevant to the query

    // For now, just return the most recent semantic memories
    return this.findMemories({
      type: 'semantic',
      limit,
    });
  }

  /**
   * Get procedural memory
   */
  getProceduralMemory(query: string, limit = 5): MemoryEntry[] {
    // In a real implementation, this would match the query against
    // stored procedures to find the most relevant ones

    // For now, just return the most recent procedural memories
    return this.findMemories({
      type: 'procedural',
      limit,
    });
  }

  /**
   * Clear expired memories
   */
  async clearExpiredMemories(): Promise<number> {
    const now = Date.now();
    const expiredIds: string[] = [];

    // Find expired memories
    for (const [id, memory] of this.memories.entries()) {
      if (memory.expiry !== undefined && memory.expiry < now) {
        expiredIds.push(id);
      }
    }

    // Delete expired memories
    for (const id of expiredIds) {
      await this.deleteMemory(id);
    }

    return expiredIds.length;
  }

  /**
   * Clear all memories
   */
  async clearAllMemories(): Promise<number> {
    const count = this.memories.size;

    this.memories.clear();

    // Clear persistence if enabled
    if (this.persistenceEnabled && this.persistencePath) {
      try {
        const files = await fs.readdir(this.persistencePath);
        for (const file of files) {
          if (file.endsWith('.json')) {
            await fs.unlink(path.join(this.persistencePath, file));
          }
        }
      } catch (error) {
        // Ignore errors
      }
    }

    this.emit('memory:cleared');

    return count;
  }

  /**
   * Load memories from persistence
   */
  private async loadMemories(): Promise<void> {
    if (!this.persistencePath) {
      return;
    }

    try {
      // Ensure the persistence directory exists
      await fs.mkdir(this.persistencePath, { recursive: true });

      // Read all files in the persistence directory
      const files = await fs.readdir(this.persistencePath);

      for (const file of files) {
        if (file.endsWith('.json')) {
          try {
            const filePath = path.join(this.persistencePath, file);
            const data = await fs.readFile(filePath, 'utf-8');
            const memory = JSON.parse(data) as MemoryEntry;

            // Skip if memory has expired
            if (memory.expiry !== undefined && memory.expiry < Date.now()) {
              continue;
            }

            this.memories.set(memory.id, memory);
          } catch (error) {
            // Ignore individual file errors
            console.error(`Failed to load memory file ${file}:`, error);
          }
        }
      }

      console.log(`Loaded ${this.memories.size} memories from persistence`);
    } catch (error) {
      console.error('Failed to load memories from persistence:', error);
    }
  }

  /**
   * Save a memory to persistence
   */
  private async saveMemory(memory: MemoryEntry): Promise<void> {
    if (!this.persistencePath) {
      return;
    }

    try {
      // Ensure the persistence directory exists
      await fs.mkdir(this.persistencePath, { recursive: true });

      // Write the memory to a file
      const filePath = path.join(this.persistencePath, `${memory.id}.json`);
      await fs.writeFile(filePath, JSON.stringify(memory, null, 2));
    } catch (error) {
      console.error(`Failed to save memory ${memory.id}:`, error);
    }
  }

  /**
   * Shutdown the memory manager
   */
  async shutdown(): Promise<void> {
    // Nothing to do if memory is disabled
    if (!this.memoryEnabled) {
      return;
    }

    // Clear expired memories
    await this.clearExpiredMemories();

    this.emit('shutdown');
  }
}
