from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.runtime.execution_tracker import ExecutionTracker
from app.ai.exceptions import AIAuthenticationError
from app.services.runtime_execution_service import RuntimeExecutionService


@pytest.mark.asyncio
async def test_execution_tracker_replays_and_delivers_runtime_events() -> None:
    """SSE consumers can receive stored steps and live terminal events."""
    tracker = ExecutionTracker()
    execution_id = "execution-123"
    request_received = {
        "name": "Request Received",
        "description": "User prompt received",
        "status": "completed",
    }
    await tracker.publish(execution_id, request_received)

    queue = tracker.subscribe(execution_id)
    result = {
        "name": "Result Generated",
        "description": "Response delivered",
        "status": "completed",
        "final": True,
    }
    await tracker.publish(execution_id, result)

    assert tracker.executions[execution_id] == [request_received, result]
    assert await queue.get() == result


@pytest.mark.asyncio
async def test_cancellation_publishes_a_terminal_cancelled_event() -> None:
    service = object.__new__(RuntimeExecutionService)
    execution_id = uuid4()
    execution = SimpleNamespace(
        id=execution_id,
        status="RUNNING",
        started_at=datetime.utcnow(),
        completed_at=None,
        duration_ms=None,
    )
    emitted = []

    class FakeTask:
        cancelled = False

        def done(self):
            return False

        def cancel(self):
            self.cancelled = True

    task = FakeTask()
    service._tasks = {str(execution_id): task}
    service.get_for_user = lambda _db, _id, _user: execution
    service._complete_execution = lambda *_args, **_kwargs: None

    async def publish_step(*_args, **kwargs):
        emitted.append(kwargs)

    service.publish_step = publish_step

    result = await service.cancel(
        None,
        execution_id=execution_id,
        user_id="user-123",
    )

    assert result is execution
    assert execution.status == "CANCELLED"
    assert task.cancelled is True
    assert emitted[0]["status"] == "cancelled"
    assert emitted[0]["final"] is True


def test_provider_error_is_sanitized_before_streaming() -> None:
    message = RuntimeExecutionService._safe_error_message(
        AIAuthenticationError("Incorrect API key provided: sk-secret")
    )

    assert message == "AI provider authentication failed. Contact an administrator."
    assert "sk-secret" not in message
