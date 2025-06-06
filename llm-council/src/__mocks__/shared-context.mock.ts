export class SharedContext {
  public readonly id: string = "mock-context-id";
  public readonly originalRequest: any = {};
  public readonly metadata: {
    userId?: string;
    sessionId?: string;
    timestamp: number;
    [key: string]: any;
  } = {
    userId: "mock-user-id",
    sessionId: "mock-session-id",
    timestamp: Date.now(),
  };

  private specialistResults: Map<string, any> = new Map();
  private memoryData: Map<string, any> = new Map();
  private variables: Map<string, any> = new Map();

  constructor(request: any = {}) {
    this.originalRequest = request;
  }

  setSpecialistResult = jest.fn((specialistId: string, result: any) => {
    this.specialistResults.set(specialistId, result);
    return this;
  });

  getSpecialistResult = jest.fn((specialistId: string) => {
    return this.specialistResults.get(specialistId);
  });

  getAllSpecialistResults = jest.fn(() => {
    return Array.from(this.specialistResults.entries()).reduce(
      (acc, [key, value]) => {
        acc[key] = value;
        return acc;
      },
      {} as Record<string, any>
    );
  });

  setMemoryData = jest.fn((key: string, value: any) => {
    this.memoryData.set(key, value);
    return this;
  });

  getMemoryData = jest.fn((key: string) => {
    return this.memoryData.get(key);
  });

  setVariable = jest.fn((key: string, value: any) => {
    this.variables.set(key, value);
    return this;
  });

  getVariable = jest.fn((key: string) => {
    return this.variables.get(key);
  });

  logProgress = jest.fn((phase: string, data: any) => {
    return this;
  });
}

export const mockSharedContext = new SharedContext();
