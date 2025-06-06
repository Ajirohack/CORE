// A more complete debug test for the decision maker

import { DecisionMaker, DecisionOption } from "../decision-maker";
import { Logger } from "../utils/logger";
import { SharedContext } from "../shared-context";
import { Specialist } from "../types";

describe("Debug Decision Maker Test", () => {
  let mockLogger: any;
  let mockSpecialists: any[];
  let mockSharedContext: any;

  beforeEach(() => {
    mockLogger = {
      debug: jest.fn(),
      info: jest.fn(),
      warn: jest.fn(),
      error: jest.fn(),
      log: jest.fn(),
    };

    // Create mock specialists
    mockSpecialists = [
      {
        id: "specialist1",
        name: "Specialist 1",
        capabilities: ["math"],
        domains: ["general"],
        execute: jest.fn(),
      },
    ];

    // Create mock shared context
    mockSharedContext = {
      getUserPreferences: jest.fn().mockReturnValue({}),
      getMemory: jest.fn().mockReturnValue({}),
      addToContext: jest.fn(),
    };
  });

  // Debug test for weighted voting
  it("should execute the weighted voting method correctly", async () => {
    // Create decision maker with high min confidence so we test only weighted voting
    const decisionMaker = new DecisionMaker(mockLogger as unknown as Logger, {
      minConfidence: 0.1, // Very low threshold to ensure weighted voting passes
      consensusThreshold: 0.9,
      enableExecutiveDecision: false, // Disable executive decision as fallback
    });

    // Create options where option1 should win by weighted voting
    const options: DecisionOption[] = [
      {
        id: "option1",
        value: "Option 1",
        confidence: 0.8,
        specialistId: "specialist1",
        weight: 0.9,
      },
    ];

    // Call makeDecision
    const result = await decisionMaker.makeDecision(
      options,
      mockSpecialists as Specialist[],
      mockSharedContext as SharedContext
    );

    console.log("DEBUG - Decision Result:", {
      selectedOption: result.selectedOption,
      method: result.metadata.decisionMethod,
      confidence: result.confidence,
    });

    // Check if weighted voting was used
    expect(result.selectedOption.id).toBe("option1");
    expect(result.metadata.decisionMethod).toBe("weighted-voting");
  });
});
