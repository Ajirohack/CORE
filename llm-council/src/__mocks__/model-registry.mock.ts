import { Logger } from "../utils/logger";

export class ModelRegistry {
  private logger: Logger;
  private models: Map<string, any> = new Map();

  constructor(logger: Logger) {
    this.logger = logger;
  }

  registerModel = jest.fn((modelId: string, modelConfig: any) => {
    this.models.set(modelId, modelConfig);
    return true;
  });

  getModel = jest.fn((modelId: string) => {
    return this.models.get(modelId);
  });

  listModels = jest.fn(() => {
    return Array.from(this.models.entries()).map(([id, config]) => ({
      id,
      ...config,
    }));
  });

  executeModel = jest.fn(async (modelId: string, input: any) => {
    this.logger.debug(`Mock executing model: ${modelId}`);
    return {
      modelId,
      result: `Mock result for ${modelId} with input: ${JSON.stringify(input)}`,
      usage: { prompt_tokens: 10, completion_tokens: 20, total_tokens: 30 },
    };
  });
}

export const mockModelRegistry = (logger: Logger) => new ModelRegistry(logger);
