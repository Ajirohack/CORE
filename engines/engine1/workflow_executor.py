from database.connections.base import SessionLocal
from database.models.workflow_execution import WorkflowExecution
import datetime

# Example workflow step function
def example_step(input_data):
    # Simulate processing
    return {"output": input_data + " processed"}

def execute_workflow(workflow_id, steps, input_data):
    session = SessionLocal()
    execution = WorkflowExecution(
        workflow_id=workflow_id,
        status="running",
        steps=[],
        started_at=datetime.datetime.utcnow()
    )
    session.add(execution)
    session.commit()
    try:
        step_results = []
        for step in steps:
            result = step(input_data)
            step_results.append(result)
        execution.status = "completed"
        execution.steps = step_results
        execution.result = step_results[-1] if step_results else None
        execution.finished_at = datetime.datetime.utcnow()
    except Exception as e:
        execution.status = "failed"
        execution.error = str(e)
        execution.finished_at = datetime.datetime.utcnow()
    finally:
        session.commit()
        session.close()
    return execution

# Example usage
if __name__ == "__main__":
    execute_workflow(
        workflow_id=1,
        steps=[example_step],
        input_data="test input"
    )
