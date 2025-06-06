import {
  DecisionMaker,
  DecisionOption,
  DecisionResult,
  DecisionMakerOptions,
} from "../decision-maker";
import { Logger } from "../utils/logger";
import { SharedContext } from "../shared-context";
import { Specialist } from "../types";

// Mock Logger
jest.mock("../utils/logger");

describe("DecisionMaker", () => {
  let decisionMaker: DecisionMaker;
  let mockLogger: any;
  let mockSpecialists: any[];
  let mockSharedContext: any;

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();

    // Create mock logger with correct signatures
    mockLogger = {
      debug: jest.fn(
        (message: string, metadata?: Record<string, any>, options?: any) => {}
      ),
      info: jest.fn(
        (message: string, metadata?: Record<string, any>, options?: any) => {}
      ),
      warn: jest.fn(
        (message: string, metadata?: Record<string, any>, options?: any) => {}
      ),
      error: jest.fn((message: string, error?: any, options?: any) => {}),
      log: jest.fn(
        (level: string, message: string, metadata?: any, options?: any) => {}
      ),
    };

    // Create mock specialists array
    mockSpecialists = [
      {
        id: "specialist1",
        name: "Specialist 1",
        capabilities: ["math", "reasoning"],
        domains: ["general"],
        execute: jest.fn().mockResolvedValue({
          specialistId: "specialist1",
          result: {},
          processingTime: 100,
        }),
        canHandle: jest.fn().mockResolvedValue({ can: true, confidence: 0.9 }),
      },
      {
        id: "specialist2",
        name: "Specialist 2",
        capabilities: ["writing", "summarization"],
        domains: ["content"],
        execute: jest.fn().mockResolvedValue({
          specialistId: "specialist2",
          result: {},
          processingTime: 150,
        }),
        canHandle: jest.fn().mockResolvedValue({ can: true, confidence: 0.8 }),
      },
      {
        id: "specialist3",
        name: "Specialist 3",
        capabilities: ["research", "analysis"],
        domains: ["data"],
        execute: jest.fn().mockResolvedValue({
          specialistId: "specialist3",
          result: {},
          processingTime: 120,
        }),
        canHandle: jest.fn().mockResolvedValue({ can: true, confidence: 0.7 }),
      },
    ];

    // Create mock SharedContext
    mockSharedContext = {
      getUserPreferences: jest.fn().mockReturnValue({}),
      getMemory: jest.fn().mockReturnValue({}),
      addToContext: jest.fn(),
      prepareSpecialistInput: jest.fn().mockReturnValue({}),
      data: {},
      request: { input: "test" },
      metadata: {},
    };

    // Initialize DecisionMaker with mock dependencies - using low minConfidence to allow weighted voting to work
    const options: DecisionMakerOptions = {
      minConfidence: 0.1, // Set very low to ensure weighted voting passes
      consensusThreshold: 0.7,
      enableExecutiveDecision: false, // Disable executive decision for cleaner tests
    };

    decisionMaker = new DecisionMaker(mockLogger as unknown as Logger, options);
  });

  it("should be defined", () => {
    expect(decisionMaker).toBeDefined();
  });

  // Test case 1: Weighted voting decision method
  it("should make a decision using weighted voting when options have different weights", async () => {
    const options: DecisionOption[] = [
      {
        id: "option1",
        value: "First option",
        confidence: 0.7,
        specialistId: "specialist1",
        weight: 0.8, // 0.7 * 0.8 = 0.56 weighted score
        reasoning: "This seems like the best choice based on X",
      },
      {
        id: "option2",
        value: "Second option",
        confidence: 0.8,
        specialistId: "specialist2",
        weight: 0.5, // 0.8 * 0.5 = 0.40 weighted score
        reasoning: "I think this is better because of Y",
      },
      {
        id: "option3",
        value: "Third option",
        confidence: 0.6,
        specialistId: "specialist3",
        weight: 0.3, // 0.6 * 0.3 = 0.18 weighted score
        reasoning: "I suggest this based on Z",
      },
    ];

    // Call the makeDecision method with all required parameters
    const result: DecisionResult = await decisionMaker.makeDecision(
      options,
      mockSpecialists as Specialist[],
      mockSharedContext as SharedContext
    );

    // Expect the highest weighted option to win (option1)
    expect(result.selectedOption.id).toBe("option1");
    expect(result.metadata.decisionMethod).toBe("weighted-voting");
    expect(mockLogger.info).toHaveBeenCalled();
  });

  // Test case 2: Highest confidence decision method
  it("should make a decision based on highest confidence when weights are equal", async () => {
    // Create a specific decision maker with appropriate settings for this test
    const confidenceDecisionMaker = new DecisionMaker(
      mockLogger as unknown as Logger,
      {
        minConfidence: 0.6, // Set to allow confidence-based decision
        consensusThreshold: 0.9, // Set high to prevent consensus
        enableExecutiveDecision: false, // Disable executive decision
      }
    );

    const options: DecisionOption[] = [
      {
        id: "option1",
        value: "First option",
        confidence: 0.7,
        specialistId: "specialist1",
        weight: 1.0, // Equal weights for all options
      },
      {
        id: "option2",
        value: "Second option",
        confidence: 0.9, // Highest confidence
        specialistId: "specialist2",
        weight: 1.0,
      },
      {
        id: "option3",
        value: "Third option",
        confidence: 0.6,
        specialistId: "specialist3",
        weight: 1.0,
      },
    ];

    const result = await confidenceDecisionMaker.makeDecision(
      options,
      mockSpecialists as Specialist[],
      mockSharedContext as SharedContext
    );

    // Expect highest confidence to win (option2)
    expect(result.selectedOption.id).toBe("option2");
    expect(result.metadata.decisionMethod).toBe("highest-confidence");
  });

  // Test case 3: Consensus decision method
  it("should identify when consensus exists among options", async () => {
    // Create a new DecisionMaker with appropriate settings for this test
    const consensusDecisionMaker = new DecisionMaker(
      mockLogger as unknown as Logger,
      {
        minConfidence: 0.1, // Low min confidence
        consensusThreshold: 0.7, // Reasonable consensus threshold
        enableExecutiveDecision: false,
      }
    );

    // Multiple specialists suggesting the same thing
    const options: DecisionOption[] = [
      {
        id: "consensus1",
        value: "Same value",
        confidence: 0.7,
        specialistId: "specialist1",
        weight: 1.0,
      },
      {
        id: "consensus2",
        value: "Same value",
        confidence: 0.8,
        specialistId: "specialist2",
        weight: 1.0,
      },
      {
        id: "consensus3",
        value: "Same value",
        confidence: 0.75,
        specialistId: "specialist3",
        weight: 1.0,
      },
      {
        id: "outlier",
        value: "Different value",
        confidence: 0.9,
        specialistId: "specialist4",
        weight: 1.0,
      },
    ];

    // Add specialist4 to specialists for this test
    const testSpecialists = [
      ...mockSpecialists,
      {
        id: "specialist4",
        name: "Specialist 4",
        capabilities: ["evaluation", "judgment"],
        domains: ["meta"],
        execute: jest.fn().mockResolvedValue({
          specialistId: "specialist4",
          result: {},
          processingTime: 110,
        }),
        canHandle: jest.fn().mockResolvedValue({ can: true, confidence: 0.9 }),
      },
    ];

    const result = await consensusDecisionMaker.makeDecision(
      options,
      testSpecialists as Specialist[],
      mockSharedContext as SharedContext
    );

    expect(result.selectedOption.value).toBe("Same value");
    expect(result.metadata.decisionMethod).toBe("consensus");
    expect(result.metadata.consensusLevel).toBeGreaterThanOrEqual(0.7);
  });

  // Test case 4: Executive decision for low confidence situations
  it("should make an executive decision when all options have low confidence", async () => {
    // Configure decision maker with executive decision enabled and high min confidence
    const executiveDecisionMaker = new DecisionMaker(
      mockLogger as unknown as Logger,
      {
        minConfidence: 0.8, // Set high to force executive decision
        consensusThreshold: 0.9, // Set high to prevent consensus
        enableExecutiveDecision: true, // Enable executive decision
      }
    );

    // Create options with confidence below the minConfidence threshold
    const options: DecisionOption[] = [
      {
        id: "option1",
        value: "First option",
        confidence: 0.6,
        specialistId: "specialist1",
        weight: 1.0,
      },
      {
        id: "option2",
        value: "Second option",
        confidence: 0.7,
        specialistId: "specialist2",
        weight: 1.0,
      },
      {
        id: "option3",
        value: "Third option",
        confidence: 0.65,
        specialistId: "specialist3",
        weight: 1.0,
      },
    ];

    // Specialists with same IDs as options to ensure executive specialist exists
    const executiveSpecialists = [
      {
        id: "specialist1",
        name: "Executive Specialist",
        capabilities: ["math", "reasoning"],
        domains: ["general"],
        execute: jest.fn(),
        canHandle: jest.fn().mockResolvedValue({ can: true, confidence: 0.9 }),
      },
      {
        id: "specialist2",
        name: "Specialist 2",
        capabilities: ["writing"],
        domains: ["content"],
        execute: jest.fn(),
        canHandle: jest.fn().mockResolvedValue({ can: true, confidence: 0.8 }),
      },
      {
        id: "specialist3",
        name: "Specialist 3",
        capabilities: ["research"],
        domains: ["data"],
        execute: jest.fn(),
        canHandle: jest.fn().mockResolvedValue({ can: true, confidence: 0.7 }),
      },
    ];

    const result = await executiveDecisionMaker.makeDecision(
      options,
      executiveSpecialists as Specialist[],
      mockSharedContext as SharedContext
    );

    // First specialist should be selected as executive
    expect(result.selectedOption.specialistId).toBe("specialist1");
    expect(result.metadata.decisionMethod).toBe("executive");
    expect(mockLogger.warn).toHaveBeenCalled(); // Should log a warning about low confidence
  });

  // Test case 5: Error handling for empty options
  it("should handle empty options array gracefully", async () => {
    // The DecisionMaker should throw an error when given an empty options array
    await expect(async () => {
      await decisionMaker.makeDecision(
        [],
        mockSpecialists as Specialist[],
        mockSharedContext as SharedContext
      );
    }).rejects.toThrow("No decision options provided");

    // Verify that an error was logged
    expect(mockLogger.error).toHaveBeenCalled();
  });
});
