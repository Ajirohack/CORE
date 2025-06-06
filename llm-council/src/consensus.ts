/**
 * Consensus Mechanism for AI Council
 * 
 * This component implements different consensus algorithms to help specialists 
 * reach agreement on complex decisions.
 */

import { EventEmitter } from 'events';
import { SharedContext } from './shared-context';
import { Logger } from './utils/logger';
import { Specialist, SpecialistResponse } from './types';
import { DecisionOption } from './decision-maker';

export type ConsensusMethod = 'majority-vote' | 'iterative-refinement' | 'delphi' | 'weighted-influence';

export interface ConsensusResult {
  agreement: boolean;
  agreedValue: any;
  confidence: number;
  iterations: number;
  participatingSpecialists: string[];
  dissenting: string[];
  metadata: {
    method: ConsensusMethod;
    executionTime: number;
    finalRound: boolean;
  };
}

export interface ConsensusOptions {
  maxIterations?: number;
  minConfidence?: number;
  timeoutMs?: number;
  defaultMethod?: ConsensusMethod;
}

export interface ConsensusRound {
  round: number;
  options: DecisionOption[];
  feedback?: string[];
}

export class ConsensusMechanism extends EventEmitter {
  private logger: Logger;
  private options: Required<ConsensusOptions>;
  
  constructor(logger: Logger, options: ConsensusOptions = {}) {
    super();
    this.logger = logger;
    
    // Default options
    this.options = {
      maxIterations: options.maxIterations ?? 3,
      minConfidence: options.minConfidence ?? 0.7,
      timeoutMs: options.timeoutMs ?? 30000, // 30 seconds default
      defaultMethod: options.defaultMethod ?? 'iterative-refinement'
    };
  }

  /**
   * Reach consensus among specialists
   */
  async reachConsensus(
    specialists: Specialist[],
    initialResponses: Record<string, SpecialistResponse>,
    sharedContext: SharedContext,
    method: ConsensusMethod = this.options.defaultMethod
  ): Promise<ConsensusResult> {
    const startTime = Date.now();
    
    this.logger.info(`Starting consensus process using ${method} method with ${specialists.length} specialists`);
    
    if (specialists.length === 0) {
      throw new Error('No specialists provided for consensus');
    }
    
    if (Object.keys(initialResponses).length === 0) {
      throw new Error('No initial responses provided for consensus');
    }
    
    // Initialize result
    let result: ConsensusResult = {
      agreement: false,
      agreedValue: null,
      confidence: 0,
      iterations: 0,
      participatingSpecialists: specialists.map(s => s.id),
      dissenting: [],
      metadata: {
        method,
        executionTime: 0,
        finalRound: false
      }
    };
    
    // Choose consensus method
    switch (method) {
      case 'majority-vote':
        result = await this.majorityVoteConsensus(specialists, initialResponses);
        break;
      case 'iterative-refinement':
        result = await this.iterativeRefinementConsensus(specialists, initialResponses, sharedContext);
        break;
      case 'delphi':
        result = await this.delphiConsensus(specialists, initialResponses, sharedContext);
        break;
      case 'weighted-influence':
        result = await this.weightedInfluenceConsensus(specialists, initialResponses, sharedContext);
        break;
      default:
        throw new Error(`Unknown consensus method: ${method}`);
    }
    
    // Update execution time
    result.metadata.executionTime = Date.now() - startTime;
    
    this.logger.info(
      `Consensus ${result.agreement ? 'reached' : 'failed'} after ${result.iterations} iterations`,
      { 
        confidence: result.confidence,
        method,
        executionTime: result.metadata.executionTime
      }
    );
    
    this.emit('consensus:complete', {
      agreement: result.agreement,
      confidence: result.confidence,
      iterations: result.iterations,
      method
    });
    
    return result;
  }
  
  /**
   * Simple majority vote consensus
   */
  private async majorityVoteConsensus(
    specialists: Specialist[],
    initialResponses: Record<string, SpecialistResponse>
  ): Promise<ConsensusResult> {
    // Extract decisions from specialist responses
    const values: Record<string, { count: number, confidence: number, specialists: string[] }> = {};
    
    // Count votes for each unique value
    for (const specialistId in initialResponses) {
      const response = initialResponses[specialistId];
      const value = JSON.stringify(response.result); // Convert to string for comparison
      
      if (!values[value]) {
        values[value] = { count: 0, confidence: 0, specialists: [] };
      }
      
      values[value].count += 1;
      values[value].confidence += response.confidence || 0;
      values[value].specialists.push(specialistId);
    }
    
    // Find the value with the most votes
    let maxVotes = 0;
    let agreedValueKey = '';
    let totalConfidence = 0;
    
    for (const value in values) {
      if (values[value].count > maxVotes) {
        maxVotes = values[value].count;
        agreedValueKey = value;
      }
      
      // Calculate average confidence for this value
      values[value].confidence /= values[value].count;
    }
    
    const votingSpecialists = Object.keys(initialResponses).length;
    const agreement = maxVotes / votingSpecialists >= 0.5; // Simple majority
    
    // Calculate confidence based on proportion of votes and average confidence
    const winningProportion = maxVotes / votingSpecialists;
    const avgConfidence = values[agreedValueKey]?.confidence || 0;
    const confidence = agreement ? winningProportion * avgConfidence : 0;
    
    // Identify dissenting specialists
    const dissentingSpecialists = Object.keys(initialResponses).filter(
      id => !values[agreedValueKey]?.specialists.includes(id)
    );
    
    return {
      agreement,
      agreedValue: agreedValueKey ? JSON.parse(agreedValueKey) : null,
      confidence,
      iterations: 1, // Majority vote always needs just one round
      participatingSpecialists: Object.keys(initialResponses),
      dissenting: dissentingSpecialists,
      metadata: {
        method: 'majority-vote',
        executionTime: 0, // Will be updated by caller
        finalRound: true
      }
    };
  }
  
  /**
   * Iterative refinement consensus
   * This approach simulates specialists learning from each other and refining their answers
   */
  private async iterativeRefinementConsensus(
    specialists: Specialist[],
    initialResponses: Record<string, SpecialistResponse>,
    sharedContext: SharedContext
  ): Promise<ConsensusResult> {
    let currentResponses = { ...initialResponses };
    let iterations = 0;
    let finalRound = false;
    
    // Record consensus rounds in shared context
    const consensusRounds: ConsensusRound[] = [];
    
    // Loop until consensus or max iterations
    while (iterations < this.options.maxIterations) {
      iterations++;
      this.logger.debug(`Consensus iteration ${iterations}`);
      
      // Convert responses to decision options
      const options: DecisionOption[] = Object.entries(currentResponses).map(
        ([specialistId, response]) => ({
          id: `${specialistId}-${iterations}`,
          value: response.result,
          confidence: response.confidence || 0.5,
          specialistId,
          weight: specialists.find(s => s.id === specialistId)?.priority || 1,
          reasoning: response.explanation
        })
      );
      
      // Add this round to our history
      consensusRounds.push({
        round: iterations,
        options
      });
      
      // Check if we have agreement
      const { agreement, agreedValue, confidence } = this.checkAgreement(options);
      
      // If we have agreement or reached max iterations, we're done
      if (agreement || iterations >= this.options.maxIterations) {
        finalRound = true;
        
        // Find dissenting specialists
        const dissentingSpecialists = options
          .filter(option => JSON.stringify(option.value) !== JSON.stringify(agreedValue))
          .map(option => option.specialistId);
        
        // Record consensus rounds in shared context
        sharedContext.set('consensusRounds', consensusRounds);
        
        return {
          agreement,
          agreedValue,
          confidence,
          iterations,
          participatingSpecialists: options.map(o => o.specialistId),
          dissenting: dissentingSpecialists,
          metadata: {
            method: 'iterative-refinement',
            executionTime: 0, // Will be updated by caller
            finalRound
          }
        };
      }
      
      // No consensus yet, we would ask specialists to refine their responses
      // This is where we would call specialists again with feedback
      // For now, we'll just simulate with a basic implementation

      // In a real implementation, this would call each specialist with feedback
      // currentResponses = await this.gatherRefinedResponses(specialists, options, currentResponses);
      
      // For simulation purposes, we'll just end after one iteration
      finalRound = true;
      break;
    }
    
    // If we get here, we couldn't reach consensus
    return {
      agreement: false,
      agreedValue: null,
      confidence: 0,
      iterations,
      participatingSpecialists: Object.keys(initialResponses),
      dissenting: Object.keys(initialResponses),
      metadata: {
        method: 'iterative-refinement',
        executionTime: 0, // Will be updated by caller
        finalRound
      }
    };
  }
  
  /**
   * Delphi consensus method
   * This implements a Delphi-like process where specialists see anonymous feedback
   */
  private async delphiConsensus(
    specialists: Specialist[],
    initialResponses: Record<string, SpecialistResponse>,
    sharedContext: SharedContext
  ): Promise<ConsensusResult> {
    // Similar to iterative refinement but with anonymous feedback
    // This is a placeholder implementation
    return this.iterativeRefinementConsensus(specialists, initialResponses, sharedContext);
  }
  
  /**
   * Weighted influence consensus
   * Higher priority specialists have more influence in convincing others
   */
  private async weightedInfluenceConsensus(
    specialists: Specialist[],
    initialResponses: Record<string, SpecialistResponse>,
    sharedContext: SharedContext
  ): Promise<ConsensusResult> {
    // Similar to iterative refinement but with weighted influence
    // This is a placeholder implementation
    return this.iterativeRefinementConsensus(specialists, initialResponses, sharedContext);
  }
  
  /**
   * Check if specialists have reached agreement
   */
  private checkAgreement(options: DecisionOption[]): { 
    agreement: boolean; 
    agreedValue: any; 
    confidence: number;
  } {
    // Group options by value
    const valueGroups: Record<string, DecisionOption[]> = {};
    
    for (const option of options) {
      const valueKey = JSON.stringify(option.value);
      
      if (!valueGroups[valueKey]) {
        valueGroups[valueKey] = [];
      }
      
      valueGroups[valueKey].push(option);
    }
    
    // Find the value with the most specialists
    let maxCount = 0;
    let agreedValueKey = '';
    
    for (const valueKey in valueGroups) {
      if (valueGroups[valueKey].length > maxCount) {
        maxCount = valueGroups[valueKey].length;
        agreedValueKey = valueKey;
      }
    }
    
    // Calculate consensus metrics
    const totalSpecialists = options.length;
    const consensusProportion = maxCount / totalSpecialists;
    
    // Average confidence of specialists who agree
    const avgConfidence = valueGroups[agreedValueKey]?.reduce(
      (sum, option) => sum + option.confidence, 
      0
    ) / maxCount;
    
    // Consider agreement reached if proportion exceeds minimum confidence
    const agreement = consensusProportion >= this.options.minConfidence;
    
    // Overall confidence is a product of proportion and average confidence
    const confidence = agreement ? consensusProportion * avgConfidence : 0;
    
    return {
      agreement,
      agreedValue: agreedValueKey ? JSON.parse(agreedValueKey) : null,
      confidence
    };
  }
  
  /**
   * Configure consensus mechanism options
   */
  updateOptions(options: Partial<ConsensusOptions>): void {
    this.options = {
      ...this.options,
      ...options
    };
    
    this.logger.debug('Consensus mechanism options updated', this.options);
  }
}