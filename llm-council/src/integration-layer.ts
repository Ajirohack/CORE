/**
 * Integration Layer for AI Council
 *
 * This component integrates outputs from multiple specialists into a coherent response,
 * presenting them as if from a single unified intelligence.
 */

import { EventEmitter } from 'events';
import { SpecialistResult, CouncilResponse } from './types';
import { SharedContext } from './shared-context';
import { Logger } from './utils/logger';

export class IntegrationLayer extends EventEmitter {
  private logger: Logger;

  constructor(logger: Logger) {
    super();
    this.logger = logger;
  }

  /**
   * Integrate results from multiple specialists into a single coherent response
   */
  async integrate(
    results: SpecialistResult[],
    sharedContext: SharedContext
  ): Promise<CouncilResponse> {
    this.logger.debug(`Integrating ${results.length} specialist results`);

    // For a single result, just return it directly
    if (results.length === 1) {
      this.logger.debug('Only one specialist result, returning directly');
      const result = results[0];

      return {
        response: result.result.response || result.result,
        metadata: {
          specialists: [result.specialistId],
          confidence: result.confidence,
          processingTime: result.processingTime,
          ...result.metadata,
        },
      };
    }

    try {
      // For multiple results, use our integration approach
      const startTime = Date.now();

      // Extract the content from each result
      const specialistContributions = results.map(result => ({
        specialistId: result.specialistId,
        content: result.result.response || result.result,
        confidence: result.confidence,
        metadata: result.metadata,
      }));

      // Sort results by confidence (highest first)
      specialistContributions.sort((a, b) => (b.confidence || 1) - (a.confidence || 1));

      // Check if we should use a specialized model for integration
      // We use this approach when the results are from very different specialists
      // or they have very different confidence levels
      const shouldUseIntegrationModel = this.shouldUseIntegrationModel(specialistContributions);

      let integratedResponse: string;
      let integratedConfidence: number;

      if (shouldUseIntegrationModel) {
        // Use an AI model to integrate responses (future implementation)
        const integrationResult = await this.integrateUsingModel(
          specialistContributions,
          sharedContext
        );

        integratedResponse = integrationResult.response;
        integratedConfidence =
          integrationResult.confidence || this.calculateAverageConfidence(specialistContributions);
      } else {
        // Use the rule-based integration approach
        const integrationResult = this.integrateUsingRules(specialistContributions, sharedContext);

        integratedResponse = integrationResult.response;
        integratedConfidence = integrationResult.confidence;
      }

      const processingTime = Date.now() - startTime;

      const response: CouncilResponse = {
        response: integratedResponse,
        metadata: {
          specialists: results.map(r => r.specialistId),
          confidence: integratedConfidence,
          processingTime,
          sourcedFrom: 'multiple specialists',
        },
      };

      this.logger.debug(`Integration completed in ${processingTime}ms`);
      this.emit('integration:complete', { specialistCount: results.length, processingTime });

      return response;
    } catch (error) {
      this.logger.error('Failed to integrate specialist results', error);

      // Fallback to the highest confidence result
      const highestConfidenceResult = results.reduce((prev, current) =>
        (current.confidence || 0) > (prev.confidence || 0) ? current : prev
      );

      return {
        response: highestConfidenceResult.result.response || highestConfidenceResult.result,
        metadata: {
          specialists: [highestConfidenceResult.specialistId],
          confidence: highestConfidenceResult.confidence,
          processingTime: highestConfidenceResult.processingTime,
          integrationError: error.message,
          fallback: true,
        },
      };
    }
  }

  /**
   * Determine if we should use a specialized integration model
   */
  private shouldUseIntegrationModel(contributions: any[]): boolean {
    // If we have more than 3 specialists, always use the integration model
    if (contributions.length > 3) {
      return true;
    }

    // Check if confidence scores vary widely
    const confidenceScores = contributions.map(c => c.confidence || 1);
    const maxConfidence = Math.max(...confidenceScores);
    const minConfidence = Math.min(...confidenceScores);

    // If the confidence range is wide, use the integration model
    if (maxConfidence - minConfidence > 0.3) {
      return true;
    }

    // Check if response lengths vary widely
    const lengths = contributions.map(c => c.content.length);
    const maxLength = Math.max(...lengths);
    const minLength = Math.min(...lengths);

    // If the length ratio is high, use the integration model
    if (maxLength / minLength > 5) {
      return true;
    }

    // For now, default to rule-based integration for most cases
    return false;
  }

  /**
   * Integrate specialist outputs using rules
   */
  private integrateUsingRules(
    contributions: any[],
    sharedContext: SharedContext
  ): { response: string; confidence: number } {
    // Start with the highest confidence contribution
    const primaryContribution = contributions[0];
    let response = primaryContribution.content;

    // If there's only one contribution, just return it
    if (contributions.length === 1) {
      return {
        response,
        confidence: primaryContribution.confidence || 1.0,
      };
    }

    // For multiple contributions, use a formatted approach based on the type of content
    const originalRequest = sharedContext.originalRequest;

    // Rule 1: For analytical questions, combine the reasoning from different specialists
    if (
      originalRequest.input &&
      originalRequest.input.match(/why|how|explain|reason|analyze|evaluate/i)
    ) {
      response = this.combineAnalyticalResponses(contributions);
    }
    // Rule 2: For factual questions, prioritize the most confident response
    else if (
      originalRequest.input &&
      originalRequest.input.match(/what|when|where|who|which|is|are|can|do|does/i)
    ) {
      response = this.combineFactualResponses(contributions);
    }
    // Rule 3: For creative or generative content, merge the contributions
    else if (
      originalRequest.input &&
      originalRequest.input.match(/create|generate|design|write|suggest|come up with/i)
    ) {
      response = this.combineCreativeResponses(contributions);
    }
    // Default rule: Combine based on confidence and content coherence
    else {
      response = this.combineDefaultResponses(contributions);
    }

    // Calculate the integrated confidence as a weighted average
    const confidence = this.calculateAverageConfidence(contributions);

    return {
      response,
      confidence,
    };
  }

  /**
   * Combine analytical responses
   */
  private combineAnalyticalResponses(contributions: any[]): string {
    // Start with the highest confidence contribution
    let response = contributions[0].content;

    // Look for unique insights in other contributions
    for (let i = 1; i < contributions.length; i++) {
      const content = contributions[i].content;

      // Extract sentences or paragraphs not present in the response
      const paragraphs = content.split('\n\n');

      for (const paragraph of paragraphs) {
        // Skip short or empty paragraphs
        if (paragraph.trim().length < 50) continue;

        // If this paragraph offers new insights, add it
        if (!this.containsSimilarContent(response, paragraph)) {
          response += '\n\n' + paragraph;
        }
      }
    }

    return response;
  }

  /**
   * Combine factual responses
   */
  private combineFactualResponses(contributions: any[]): string {
    // For factual responses, we tend to trust the highest confidence specialist
    let response = contributions[0].content;

    // Check if other specialists strongly disagree
    const disagreements = [];

    for (let i = 1; i < contributions.length; i++) {
      // Only consider high-confidence disagreements
      if (
        contributions[i].confidence &&
        contributions[i].confidence > 0.7 &&
        !this.containsSimilarContent(response, contributions[i].content)
      ) {
        disagreements.push(contributions[i].content);
      }
    }

    // If there are disagreements from high-confidence specialists, include them
    if (disagreements.length > 0) {
      response += '\n\nAdditional perspective: ' + disagreements[0];
    }

    return response;
  }

  /**
   * Combine creative responses
   */
  private combineCreativeResponses(contributions: any[]): string {
    // For creative content, we often want to merge ideas

    // Extract the best parts from each contribution
    const sections = [];

    for (const contribution of contributions) {
      const content = contribution.content;

      // Split into paragraphs
      const paragraphs = content.split('\n\n');

      // Add the most substantial paragraphs
      for (const paragraph of paragraphs) {
        if (paragraph.trim().length > 100) {
          // Avoid duplicate content
          if (!sections.some(s => this.containsSimilarContent(s, paragraph))) {
            sections.push(paragraph);
          }
        }
      }
    }

    // Combine the sections
    return sections.join('\n\n');
  }

  /**
   * Default combination method
   */
  private combineDefaultResponses(contributions: any[]): string {
    // Use the highest confidence response as the base
    let response = contributions[0].content;

    // Include unique additional information from other contributions
    for (let i = 1; i < contributions.length; i++) {
      const content = contributions[i].content;

      // Split into sections
      const sections = content.split('\n\n');

      for (const section of sections) {
        // Skip short sections
        if (section.trim().length < 70) continue;

        // If this section offers new content, add it
        if (!this.containsSimilarContent(response, section)) {
          response += '\n\n' + section;
        }
      }
    }

    return response;
  }

  /**
   * Check if one text contains similar content to another
   */
  private containsSimilarContent(text1: string, text2: string): boolean {
    // This is a simple implementation that could be improved with better NLP techniques

    // Normalize both texts
    const normalized1 = text1.toLowerCase().replace(/\s+/g, ' ');
    const normalized2 = text2.toLowerCase().replace(/\s+/g, ' ');

    // Extract key phrases (words of 5+ chars)
    const keyWords1 = new Set(normalized1.split(/\W+/).filter(w => w.length >= 5));

    const keyWords2 = normalized2.split(/\W+/).filter(w => w.length >= 5);

    // Count matching key words
    let matchCount = 0;
    for (const word of keyWords2) {
      if (keyWords1.has(word)) {
        matchCount++;
      }
    }

    // If more than 40% of key words match, consider it similar content
    return matchCount / keyWords2.length > 0.4;
  }

  /**
   * Calculate average confidence weighted by content length
   */
  private calculateAverageConfidence(contributions: any[]): number {
    if (contributions.length === 0) return 0;
    if (contributions.length === 1) return contributions[0].confidence || 1.0;

    let totalWeight = 0;
    let weightedSum = 0;

    for (const contribution of contributions) {
      const confidence = contribution.confidence || 0.7; // Default confidence
      const weight = contribution.content.length; // Weight by content length

      weightedSum += confidence * weight;
      totalWeight += weight;
    }

    return totalWeight > 0 ? weightedSum / totalWeight : 0.7;
  }

  /**
   * Integrate specialist outputs using an AI model
   */
  private async integrateUsingModel(
    contributions: any[],
    sharedContext: SharedContext
  ): Promise<{ response: string; confidence?: number }> {
    // This would normally use an actual LLM to integrate the responses
    // For now, we'll use a simpler approach that simulates what the model would do

    this.logger.debug('Using model-based integration (simulated)');

    // Sort by confidence
    contributions.sort((a, b) => (b.confidence || 1) - (a.confidence || 1));

    // Extract the original request
    const request = sharedContext.originalRequest.input;

    // Create a prompt that would be sent to the model
    const prompt = `
Original request: ${request}

Specialist responses:
${contributions.map((c, i) => `[Specialist ${i + 1}]:\n${c.content}\n`).join('\n')}

Your task is to create a unified, coherent response that:
1. Addresses the original request fully
2. Integrates the insights from all specialists
3. Presents the information in a logical flow
4. Speaks with a unified voice (don't mention different specialists)
5. Prioritizes higher confidence information (Specialist 1 has highest confidence)

Unified response:`;

    // For simulation purposes, we'll use a rule-based approach
    // In a real implementation, we would send the prompt to an LLM

    // Start with the highest confidence contribution
    let response = contributions[0].content;

    // For longer responses, extract 1-2 key insights from other contributions
    if (response.length > 500) {
      for (let i = 1; i < Math.min(3, contributions.length); i++) {
        const content = contributions[i].content;

        // Find a paragraph that doesn't exist in the response
        const paragraphs = content.split('\n\n');

        for (const paragraph of paragraphs) {
          if (paragraph.length > 100 && !this.containsSimilarContent(response, paragraph)) {
            response += '\n\n' + paragraph;
            break; // Just add one paragraph from each contribution
          }
        }
      }
    }
    // For shorter responses, combine more extensively
    else {
      for (let i = 1; i < contributions.length; i++) {
        const content = contributions[i].content;

        // Add non-duplicate paragraphs
        const paragraphs = content.split('\n\n');

        for (const paragraph of paragraphs) {
          if (paragraph.length > 50 && !this.containsSimilarContent(response, paragraph)) {
            response += '\n\n' + paragraph;
          }
        }
      }
    }

    // In a real implementation, the model would return a confidence score
    // For now, calculate a weighted average
    const confidence = this.calculateAverageConfidence(contributions);

    return {
      response,
      confidence,
    };
  }
}
