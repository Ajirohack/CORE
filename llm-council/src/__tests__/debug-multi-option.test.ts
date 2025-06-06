// A test with multiple options

import { DecisionMaker, DecisionOption } from "../decision-maker";
import { Logger } from "../utils/logger";
import { SharedContext } from "../shared-context";
import { Specialist } from "../types";

describe("Multiple Options Test", () => {
  let mockLogger: any;
  let mockSpecialists: any[];
  let mockSharedContext: any;
  
  beforeEach(() => {
    mockLogger = {
      debug: jest.fn(),
      info: jest.fn(),
      warn: jest.fn(),
      error: jest.fn(),
      log: jest.fn()
    };
    
    // Create mock specialists with multiple options
    mockSpecialists = [
      { 
        id: "specialist1", 
        name: "Specialist 1",
        capabilities: ["math"],
        domains: ["general"],
        execute: jest.fn()
      },
      { 
        id: "specialist2", 
        name: "Specialist 2",
        capabilities: ["writing"],
        domains: ["content"],
        execute: jest.fn()
      },
      { 
        id: "specialist3", 
        name: "Specialist 3",
        capabilities: ["research"],
        domains: ["data"],
        execute: jest.fn()
      }
    ];
    
    // Create mock shared context
    mockSharedContext = {
      getUserPreferences: jest.fn().mockReturnValue({}),
      getMemory: jest.fn().mockReturnValue({}),
      addToContext: jest.fn()
    };
  });

  // Test weighted voting
  it("should choose the option with highest weighted score", async () => {
    const decisionMaker = new DecisionMaker(mockLogger as unknown as Logger, {
      minConfidence: 0.1,
      consensusThreshold: 0.9,
      enableExecutiveDecision: false
    });
    
    const options: DecisionOption[] = [
      { 
        id: "option1", 
        value: "Option 1", 
        confidence: 0.7, 
        specialistId: "specialist1", 
        weight: 0.9
      },
      {
        id: "option2",
        value: "Option 2",
        confidence: 0.8,
        specialistId: "specialist2",
        weight: 0.5
      },
      {
        id: "option3",
        value: "Option 3",
        confidence: 0.6,
        specialistId: "specialist3",
        weight: 0.3
      }
    ];
    
    const result = await decisionMaker.makeDecision(
      options,
      mockSpecialists as Specialist[],
      mockSharedContext as SharedContext
    );
    
    console.log('TEST - Weighted voting result:', {
      selectedOption: result.selectedOption,
      method: result.metadata.decisionMethod,
      confidence: result.confidence
    });
    
    expect(result.selectedOption.id).toBe("option1");
    expect(result.metadata.decisionMethod).toBe("weighted-voting");
  });
});
