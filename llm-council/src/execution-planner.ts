/**
 * Execution Planner for AI Council
 *
 * This component plans the execution flow for a request through the AI Council,
 * determining which specialists to use and in what order.
 */

import { EventEmitter } from "events";
import { ExecutionPlan, ExecutionStep, ProcessingPhase } from "./types";
import { SpecialistManager } from "./specialist-manager";
import { SharedContext } from "./shared-context";
import { Logger } from "./utils/logger";

// Define ProcessingPhases as constant object to use as enum values
const ProcessingPhases = {
  ANALYSIS: "analysis" as ProcessingPhase,
  REASONING: "reasoning" as ProcessingPhase,
  PLANNING: "planning" as ProcessingPhase,
  EXECUTION: "execution" as ProcessingPhase,
  SYNTHESIS: "synthesis" as ProcessingPhase,
};

export class ExecutionPlanner extends EventEmitter {
  private specialistManager: SpecialistManager;
  private logger: Logger;

  constructor(specialistManager: SpecialistManager, logger: Logger) {
    super();
    this.specialistManager = specialistManager;
    this.logger = logger;
  }

  /**
   * Create an execution plan for a request
   */
  async createPlan(
    request: any,
    sharedContext: SharedContext
  ): Promise<ExecutionPlan> {
    try {
      this.logger.debug("Creating execution plan for request");

      // Analyze the request to determine required specializations
      const requiredSpecializations = await this.analyzeRequest(request);

      // Get all enabled specialists
      const allSpecialists = this.specialistManager.getEnabledSpecialists();

      // Filter specialists based on required specializations
      let selectedSpecialists = allSpecialists.filter(
        (specialist) =>
          specialist.specialization &&
          requiredSpecializations.includes(specialist.specialization)
      );

      // If no specialists were selected, use all enabled specialists
      // This is a fallback to ensure we always have specialists
      if (selectedSpecialists.length === 0) {
        this.logger.debug(
          "No specialists matched required specializations, using all enabled specialists"
        );
        selectedSpecialists = allSpecialists;
      }

      // Sort specialists by priority (lower runs first)
      selectedSpecialists.sort((a, b) => (a.priority || 1) - (b.priority || 1));

      // Determine execution phases based on request complexity
      const phases = this.determinePhases(request);

      // Create execution steps
      const steps: ExecutionStep[] = [];

      for (const phase of phases) {
        // For each phase, select the appropriate specialists
        const phaseSpecialists = this.selectSpecialistsForPhase(
          selectedSpecialists,
          phase
        );

        // Create a step for each specialist in this phase
        for (const specialist of phaseSpecialists) {
          const step: ExecutionStep = {
            specialistId: specialist.id,
            input: sharedContext.prepareSpecialistInput(specialist.id, {
              phase,
            }),
            phase,
            priority: specialist.priority || 1, // Lower priority runs first
            options: {},
          };

          // Add dependencies on previous phase steps if applicable
          if (steps.length > 0 && phase !== ProcessingPhases.ANALYSIS) {
            // This step depends on all steps from the previous phase
            step.dependsOn = steps
              .filter((s) =>
                this.isStepFromPreviousPhase(
                  s.phase as ProcessingPhase,
                  phase as ProcessingPhase
                )
              )
              .map((s) => s.specialistId);
          }

          steps.push(step);
        }
      }

      // Create an integration step if needed (when multiple specialists are used)
      let integrationStep: ExecutionStep | undefined;

      if (selectedSpecialists.length > 1) {
        integrationStep = {
          specialistId: "integration",
          input: {
            ...sharedContext.prepareSpecialistInput("integration"),
            phase: ProcessingPhases.SYNTHESIS,
          },
          phase: ProcessingPhases.SYNTHESIS,
          dependsOn: steps.map((s) => s.specialistId), // Depends on all specialists
          priority: 100, // Integration runs last
          options: {},
        };
      }

      // Create and return the execution plan
      const plan: ExecutionPlan = {
        steps,
        integrationStep,
        context: {},
      };

      this.logger.debug(
        `Created execution plan with ${steps.length} steps and ${
          integrationStep ? "an" : "no"
        } integration step`
      );
      this.emit("plan:created", { stepCount: steps.length });

      return plan;
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error";
      this.logger.error("Failed to create execution plan", {
        error: errorMessage,
      });
      throw error;
    }
  }

  /**
   * Check if a step's phase is the one immediately before another phase
   */
  private isStepFromPreviousPhase(
    stepPhase: ProcessingPhase,
    currentPhase: ProcessingPhase
  ): boolean {
    const phaseOrder = [
      ProcessingPhases.ANALYSIS,
      ProcessingPhases.REASONING,
      ProcessingPhases.PLANNING,
      ProcessingPhases.EXECUTION,
      ProcessingPhases.SYNTHESIS,
    ];

    const stepIndex = phaseOrder.indexOf(stepPhase);
    const currentIndex = phaseOrder.indexOf(currentPhase);

    return stepIndex === currentIndex - 1;
  }

  /**
   * Analyze a request to determine which specializations are required
   */
  private async analyzeRequest(request: any): Promise<string[]> {
    // This is a simplified implementation that could be enhanced with a more
    // sophisticated analysis in a real system, potentially using NLP or
    // content-based rules

    const requiredSpecializations: string[] = [];

    // Basic text content always requires the text specialist
    requiredSpecializations.push("text");

    // Check if request includes code
    if (this.containsCode(request)) {
      requiredSpecializations.push("code");
    }

    // Check if request includes structured data
    if (this.containsStructuredData(request)) {
      requiredSpecializations.push("data");
    }

    // Check if request includes images or multimedia
    if (this.containsMultimedia(request)) {
      requiredSpecializations.push("multimodal");
    }

    // Check if request requires complex reasoning
    if (this.requiresComplexReasoning(request)) {
      requiredSpecializations.push("reasoning");
    }

    // Check if request requires deep thinking
    if (this.requiresDeepThinking(request)) {
      requiredSpecializations.push("thinking");
    }

    // Check if request requires tools
    if (this.requiresTools(request)) {
      requiredSpecializations.push("tool");
    }

    return requiredSpecializations;
  }

  /**
   * Determine execution phases based on request complexity
   */
  private determinePhases(request: any): ProcessingPhase[] {
    // Low complexity: just analysis phase
    // Medium complexity: analysis and synthesis
    // High complexity: analysis, reasoning, synthesis
    // Very high complexity: all phases

    const complexity = this.estimateComplexity(request);

    if (complexity < 2) {
      return [ProcessingPhases.ANALYSIS];
    } else if (complexity < 4) {
      return [ProcessingPhases.ANALYSIS, ProcessingPhases.SYNTHESIS];
    } else if (complexity < 7) {
      return [
        ProcessingPhases.ANALYSIS,
        ProcessingPhases.REASONING,
        ProcessingPhases.SYNTHESIS,
      ];
    } else {
      return [
        ProcessingPhases.ANALYSIS,
        ProcessingPhases.REASONING,
        ProcessingPhases.PLANNING,
        ProcessingPhases.EXECUTION,
        ProcessingPhases.SYNTHESIS,
      ];
    }
  }

  /**
   * Select specialists for a specific phase
   */
  private selectSpecialistsForPhase(
    specialists: any[],
    phase: ProcessingPhase
  ): any[] {
    // For analysis, use all specialists
    if (phase === ProcessingPhases.ANALYSIS) {
      return specialists;
    }

    // For reasoning, prefer reasoning and thinking specialists
    if (phase === ProcessingPhases.REASONING) {
      const reasoningSpecialists = specialists.filter(
        (s) =>
          s.specialization === "reasoning" || s.specialization === "thinking"
      );

      return reasoningSpecialists.length > 0
        ? reasoningSpecialists
        : specialists;
    }

    // For planning, prefer planning specialists
    if (phase === ProcessingPhases.PLANNING) {
      const planningSpecialists = specialists.filter(
        (s) => s.specialization === "planning"
      );

      return planningSpecialists.length > 0 ? planningSpecialists : specialists;
    }

    // For execution, prefer tool specialists
    if (phase === ProcessingPhases.EXECUTION) {
      const toolSpecialists = specialists.filter(
        (s) => s.specialization === "tool"
      );

      return toolSpecialists.length > 0 ? toolSpecialists : specialists;
    }

    // For synthesis, prefer higher weight specialists
    if (phase === ProcessingPhases.SYNTHESIS) {
      return specialists
        .sort((a, b) => (b.weight || 1) - (a.weight || 1))
        .slice(0, 2);
    }

    return specialists;
  }

  /**
   * Estimate request complexity on a scale of 1-10
   */
  private estimateComplexity(request: any): number {
    let complexity = 1; // Start with minimal complexity

    if (!request.input) {
      return complexity;
    }

    const input = typeof request.input === "string" ? request.input : "";

    // Very long inputs are more complex
    if (input.length > 1000) {
      complexity += 2;
    } else if (input.length > 500) {
      complexity += 1;
    }

    // Questions are more complex
    if (input.includes("?")) {
      complexity += 1;
    }

    // Multiple questions are even more complex
    const questionCount = (input.match(/\?/g) || []).length;
    if (questionCount > 2) {
      complexity += 1;
    }

    // Requests for plans or step-by-step instructions are complex
    if (
      input.match(/plan|steps|procedure|how to|explain|step[-\s]by[-\s]step/i)
    ) {
      complexity += 2;
    }

    // Comparisons are complex
    if (
      input.match(/compare|difference|better|worse|versus|vs\.|pros and cons/i)
    ) {
      complexity += 2;
    }

    // Technical or specialized content is complex
    if (input.match(/code|program|function|algorithm|technical|formula/i)) {
      complexity += 2;
    }

    // Presence of attachments increases complexity
    if (request.attachments && request.attachments.length > 0) {
      complexity += 2;
    }

    // Cap at 10
    return Math.min(10, complexity);
  }

  /**
   * Check if request contains code
   */
  private containsCode(request: any): boolean {
    if (!request.input) return false;

    const input = typeof request.input === "string" ? request.input : "";

    // Check for code indicators
    return Boolean(
      input.match(
        /function|const|var|let|import|export|class|if|else|for|while|return|=>/i
      ) ||
        (input.includes("{") && input.includes("}")) ||
        input.includes("```")
    );
  }

  /**
   * Check if request contains structured data
   */
  private containsStructuredData(request: any): boolean {
    if (!request.input) return false;

    const input = typeof request.input === "string" ? request.input : "";

    // Check for data indicators
    return Boolean(
      input.match(
        /json|csv|database|table|row|column|field|value|schema|query|sql/i
      ) ||
        (input.includes("{") && input.includes('"')) ||
        (input.includes("[") && input.includes("]"))
    );
  }

  /**
   * Check if request contains multimedia content
   */
  private containsMultimedia(request: any): boolean {
    // Check for attachments
    if (request.attachments && request.attachments.length > 0) {
      return true;
    }

    if (!request.input) return false;

    const input = typeof request.input === "string" ? request.input : "";

    // Check for mentions of images or videos
    return Boolean(
      input.match(/image|picture|photo|diagram|video|audio|media|file/i)
    );
  }

  /**
   * Check if request requires complex reasoning
   */
  private requiresComplexReasoning(request: any): boolean {
    if (!request.input) return false;

    const input = typeof request.input === "string" ? request.input : "";

    // Check for reasoning indicators
    return Boolean(
      input.match(
        /why|reason|because|cause|effect|therefore|thus|hence|explain|logic|argument|proof|evidence|analyze|evaluate|compare/i
      )
    );
  }

  /**
   * Check if request requires deep thinking
   */
  private requiresDeepThinking(request: any): boolean {
    if (!request.input) return false;

    const input = typeof request.input === "string" ? request.input : "";

    // Check for deep thinking indicators
    return Boolean(
      input.match(
        /philosophy|ethical|moral|implications|consequences|tradeoffs|dilemma|complex|nuanced|perspective|creative|imagine|design|invent|develop|strategy/i
      )
    );
  }

  /**
   * Check if request requires tools
   */
  private requiresTools(request: any): boolean {
    // If the request explicitly mentions tools, it likely requires them
    if (!request.input) return false;

    const input = typeof request.input === "string" ? request.input : "";

    // Check for tool indicators
    return Boolean(
      input.match(
        /search|look up|find information|calculate|convert|translate|tool|api|http|get data|fetch|retrieve/i
      )
    );
  }
}
