import { EventEmitter } from "events";
import { ModelRegistry } from "../model-registry";
import { Logger } from "../utils/logger";
import { Specialist, AICouncilConfig } from "../types";
import { SharedContext } from "../shared-context";

export class SpecialistManager extends EventEmitter {
  private specialists: Map<string, Specialist> = new Map();
  private specialistPrompts: Map<string, string> = new Map();
  private modelRegistry: ModelRegistry;
  private logger: Logger;
  private initialized: boolean = false;

  constructor(modelRegistry: ModelRegistry, logger: Logger) {
    super();
    this.modelRegistry = modelRegistry;
    this.logger = logger;
  }

  initialize = jest.fn(async (config: AICouncilConfig): Promise<void> => {
    this.initialized = true;

    // Register mock specialists
    this.specialists.set("analyst", {
      id: "analyst",
      name: "Data Analyst",
      specialization: "analysis",
      modelId: "gpt-4",
      priority: 1,
      enabled: true,
      config: {
        temperature: 0.2,
      },
    });

    this.specialists.set("researcher", {
      id: "researcher",
      name: "Deep Researcher",
      specialization: "research",
      modelId: "claude-3",
      priority: 2,
      enabled: true,
      config: {
        temperature: 0.3,
      },
    });

    this.specialists.set("creative", {
      id: "creative",
      name: "Creative Writer",
      specialization: "creative",
      modelId: "gpt-4",
      priority: 3,
      enabled: true,
      config: {
        temperature: 0.7,
      },
    });

    // Register mock prompts
    this.specialistPrompts.set("analyst", "You are a data analyst...");
    this.specialistPrompts.set("researcher", "You are a researcher...");
    this.specialistPrompts.set("creative", "You are a creative writer...");

    this.logger.info("Mock specialist manager initialized with 3 specialists");
  });

  registerSpecialist = jest.fn((specialist: Specialist) => {
    this.specialists.set(specialist.id, specialist);
    return true;
  });

  getSpecialist = jest.fn((specialistId: string): Specialist | undefined => {
    return this.specialists.get(specialistId);
  });

  getEnabledSpecialists = jest.fn((): Specialist[] => {
    return Array.from(this.specialists.values()).filter((s) => s.enabled);
  });

  getAllSpecialists = jest.fn((): Specialist[] => {
    return Array.from(this.specialists.values());
  });

  executeSpecialist = jest.fn(
    async (specialistId: string, request: any, context: SharedContext) => {
      const specialist = this.specialists.get(specialistId);
      if (!specialist) {
        throw new Error(`Specialist not found: ${specialistId}`);
      }

      this.logger.info(`Executing specialist: ${specialistId}`);

      // Mock different responses based on specialist
      switch (specialistId) {
        case "analyst":
          return {
            analysis: "This is a detailed analysis based on the data...",
            confidence: 0.85,
          };
        case "researcher":
          return {
            findings: "Based on my research, I found several key points...",
            references: ["source1", "source2"],
            confidence: 0.78,
          };
        case "creative":
          return {
            content: "Here is a creative solution to your request...",
            alternatives: ["option A", "option B"],
            confidence: 0.92,
          };
        default:
          return {
            result: `Generic response from ${specialistId}`,
            confidence: 0.5,
          };
      }
    }
  );
}

export const mockSpecialistManager = (
  modelRegistry: ModelRegistry,
  logger: Logger
) => new SpecialistManager(modelRegistry, logger);
