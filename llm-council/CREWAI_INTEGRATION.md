# CrewAI Integration for LLM Council

This directory contains both the main LLM Council service and an optional CrewAI-based implementation.

## Files

- **`llm_council_service.py`** - Main LLM Council service (FastAPI-based)
- **`run_council.py`** - Service runner
- **`crewai_council.py`** - Alternative CrewAI-based implementation

## CrewAI Implementation

The `crewai_council.py` provides an alternative implementation using the CrewAI framework for multi-agent orchestration.

### Installation

To use the CrewAI implementation, install the CrewAI package:

```bash
pip install crewai
```

### Usage

```python
from crewai_council import CrewAICouncil

council = CrewAICouncil()
council.register_specialist("analyst", "Data Analyst", ["data_analysis", "reporting"])
council.register_specialist("writer", "Content Writer", ["writing", "editing"])

# Execute tasks
tasks = [...]  # CrewAI Task objects
result = council.execute_plan(tasks)
```

### Features

- Specialist registration and management
- Shared memory between agents
- Tool integration
- Plan execution with context
- Integration with Space API communication layer

### Architecture Notes

The CrewAI implementation has been updated to work with the new CORE architecture:

- Uses `SpaceAPIClient` for service communication
- Uses structured logging via `service_logging`
- Gracefully handles missing CrewAI dependency
- Compatible with the independent service model

Both implementations can coexist, allowing flexibility in choosing the orchestration approach.
