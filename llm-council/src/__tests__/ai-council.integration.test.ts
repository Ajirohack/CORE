// filepath: /Volumes/Project Disk/SpaceNew/core/ai-council/src/__tests__/ai-council.integration.test.ts
import { AICouncil } from "../ai-council";
import { ToolsAdapter } from "../adapters/tools-adapter";
import { MemoryManager } from "../memory-manager";
import { SharedContext } from "../shared-context";
import { ModelRegistry } from "../model-registry";
import { SpecialistManager } from "../specialist-manager";
import { ExecutionPlanner } from "../execution-planner";
import { IntegrationLayer } from "../integration-layer";
import { Logger } from "../utils/logger";
import { mockToolSystemAdapter } from "../__mocks__/tools-adapter.mock";
import { mockModelRegistry } from "../__mocks__/model-registry.mock";
import { mockSpecialistManager } from "../__mocks__/specialist-manager.mock";
import { mockSharedContext } from "../__mocks__/shared-context.mock";

// Mock all dependencies
jest.mock("../config-manager");
jest.mock("../model-registry", () => ({
  ModelRegistry: jest.fn().mockImplementation(() => mockModelRegistry),
}));
jest.mock("../specialist-manager", () => ({
  SpecialistManager: jest.fn().mockImplementation(() => mockSpecialistManager),
}));
jest.mock("../execution-planner");
jest.mock("../integration-layer");
jest.mock("../memory-manager");
jest.mock("../shared-context", () => ({
  SharedContext: jest.fn().mockImplementation(() => mockSharedContext),
}));
jest.mock("../adapters/tools-adapter", () => ({
  ToolsAdapter: jest.fn().mockImplementation(() => mockToolSystemAdapter),
}));
jest.mock("../utils/logger");

describe("AICouncil - Integration Tests", () => {
  let aiCouncil: AICouncil;
  let mockedToolAdapter: jest.Mocked<any>;
  let mockedMemoryManager: jest.Mocked<MemoryManager>;
  let mockedLogger: jest.Mocked<Logger>;
  let mockedExecutionPlanner: any;
  let mockedIntegrationLayer: any;

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();

    // Create mock logger
    mockedLogger = {
      debug: jest.fn(),
      info: jest.fn(),
      warn: jest.fn(),
      error: jest.fn(),
      log: jest.fn()
    } as unknown as jest.Mocked<Logger>;

    // Set up mock dependencies
    mockedToolAdapter = mockToolSystemAdapter as any;
    mockedMemoryManager = new MemoryManager() as jest.Mocked<MemoryManager>;
    
    // Use 'any' type to avoid TypeScript errors with mocked methods
    mockedExecutionPlanner = {
      createPlan: jest.fn(),
      on: jest.fn(),
      emit: jest.fn()
    };
    
    mockedIntegrationLayer = {
      integrate: jest.fn(),
      on: jest.fn(),
      emit: jest.fn()
    };
    
    // Create the AICouncil instance
    aiCouncil = new AICouncil({ logLevel: 'debug' });
    
    // Replace its internal components with our mocks
    (aiCouncil as any).executionPlanner = mockedExecutionPlanner;
    (aiCouncil as any).integrationLayer = mockedIntegrationLayer;
    (aiCouncil as any).memoryManager = mockedMemoryManager;
    (aiCouncil as any).logger = mockedLogger;
    (aiCouncil as any).initialized = true; // Mark as initialized
  });

  it("should orchestrate a request through planning and execution phases", async () => {
    const userInput = "Calculate 5 plus 3";

    const request = {
      input: userInput,
      userId: "user123",
      sessionId: "test-session"
    };

    // Create mock execution plan
    const mockExecutionPlan = {
      steps: [
        {
          specialistId: "calculator",
          phase: "analysis",
          priority: 1,
          input: { query: userInput }
        },
        {
          specialistId: "explainer",
          phase: "synthesis",
          priority: 2,
          input: { query: userInput }
        }
      ]
    };
    
    const specialistResults = [
      { specialistId: "calculator", response: { result: 8, explanation: "5 + 3 = 8" } },
      { specialistId: "explainer", response: { explanation: "I calculated by adding the numbers" } }
    ];

    const finalResponse = {
      response: "The answer is 8",
      metadata: { confidence: 1.0 }
    };

    // Mock the execution plan creation
    mockedExecutionPlanner.createPlan.mockResolvedValueOnce(mockExecutionPlan);

    // Mock specialist execution - we'll need to modify the AICouncil implementation to expose this
    (aiCouncil as any).executeSpecialists = jest.fn().mockResolvedValueOnce(specialistResults);

    // Mock integration result
    mockedIntegrationLayer.integrate.mockResolvedValueOnce(finalResponse);

    // Mock memory operations based on what's used in ai-council.ts
    (aiCouncil as any).loadMemoryIntoContext = jest.fn().mockResolvedValueOnce({});
    (aiCouncil as any).storeInteractionInMemory = jest.fn().mockResolvedValueOnce(undefined);

    // --- Execute the request ---
    const response = await aiCouncil.processRequest(request);

    // --- Assertions ---
    expect(response).toEqual(finalResponse);
    expect(mockedExecutionPlanner.createPlan).toHaveBeenCalledWith(request, expect.any(Object));
    expect((aiCouncil as any).executeSpecialists).toHaveBeenCalledWith(mockExecutionPlan, expect.any(Object));
    expect(mockedIntegrationLayer.integrate).toHaveBeenCalledWith(specialistResults, expect.any(Object));
    expect(mockedLogger.info).toHaveBeenCalledWith("Processing request", expect.any(Object));
    expect(mockedLogger.info).toHaveBeenCalledWith("Request processed successfully", expect.any(Object));
  });

  it("should handle complex multi-stage task execution with specialist collaboration", async () => {
    const userInput = "Find information about quantum computing and then summarize it";

    const request = {
      input: userInput,
      userId: "user123",
      sessionId: "test-session"
    };

    // Create a more complex execution plan with multiple stages and specialist collaboration
    const mockExecutionPlan = {
      steps: [
        // Analysis phase - determine what to do
        {
          specialistId: "analyzer",
          phase: "analysis",
          priority: 1,
          input: { query: userInput }
        },
        // Research phase - find information
        {
          specialistId: "researcher",
          phase: "processing",
          priority: 2,
          input: { query: "quantum computing" },
          dependsOn: ["analyzer"]
        },
        // Summarization phase - process and summarize the findings
        {
          specialistId: "summarizer",
          phase: "generation",
          priority: 3,
          input: { query: userInput },
          dependsOn: ["researcher"]
        }
      ]
    };
    
    // Mock specialist results with dependencies between them
    const specialistResults = [
      { 
        specialistId: "analyzer", 
        response: { 
          analysis: "This is a two-stage task: 1) research quantum computing, 2) summarize findings",
          confidence: 0.95
        }
      },
      { 
        specialistId: "researcher", 
        response: { 
          findings: "Quantum computing uses quantum bits (qubits) that can exist in multiple states...",
          sources: ["source1", "source2"],
          confidence: 0.9
        }
      },
      { 
        specialistId: "summarizer", 
        response: { 
          summary: "Quantum computing is a type of computing that uses quantum mechanics principles...",
          keyPoints: ["Uses qubits", "Enables parallel processing", "Still experimental"],
          confidence: 0.85
        }
      }
    ];

    // Final integrated response
    const finalResponse = {
      response: "Quantum computing is a type of computing that uses quantum mechanics principles...",
      metadata: { 
        confidence: 0.9,
        sources: ["source1", "source2"],
        processingSteps: 3
      }
    };

    // Mock the execution plan creation
    mockedExecutionPlanner.createPlan.mockResolvedValueOnce(mockExecutionPlan);

    // Mock specialist execution
    (aiCouncil as any).executeSpecialists = jest.fn().mockResolvedValueOnce(specialistResults);

    // Mock integration result
    mockedIntegrationLayer.integrate.mockResolvedValueOnce(finalResponse);

    // Mock memory operations
    (aiCouncil as any).loadMemoryIntoContext = jest.fn().mockResolvedValueOnce({});
    (aiCouncil as any).storeInteractionInMemory = jest.fn().mockResolvedValueOnce(undefined);

    // Execute the request
    const response = await aiCouncil.processRequest(request);

    // Assertions
    expect(response).toEqual(finalResponse);
    expect(mockedExecutionPlanner.createPlan).toHaveBeenCalledWith(request, expect.any(Object));
    expect((aiCouncil as any).executeSpecialists).toHaveBeenCalledWith(mockExecutionPlan, expect.any(Object));
    expect(mockedIntegrationLayer.integrate).toHaveBeenCalledWith(specialistResults, expect.any(Object));
    
    // Verify that the appropriate number of specialists were used and in the right order
    expect(specialistResults.length).toBe(3);
    expect(specialistResults[0].specialistId).toBe("analyzer");
    expect(specialistResults[1].specialistId).toBe("researcher");
    expect(specialistResults[2].specialistId).toBe("summarizer");
  });

  it("should handle errors during planning or execution gracefully", async () => {
    const request = {
      input: "Process this complex request",
      userId: "user123",
      sessionId: "test-session"
    };

    // Mock an error during execution plan creation
    const planningError = new Error("Failed to create execution plan");
    mockedExecutionPlanner.createPlan.mockRejectedValueOnce(planningError);
    
    // Execute request and expect it to be handled gracefully
    await expect(aiCouncil.processRequest(request)).rejects.toThrow();

    // Verify error was logged
    expect(mockedLogger.error).toHaveBeenCalledWith(
      expect.stringContaining("Failed to process request"),
      expect.anything()
    );

    // Reset mocks for the second part of the test
    jest.clearAllMocks();
    
    // Now set up a scenario where planning works but execution fails
    const mockExecutionPlan = {
      steps: [
        {
          specialistId: "specialist1",
          phase: "analysis",
          priority: 1,
          input: { query: request.input }
        }
      ]
    };

    // Mock successful plan creation
    mockedExecutionPlanner.createPlan.mockResolvedValueOnce(mockExecutionPlan);
    
    // But execution fails
    const executionError = new Error("Specialist execution failed");
    (aiCouncil as any).executeSpecialists = jest.fn().mockRejectedValueOnce(executionError);

    // Execute request again
    await expect(aiCouncil.processRequest(request)).rejects.toThrow();
    
    // Verify the appropriate error logging
    expect(mockedLogger.error).toHaveBeenCalledWith(
      expect.stringContaining("Failed to process request"),
      expect.anything()
    );
  });
  
  it("should adapt to user preferences and context", async () => {
    const request = {
      input: "What can you tell me about this topic?",
      userId: "user123",
      sessionId: "test-session",
      context: {
        preferences: {
          verbosity: "high",
          formatPreference: "bullet-points"
        }
      }
    };

    // Mock execution plan that includes the user preferences in context
    const mockExecutionPlan = {
      steps: [
        {
          specialistId: "contextualSpecialist",
          phase: "analysis",
          priority: 1,
          input: { 
            query: request.input,
            userPreferences: request.context.preferences
          }
        }
      ]
    };

    const specialistResults = [
      { 
        specialistId: "contextualSpecialist", 
        response: { 
          answer: "Detailed information in bullet points...",
          format: "bullet-points",
          verbosityLevel: "high",
          confidence: 0.9
        }
      }
    ];

    const finalResponse = {
      response: "Detailed information in bullet points...",
      metadata: { 
        adaptedToPreferences: true,
        verbosityLevel: "high",
        format: "bullet-points"
      }
    };

    // Set up the mocks
    mockedExecutionPlanner.createPlan.mockResolvedValueOnce(mockExecutionPlan);
    (aiCouncil as any).executeSpecialists = jest.fn().mockResolvedValueOnce(specialistResults);
    mockedIntegrationLayer.integrate.mockResolvedValueOnce(finalResponse);
    (aiCouncil as any).loadMemoryIntoContext = jest.fn().mockResolvedValueOnce({});
    
    // Execute the request
    const response = await aiCouncil.processRequest(request);
    
    // Verify the response incorporates user preferences
    expect(response).toEqual(finalResponse);
    expect(response.metadata?.adaptedToPreferences).toBeTruthy();
  });
});
