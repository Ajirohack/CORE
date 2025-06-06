# SpaceNew Tools System Integration

## Overview

This module expands the core Tool/Packages system to integrate with other SpaceNew components:

- RAG system for knowledge retrieval and memory management
- AI Council for orchestration and capability sharing
- Memory/context sharing between systems

## Components

### 1. Tool Integration (`tool_integration.py`)

Provides integration points between the tool system and other components:

- Tool discovery and execution from the RAG system
- Tool registration with AI Council
- Memory and context sharing between tools and other systems

### 2. AI Council Connector (`ai_council_connector.py`)

Specialized connector for AI Council integration:

- Registration of tools as AI Council capabilities
- Shared context management between tools and council
- Tool execution from AI Council requests
- Memory sharing with the AI Council system

### 3. RAG Connector (`rag_connector.py`)

Specialized connector for RAG system integration:

- Knowledge retrieval from RAG for tool execution
- Feeding tool execution results to RAG memory
- Context-aware tool execution with RAG integration

### 4. Memory/Context Orchestrator (`memory_context_orchestrator.py`)

Central memory and context management:

- Unified memory interfaces for short-term and long-term memory
- Context sharing with appropriate scoping (request, session, user, global)
- Pub/sub mechanism for context updates
- Integration with RAG system and AI Council

### 5. Integrated Tools System (`tools_system_integration.py`)

Unified facade for the entire tools system:

- Core tool registration and execution
- Integration with RAG system and AI Council
- Memory and context sharing
- Enhanced tool execution with context enrichment

## Memory Types and Context Scopes

### Memory Types

The system supports several memory types:

- **Factual**: Facts and information (default, long persistence)
- **Procedural**: How to perform tasks (high persistence)
- **Episodic**: Events and experiences (medium persistence)
- **Conversation**: Dialog history (variable persistence)
- **Entity**: Information about specific entities (high persistence)
- **System**: System state and metadata (high persistence)

### Context Scopes

Memories are managed at different scopes:

- **Request**: Only for the current request (temporary)
- **Session**: For the current session (medium-term)
- **User**: Specific to a user across sessions (long-term)
- **Global**: Available to all users and sessions (permanent)

## Advanced Features

### Hybrid RAG Integration

We've implemented hybrid search integration with the RAG system combining:

- **Dense Retrieval**: Vector embeddings for semantic similarity
- **Sparse Retrieval**: BM25/lexical search for keyword matching
- **Knowledge Graph**: Graph-based retrieval for concept relationships

Results are combined with weighted scoring to provide more comprehensive and accurate retrievals.

### Memory Importance Scoring

Memories are scored for importance based on:

- **Explicit Importance**: Assigned by tools during creation
- **Usage Frequency**: Frequently accessed memories gain importance
- **Recency**: More recent memories may have higher importance
- **Relevance**: Contextual relevance to current operations

### Memory Lifecycle

1. **Creation**: Memory created during tool execution
2. **Short-term Storage**: Initially stored in short-term memory
3. **Importance Assessment**: Evaluated for long-term storage
4. **Long-term Storage**: Important memories persisted to RAG system
5. **Retrieval**: Retrieved when relevant to context
6. **Decay/Archive**: Eventually archived or forgotten based on relevance

## Testing

Comprehensive integration tests have been implemented to verify:

- Memory sharing between systems
- Context enrichment from multiple sources
- Memory persistence across sessions
- Tool execution with RAG knowledge
- Knowledge graph integration

Run the tests with:

```bash
cd /Volumes/Project\ Disk/SpaceNew/tests/core/packages/integration/
./run_integration_tests.py --group all
```

Specific test groups can be run with:

```bash
./run_integration_tests.py --group rag    # RAG integration tests
./run_integration_tests.py --group tools  # Tools integration tests
./run_integration_tests.py --group ai_council  # AI Council integration tests
./run_integration_tests.py --group memory  # Memory/context sharing tests
```

## Usage Examples

### Registering and Executing Tools with Integration

```python
from core.packages.src.tools_system_integration import IntegratedToolsSystem
from core.packages.src.schemas import ToolManifest, ToolExecutionRequest

# Create integrated tools system
tools_system = IntegratedToolsSystem()

# Register a tool
manifest = ToolManifest(
    id="web_search",
    name="Web Search",
    description="Search the web for information",
    parameters={
        "query": {"type": "string", "description": "Search query"},
        "engine": {"type": "string", "description": "Search engine to use", "default": "google"}
    },
    required_permissions=["web_access"]
)

def web_search_implementation(params, context):
    query = params.get("query")
    engine = params.get("engine", "google")
    # Implementation details...
    return {"results": [...]}

tools_system.register_tool(manifest, web_search_implementation)

# Execute a tool with context
request = ToolExecutionRequest(
    tool_id="web_search",
    parameters={"query": "SpaceNew architecture"},
    request_id="req-123",
    mode="standard",
    user_id="user-456",
    metadata={"session_id": "sess-789"}
)

result = tools_system.execute_tool(request)
```

### Connecting to RAG and AI Council

```python
from core.rag_system.rag_system import RAGSystem
from core.ai_council.ai_council import AICouncil

# Initialize systems
rag_system = RAGSystem()
ai_council = AICouncil()

# Connect to integrated tools system
tools_system.connect_rag_system(rag_system)
tools_system.connect_ai_council(ai_council)
```

### Using Memory and Context

```python
# Set user preferences
tools_system.set_user_preference("user-123", "preferred_search_engine", "duckduckgo")

# Get user preference in tool implementation
def search_implementation(params, context):
    user_id = context.get("user_id")
    preferred_engine = tools_system.get_user_preference(user_id, "preferred_search_engine", "google")
    # Use preferred engine...

# Share memory between systems
tools_system.memory_context_orchestrator.add_to_long_term_memory(
    memory_data={"important_fact": "SpaceNew architecture has three main components"},
    metadata={"source": "documentation"},
    importance=0.8,
    memory_type="factual"
)
```

## Integration Flow

1. **Tool Execution Flow**:
   - Tool execution request received
   - Context enriched with user preferences, session data, etc.
   - RAG system provides relevant knowledge
   - Tool executed with enriched context
   - Results stored in memory and shared with other systems

2. **Memory Flow**:
   - Short-term memory for temporary storage
   - Long-term memory via RAG system
   - Memory sharing with AI Council for specialist agents
   - Context scoping (request, session, user, global)

3. **Context Sharing**:
   - Context updates propagated via pub/sub
   - User preferences persisted and shared
   - Session context maintained for conversation flow
   - Global context for system-wide settings

## Implementation Notes

- Thread-safe context management
- Cached memory for performance
- Fallbacks when systems are not connected
- Unified interfaces for easy integration
