# Tools/Packages System for Space WH

This module implements the Tools/Packages System component of Space WH using Model Context Protocol (MCP). The Tools/Packages System provides:

- Standardized tool interfaces
- Schema-based validation
- Mode-based access control
- Safe tool execution

## Usage

```python
from core.tools_packages.src.tools_system import ToolsSystem

# Initialize the tools system
tools = ToolsSystem()

# Register a custom tool
@tools.register_tool(
    name="calculator",
    description="Perform basic calculations",
    required_permissions=["basic_tools"]
)
def calculator(operation: str, a: float, b: float) -> float:
    """Perform basic calculations."""
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b == 0:
            raise ValueError("Division by zero")
        return a / b
    else:
        raise ValueError(f"Unsupported operation: {operation}")

# Execute a tool
response = tools.execute_tool(
    tool_id="calculator",
    parameters={
        "operation": "add",
        "a": 5,
        "b": 3
    },
    mode="archivist"  # Mode determines access permissions
)

# Print the result
if response.success:
    print(f"Result: {response.result}")
else:
    print(f"Error: {response.error}")
```

## Components

- `tools_system.py`: Main entry point for the tools functionality
- `tool_registry.py`: Manages tool registration and discovery
- `tool_executor.py`: Handles tool execution with safety measures
- `access_control.py`: Manages access permissions for tools
- `schemas.py`: Defines data structures for tools and requests

## Access Modes

The system includes four default access modes with increasing permission levels:

1. **Archivist**: Basic access mode with limited permissions
   - Permissions: `basic_tools`, `read_knowledge`

2. **Orchestrator**: Standard access mode with moderate permissions
   - Permissions: `basic_tools`, `read_knowledge`, `write_knowledge`, `advanced_tools`

3. **Godfather**: Advanced access mode with extended permissions
   - Permissions: `basic_tools`, `read_knowledge`, `write_knowledge`, `advanced_tools`, `admin_tools`

4. **Entity**: Full access mode with all permissions
   - Permissions: `basic_tools`, `read_knowledge`, `write_knowledge`, `advanced_tools`, `admin_tools`, `unrestricted`

## Tool Registration

Tools can be registered in three ways:

1. **Decorator**: Using the `@tools.register_tool` decorator
2. **Function Introspection**: Using `registry.register_from_function()`
3. **Manual Registration**: Using `registry.register_tool()` with a manifest

## Integration Points

- Used by AI Council for tool execution
- Integrated with RAG System for knowledge tools
- Provides tools to System Engine Control for workflows

## TODO: Core Completion Tasks (May 2025)

- [ ] Expand tool registration with more real-world examples
- [ ] Implement advanced tool execution logic (error handling, async, etc.)
- [ ] Ensure seamless integration with RAG and AI Council modules

> See implementation-checklist.md for progress tracking. Update this section as each feature is completed.
