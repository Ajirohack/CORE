// A simplified test for the decision maker

import { DecisionMaker } from "../decision-maker";
import { Logger } from "../utils/logger";

describe("Simple Decision Maker Test", () => {
  let mockLogger: any;

  beforeEach(() => {
    mockLogger = {
      debug: jest.fn(),
      info: jest.fn(),
      warn: jest.fn(),
      error: jest.fn(),
      log: jest.fn(),
    };
  });

  it("should be defined", () => {
    const decisionMaker = new DecisionMaker(mockLogger as unknown as Logger);
    expect(decisionMaker).toBeDefined();
  });
});
