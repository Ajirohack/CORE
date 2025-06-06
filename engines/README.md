# SpaceNew Engines

This directory contains pluggable engine implementations for the "the-space" architecture. Each engine is responsible for a specific backend or processing task within the workflow pipeline.

## Subdirectories

- **engine1/**: Workflow Execution Engine - Manages workflow processing and execution tracking
- **engine2/**: Data Processing & Transformation Engine - Handles data enrichment and transformation
- **engine3/**: AI Processing & Reasoning Engine - Provides AI reasoning, planning and decision-making
- **engine4/**: Action & Integration Engine - Executes actions and integrates with external systems
- **src/**: Shared engine source code and utilities used across all engines

## Engine Pipeline

The engines work together in a sequential pipeline:

1. **Engine 1** receives workflow requests and manages execution
2. **Engine 2** processes and transforms the data from Engine 1
3. **Engine 3** applies AI reasoning and planning to the transformed data
4. **Engine 4** executes the final actions and delivers results

Each engine has its own specialized agents and workflows tailored to its role in the pipeline.

## Implementation Status

- [x] Basic directory structure for all engines
- [x] Documentation for each engine subdirectory
- [x] Workflow execution framework in Engine 1
- [ ] Agent implementations across all engines
- [ ] Workflow definitions for standard processing patterns
- [ ] Integration between engines and with other core components (RAG, AI Council)
- [ ] Complete error handling and monitoring

## Next Steps

1. Implement agent frameworks across all engines
2. Define standard workflow patterns for common use cases
3. Establish integration points between engines and other core components
4. Add comprehensive monitoring, logging, and error handling

> See implementation-checklist.md for detailed progress tracking.

---

*Last Updated: May 10, 2025*
