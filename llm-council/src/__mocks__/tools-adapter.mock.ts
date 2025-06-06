// Mock for core/ai-council/src/adapters/tools-adapter.ts

// Simulates the ToolsSystem from core/packages
const mockToolsSystem = {
  calculator: {
    description: "Perform basic calculations",
    required_permissions: ["basic_tools"],
    execute: (params: { operation: string; a: number; b: number }) => {
      if (params.operation === "add") return params.a + params.b;
      if (params.operation === "subtract") return params.a - params.b;
      // ... other operations
      throw new Error("Unsupported operation");
    },
  },
  knowledgeSearch: {
    description: "Searches the knowledge base (simulates RAG)",
    required_permissions: ["read_knowledge"],
    execute: async (params: { query: string }) => {
      if (params.query.includes("topic T")) {
        return "Information about topic T found via RAG.";
      }
      return "No information found.";
    },
  },
  // Add more mock tools as needed for testing
};

export const mockToolSystemAdapter = {
  listTools: jest.fn(async (mode: string) => {
    // Simulate permission-based filtering if necessary
    return Object.entries(mockToolsSystem).map(([name, tool]) => ({
      id: name,
      name: name,
      description: tool.description,
      // Add other relevant tool properties if your adapter expects them
    }));
  }),
  executeTool: jest.fn(
    async (toolId: string, parameters: any, mode: string) => {
      if (mockToolsSystem[toolId]) {
        try {
          const result = await mockToolsSystem[toolId].execute(parameters);
          return { success: true, result: result };
        } catch (error) {
          return { success: false, error: error.message };
        }
      }
      return { success: false, error: `Tool ${toolId} not found` };
    }
  ),
  // Add any other methods your actual tools-adapter.ts might have
};

// This allows you to do: jest.mock('../adapters/tools-adapter', () => require('../__mocks__/tools-adapter.mock'));
// Or configure Jest moduleNameMapper to pick this up automatically.
