# LLM Instructions for Working with the Superior RAG Codebase

---

```markdown
# LLM Instructions for Working with the Superior RAG Codebase

This document provides detailed instructions for AI assistants when working with the Superior RAG codebase. These guidelines help ensure consistent, high-quality modifications and development.

## General Guidelines

1. **Always Understand Before Modifying**
   - Thoroughly analyze the existing code structure and patterns before making changes
   - Identify dependencies and potential side effects of modifications
   - Respect the existing architectural decisions and patterns

2. **Code Improvements vs. Replacements**
   - Always try to improve existing code rather than completely replacing it
   - Maintain compatibility with other system components
   - Preserve important implementation details when refactoring

3. **Error Handling and Validation**
   - Maintain robust error handling throughout the codebase
   - Validate inputs at service boundaries
   - Log appropriate information for debugging while respecting privacy

4. **Testing Considerations**
   - Consider how changes can be tested effectively
   - Suggest appropriate test strategies for new functionality
   - Ensure changes don't break existing test cases

## Project Structure

The project follows a layered architecture with clear separation of concerns:

```
superior-rag/
├── docker/            - Docker configuration files
├── src/               - Source code
│   ├── api/           - API endpoints and middleware
│   ├── core/          - Core processing modules
│   ├── retrieval/     - Retrieval mechanisms
│   ├── memory/        - Memory management
│   ├── storage/       - Database interfaces
│   ├── integration/   - External integrations
│   └── utils/         - Utility functions
├── ui/                - User interfaces
├── scripts/           - Helper scripts
├── tests/             - Test suite
├── config/            - Configuration files
└── docs/              - Documentation
```

## Detailed Layer Guidelines

### API Layer (`src/api/`)

- **Purpose**: External interfaces, request handling, response formatting
- **Guidelines**:
  - Follow RESTful design principles
  - Keep route handlers lightweight, delegating business logic to core services
  - Implement proper validation, authentication, and error handling
  - Use dependency injection pattern consistently

### Core Layer (`src/core/`)

- **Purpose**: Central business logic, query processing, document handling
- **Guidelines**:
  - Keep methods focused on single responsibilities
  - Ensure proper error propagation and logging
  - Maintain asynchronous patterns consistently
  - Document complex algorithms clearly with comments

### Retrieval Layer (`src/retrieval/`)

- **Purpose**: Different retrieval strategies and fusion mechanisms
- **Guidelines**:
  - Follow interface contracts for retrievers
  - Ensure proper score normalization across different retrievers
  - Optimize for both effectiveness and efficiency
  - Document the strengths and limitations of each retriever

### Memory Layer (`src/memory/`)

- **Purpose**: Different memory types (working, short-term, long-term)
- **Guidelines**:
  - Respect TTL (time-to-live) configurations
  - Implement proper serialization/deserialization
  - Consider memory usage and optimization
  - Follow established memory management patterns

### Storage Layer (`src/storage/`)

- **Purpose**: Database interfaces for different storage types
- **Guidelines**:
  - Maintain clean separation between storage technologies
  - Use proper connection pooling and resource management
  - Implement efficient querying patterns
  - Handle connection failures gracefully

### Integration Layer (`src/integration/`)

- **Purpose**: Connections to external systems and LLMs
- **Guidelines**:
  - Handle API rate limits and retries
  - Implement proper caching strategies
  - Abstract provider-specific details
  - Support multiple service providers where possible

## Code Style Guidelines

1. **Python Best Practices**
   - Follow PEP 8 style guidelines
   - Use type hints consistently
   - Write descriptive docstrings in Google style format
   - Use meaningful variable and function names

2. **Asynchronous Programming**
   - Use `async`/`await` patterns consistently
   - Properly handle concurrent operations
   - Avoid blocking operations in asynchronous code
   - Use asyncio primitives appropriately

3. **Error Handling**
   - Use specific exception types
   - Provide meaningful error messages
   - Log exceptions with appropriate context
   - Recover gracefully when possible

4. **Logging**
   - Use the appropriate log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   - Include relevant context in log messages
   - Avoid logging sensitive information
   - Use structured logging where appropriate

## Working with Database Components

### Vector Database (Qdrant)

- Use the provided vector store interface
- Respect vector dimensionality in the configuration
- Handle collection creation and management carefully
- Consider performance implications of vector operations

### Relational Database (PostgreSQL)

- Use parameterized queries to prevent SQL injection
- Follow the established schema design
- Use transactions where appropriate
- Consider indexing strategy for queries

### Graph Database (Neo4j)

- Use Cypher queries with parameters
- Follow the established node/relationship patterns
- Consider query performance for graph traversals
- Handle graph database connection issues appropriately

### Cache (Redis)

- Use appropriate data structures (strings, hashes, sets)
- Set proper TTL values based on data type
- Implement cache invalidation strategies
- Handle serialization/deserialization consistently

## Debugging and Troubleshooting Checklist

When adding new code or fixing issues, ensure you:

1. **Check Docker Services**
   - Verify all required services are running
   - Check container logs for errors
   - Ensure proper networking between containers
   - Validate service configuration

2. **Verify Database Connections**
   - Confirm connection strings are correct
   - Check authentication credentials
   - Verify database schema is properly initialized
   - Validate query execution

3. **LLM Integration Issues**
   - Verify API keys and endpoints
   - Check rate limits and quotas
   - Handle token limits appropriately
   - Implement proper error handling for API failures

4. **Memory Management**
   - Ensure proper TTL settings
   - Check cache key namespaces
   - Verify proper serialization/deserialization
   - Monitor memory usage for potential leaks

5. **Port Configuration**
   - Check for port conflicts before binding services
   - Verify port exposure in Docker configuration
   - Ensure consistent port configuration across components
   - Validate network connectivity between services

## Implementation Strategy

When implementing new features or fixing bugs:

1. **First, understand the existing code thoroughly**
   - Read the relevant modules and their interactions
   - Understand the data flow and core functionality
   - Identify key interfaces and contracts

2. **Plan your changes carefully**
   - Start with small, focused changes
   - Test each component individually
   - Build incrementally toward the full solution
   - Consider backward compatibility

3. **Follow the modular architecture**
   - Keep changes isolated to appropriate modules
   - Respect layer boundaries and interfaces
   - Maintain separation of concerns
   - Avoid tight coupling between components

4. **Document your changes**
   - Update docstrings and comments as needed
   - Explain complex algorithms or decisions
   - Note any configuration changes required
   - Include examples for API changes

## Version Control Best Practices

When suggesting code changes:

1. **Organize changes logically**
   - Group related changes together
   - Make each change focused and purposeful
   - Separate refactoring from feature additions
   - Keep changes as small as practical

2. **Follow commit message guidelines**
   - Use clear, descriptive commit messages
   - Reference issue numbers when applicable
   - Separate subject from body with a blank line
   - Use imperative mood in commit subjects

3. **Consider backward compatibility**
   - Avoid breaking existing functionality
   - Provide migration paths for data changes
   - Update documentation for API changes
   - Consider configuration updates needed

## Important Architectural Patterns

Be aware of these key patterns used throughout the codebase:

1. **Singleton Pattern**
   - Used for database connections, caches, and managers
   - Ensure proper initialization and cleanup
   - Access through getter functions
   - Handle concurrent access properly

2. **Dependency Injection**
   - Components receive dependencies via constructors or methods
   - Facilitates testing and flexibility
   - Maintain this pattern when adding new components
   - Avoid direct instantiation of dependencies

3. **Repository Pattern**
   - Database access through specialized repository classes
   - Abstracts storage details from business logic
   - Maintains separation of concerns
   - Follows consistent interface contracts

4. **Service Layer Pattern**
   - Business logic encapsulated in service classes
   - Services orchestrate multiple operations
   - Maintain stateless design where possible
   - Services depend on repositories, not vice versa

## Testing Approach

When adding or modifying code, consider:

1. **Unit Testing**
   - Test individual functions and methods
   - Use mocks for external dependencies
   - Focus on behavior, not implementation details
   - Ensure high coverage of critical paths

2. **Integration Testing**
   - Test interactions between components
   - Verify proper database operations
   - Test API endpoints end-to-end
   - Validate error handling paths

3. **Performance Testing**
   - Consider query performance impacts
   - Test with realistic data volumes
   - Validate memory usage patterns
   - Ensure response time requirements are met

## Configuration Management

When working with configuration:

1. **Use the configuration system consistently**
   - Access via the `load_config()` function
   - Follow the established structure
   - Use environment variables for sensitive values
   - Document configuration options

2. **Handle configuration validation**
   - Check for required configuration values
   - Provide sensible defaults where appropriate
   - Validate configuration early in startup
   - Log configuration issues clearly

## Final Checklist for Code Changes

Before finalizing code changes, ensure:

1. **Code is well-formatted and follows style guidelines**
2. **All imports are resolved and necessary**
3. **Error handling is comprehensive**
4. **Logging is appropriate and informative**
5. **Documentation is updated**
6. **Tests cover the new functionality**
7. **Configuration is handled properly**
8. **Performance implications are considered**
9. **Security aspects are addressed**
10. **Backward compatibility is maintained where needed**
```