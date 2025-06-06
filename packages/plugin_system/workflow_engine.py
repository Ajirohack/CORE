"""
Workflow Engine for Cross-Plugin Workflows in SpaceNew

Allows definition and execution of workflows that span multiple plugins.
"""
from typing import List, Dict, Any, Callable

class WorkflowEngine:
    def __init__(self):
        self._workflows: Dict[str, List[Callable]] = {}

    def register_workflow(self, name: str, steps: List[Callable]):
        self._workflows[name] = steps

    def run_workflow(self, name: str, context: Dict[str, Any]):
        for step in self._workflows.get(name, []):
            step(context)

# Singleton instance
space_new_workflow_engine = WorkflowEngine()

# Example usage:
# engine = WorkflowEngine()
# engine.register_workflow("onboarding", [lambda ctx: print("Step 1", ctx), lambda ctx: print("Step 2", ctx)])
# engine.run_workflow("onboarding", {"user_id": "123"})
