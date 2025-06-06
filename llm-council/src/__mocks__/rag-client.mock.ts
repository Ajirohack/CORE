// Mock for a generic RAG client/endpoint

export const mockRagClient = {
  query: jest.fn(async (queryText: string, options?: any) => {
    if (queryText.toLowerCase().includes("error_query")) {
      return {
        success: false,
        error: "Simulated RAG query error",
        results: [],
      };
    }
    if (queryText.toLowerCase().includes("topic t")) {
      return {
        success: true,
        results: [
          {
            id: "doc1",
            score: 0.9,
            text: "Detailed information about topic T from document 1.",
            metadata: { source: "sourceA" },
          },
          {
            id: "doc2",
            score: 0.85,
            text: "More details on topic T from document 2.",
            metadata: { source: "sourceB" },
          },
        ],
      };
    }
    return {
      success: true,
      results: [
        {
          id: "default_doc",
          score: 0.7,
          text: `Default RAG response for query: ${queryText}`,
          metadata: { source: "default_source" },
        },
      ],
    };
  }),
  // Add other methods if your RAG client has them (e.g., addDocuments, status)
};

// Usage:
// jest.mock('../path/to/actual/rag-client', () => require('../__mocks__/rag-client.mock'));
