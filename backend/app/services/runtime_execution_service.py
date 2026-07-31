from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any, AsyncGenerator
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.actions.examples.report_action import GenerateDeploymentReportAction
from app.actions.registry import ActionRegistry
from app.actions.services.action_executor import ActionExecutor
from app.ai.exceptions import (
    AIAuthenticationError,
    AIConnectionError,
    AIProviderError,
    AIRateLimitError,
    AITimeoutError,
)
from app.database.session import SessionLocal
from app.events.runtime_events import (
    PlanningCompleted,
    PlanningFailed,
    PlanningStarted,
    TaskCompleted,
    TaskFailed,
    TaskStarted,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowStarted,
)
from app.models.runtime_execution import RuntimeExecution
from app.runtime.context import RuntimeContext
from app.runtime.execution_tracker import ExecutionTracker
from app.services.chat_service import chat_service
from app.services.runtime_service import get_runtime


class RuntimeExecutionService:
    """Bridges the reusable runtime EventBus to durable SSE executions."""

    def __init__(self) -> None:
        self._runtime = get_runtime()
        self._tracker = ExecutionTracker()
        self._workflow_to_execution: dict[str, str] = {}
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._subscriptions_registered = False

        registry = ActionRegistry()
        registry.register(GenerateDeploymentReportAction())
        self._action_executor = ActionExecutor(registry)
        self._register_event_subscriptions()

    def _register_event_subscriptions(self) -> None:
        if self._subscriptions_registered:
            return

        event_bus = self._runtime._event_bus
        for event_type in (
            PlanningStarted,
            PlanningCompleted,
            PlanningFailed,
            WorkflowStarted,
            WorkflowCompleted,
            WorkflowFailed,
            TaskStarted,
            TaskCompleted,
            TaskFailed,
        ):
            event_bus.subscribe(event_type, self._handle_runtime_event)
        self._subscriptions_registered = True

    async def start(
        self,
        db: Session,
        *,
        user_id: str,
        message: str,
        conversation_id: UUID,
    ) -> RuntimeExecution:
        execution = RuntimeExecution(
            id=uuid4(),
            workflow_id=uuid4(),
            conversation_id=conversation_id,
            user_id=user_id,
            goal=message,
            status="RUNNING",
            steps=[],
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)

        execution_id = str(execution.id)
        self._workflow_to_execution[str(execution.workflow_id)] = execution_id
        self._tasks[execution_id] = asyncio.create_task(
            self._execute(execution, message)
        )
        return execution

    def get_for_user(
        self, db: Session, execution_id: UUID, user_id: str
    ) -> RuntimeExecution | None:
        return (
            db.query(RuntimeExecution)
            .filter(
                RuntimeExecution.id == execution_id,
                RuntimeExecution.user_id == user_id,
            )
            .first()
        )

    async def cancel(
        self,
        db: Session,
        *,
        execution_id: UUID,
        user_id: str,
    ) -> RuntimeExecution | None:
        """Cancel an owned execution and notify every connected SSE consumer."""
        execution = self.get_for_user(db, execution_id, user_id)
        if execution is None:
            return None
        if execution.status in {"COMPLETED", "FAILED", "CANCELLED"}:
            return execution

        execution_key = str(execution_id)
        duration_ms = round(
            (datetime.now(UTC) - execution.started_at.replace(tzinfo=UTC)).total_seconds()
            * 1000,
            2,
        )
        self._complete_execution(
            execution_key,
            status="CANCELLED",
            duration_ms=duration_ms,
            message="Execution cancelled by user.",
        )
        execution.status = "CANCELLED"
        execution.completed_at = datetime.utcnow()
        execution.duration_ms = duration_ms
        await self.publish_step(
            execution_key,
            name="Runtime Execution",
            description="Execution cancelled by user",
            status="cancelled",
            final=True,
            message="Execution cancelled by user.",
            duration_ms=duration_ms,
        )
        task = self._tasks.get(execution_key)
        if task is not None and not task.done():
            task.cancel()
        return execution

    async def _execute(self, execution: RuntimeExecution, message: str) -> None:
        """Run outside the request lifecycle using a fresh database session."""
        execution_id = str(execution.id)
        started_at = datetime.now(UTC)
        context = RuntimeContext(
            request_id=uuid4(),
            workflow_id=execution.workflow_id,
            session_id=uuid4(),
            conversation_id=execution.conversation_id,
            tenant_id="default",
            user_id=execution.user_id,
            goal=message,
            trace_id=str(uuid4()),
            available_agents=["default-agent"],
            available_tools=["generate-deployment-report"],
        )

        try:
            await self.publish_step(
                execution_id,
                name="Request Received",
                description="User prompt received",
                status="completed",
            )
            await asyncio.to_thread(
                self._load_conversation_context,
                execution.conversation_id,
                execution.user_id,
            )
            await self.publish_step(
                execution_id,
                name="Conversation API",
                description="Loading conversation context",
                status="completed",
            )

            result = await self._runtime.run(context)
            task_results = result.output.get("results", [])
            agent = task_results[0].get("agent") if task_results else "default-agent"

            await self.publish_step(
                execution_id,
                name="Generate Report Action",
                description="Calling enterprise action",
                status="running",
                agent=agent,
            )
            action_result = await self._action_executor.execute(
                "generate-deployment-report", {"goal": message}
            )
            if not action_result.success:
                raise RuntimeError(action_result.error or "Action execution failed")
            await self.publish_step(
                execution_id,
                name="Generate Report Action",
                description="Enterprise action completed",
                status="completed",
                agent=agent,
            )

            await self.publish_step(
                execution_id,
                name="Result Generated",
                description="Generating assistant response",
                status="running",
                agent=agent,
            )
            response = await asyncio.to_thread(
                self._generate_response,
                execution.conversation_id,
                execution.user_id,
                message,
            )
            duration_ms = round((datetime.now(UTC) - started_at).total_seconds() * 1000, 2)
            await self.publish_step(
                execution_id,
                name="Result Generated",
                description="Response delivered",
                status="completed",
                agent=agent,
                final=True,
                message=response.text,
                response_id=response.response_id,
                duration_ms=duration_ms,
                actions=[action_result.action_name],
            )
            self._complete_execution(
                execution_id,
                status="COMPLETED",
                agent=agent,
                message=response.text,
                duration_ms=duration_ms,
            )
        except asyncio.CancelledError:
            # cancel() already persisted and published the terminal event.
            raise
        except Exception as exc:
            duration_ms = round((datetime.now(UTC) - started_at).total_seconds() * 1000, 2)
            safe_error = self._safe_error_message(exc)
            await self.publish_step(
                execution_id,
                name="Runtime Orchestrator",
                description="Runtime failed during result generation",
                status="failed",
            )
            await self.publish_step(
                execution_id,
                name="Result Generated",
                description=safe_error,
                status="failed",
                final=True,
                message="Enterprise AI Runtime failed.",
                duration_ms=duration_ms,
                error=safe_error,
            )
            self._complete_execution(
                execution_id,
                status="FAILED",
                duration_ms=duration_ms,
                error=safe_error,
            )
        finally:
            self._tasks.pop(execution_id, None)
            self._workflow_to_execution.pop(str(execution.workflow_id), None)

    @staticmethod
    def _load_conversation_context(conversation_id: UUID, user_id: str) -> None:
        """Load the owned history before planning; ChatService rebuilds it for inference."""
        db = SessionLocal()
        try:
            from app.services.conversation_service import conversation_service

            conversation_service.get_messages(
                db=db, conversation_id=conversation_id, user_id=user_id
            )
        finally:
            db.close()

    @staticmethod
    def _generate_response(conversation_id: UUID, user_id: str, message: str):
        db = SessionLocal()
        try:
            return chat_service.ask(
                db=db,
                user_id=user_id,
                message=message,
                conversation_id=conversation_id,
            )
        finally:
            db.close()

    @staticmethod
    def _safe_error_message(error: Exception) -> str:
        """Keep provider payloads and credentials out of SSE events and the UI."""
        if isinstance(error, AIAuthenticationError):
            return "AI provider authentication failed. Contact an administrator."
        if isinstance(error, AIRateLimitError):
            return "AI provider rate limit reached. Please try again shortly."
        if isinstance(error, (AIConnectionError, AITimeoutError)):
            return "AI provider is temporarily unavailable. Please try again."
        if isinstance(error, AIProviderError):
            return "AI provider could not generate a response. Please try again."
        return "Runtime execution failed. Please try again or contact an administrator."

    async def _handle_runtime_event(self, event: Any) -> None:
        payload = event.payload
        execution_id = self._workflow_to_execution.get(payload.get("workflow_id", ""))
        if execution_id is None:
            return

        if isinstance(event, PlanningStarted):
            await self.publish_step(execution_id, "Planner", "Creating execution plan", "running")
        elif isinstance(event, PlanningCompleted):
            await self.publish_step(execution_id, "Planner", "Execution plan created", "completed")
        elif isinstance(event, PlanningFailed):
            await self.publish_step(execution_id, "Planner", "Planning failed", "failed")
        elif isinstance(event, WorkflowStarted):
            await self.publish_step(execution_id, "Runtime Orchestrator", "Workflow started", "running")
        elif isinstance(event, TaskStarted):
            agent = payload.get("agent") or "default-agent"
            await self.publish_step(execution_id, "Agent Selected", f"Selected {agent}", "completed", agent=agent)
            await self.publish_step(execution_id, "Agent Execution", "Executing agent workflow", "running", agent=agent)
        elif isinstance(event, TaskCompleted):
            await self.publish_step(execution_id, "Agent Execution", "Agent workflow completed", "completed", agent=payload.get("agent"))
        elif isinstance(event, TaskFailed):
            await self.publish_step(execution_id, "Agent Execution", payload.get("error", "Agent failed"), "failed", agent=payload.get("agent"))
        elif isinstance(event, WorkflowCompleted):
            await self.publish_step(
                execution_id,
                "Runtime Orchestrator",
                "Workflow execution completed",
                "completed",
            )
        elif isinstance(event, WorkflowFailed):
            await self.publish_step(
                execution_id,
                "Runtime Orchestrator",
                "Workflow execution failed",
                "failed",
            )

    async def publish_step(
        self,
        execution_id: str,
        name: str,
        description: str,
        status: str,
        *,
        agent: str | None = None,
        final: bool = False,
        **extra: Any,
    ) -> None:
        event = {
            "type": "completed" if final and status == "completed" else "step",
            "name": name,
            "description": description,
            "status": status,
            "timestamp": datetime.now(UTC).isoformat(),
            "final": final,
            **extra,
        }
        if agent:
            event["agent"] = agent
        self._append_step(execution_id, event)
        await self._tracker.publish(execution_id, event)

    def _append_step(self, execution_id: str, event: dict[str, Any]) -> None:
        db = SessionLocal()
        try:
            record = db.get(RuntimeExecution, UUID(execution_id))
            if record is None:
                return
            steps = list(record.steps or [])
            step_id = event["name"]
            existing_index = next((i for i, step in enumerate(steps) if step.get("id") == step_id), None)
            persisted_step = {
                "id": step_id,
                "name": event["name"],
                "description": event["description"],
                "status": event["status"],
                "timestamp": event["timestamp"],
            }
            if existing_index is None:
                steps.append(persisted_step)
            else:
                steps[existing_index] = persisted_step
            record.steps = steps
            db.commit()
        finally:
            db.close()

    def _complete_execution(
        self,
        execution_id: str,
        *,
        status: str,
        agent: str | None = None,
        message: str | None = None,
        duration_ms: float | None = None,
        error: str | None = None,
    ) -> None:
        db = SessionLocal()
        try:
            record = db.get(RuntimeExecution, UUID(execution_id))
            if record is None:
                return
            record.status = status
            record.agent = agent or record.agent
            record.result_message = message
            record.error = error
            record.duration_ms = duration_ms
            record.completed_at = datetime.utcnow()
            db.commit()
        finally:
            db.close()

    async def stream(self, execution_id: str) -> AsyncGenerator[dict[str, Any], None]:
        sent = 0
        queue = self._tracker.subscribe(execution_id)
        if not self._tracker.executions[execution_id]:
            db = SessionLocal()
            try:
                record = db.get(RuntimeExecution, UUID(execution_id))
                if record is not None:
                    for step in record.steps or []:
                        yield {"type": "step", "final": False, **step}
                    if record.status in {"COMPLETED", "FAILED", "CANCELLED"}:
                        yield {
                            "type": "completed" if record.status == "COMPLETED" else "step",
                            "name": "Result Generated" if record.status == "COMPLETED" else "Runtime Execution",
                            "description": (
                                "Response delivered"
                                if record.status == "COMPLETED"
                                else self._safe_error_message(Exception(record.error or ""))
                            ),
                            "status": (
                                "completed" if record.status == "COMPLETED"
                                else "cancelled" if record.status == "CANCELLED"
                                else "failed"
                            ),
                            "timestamp": (record.completed_at or record.started_at).isoformat(),
                            "final": True,
                            "message": record.result_message,
                            "duration_ms": record.duration_ms,
                            "agent": record.agent,
                        }
                        return
            finally:
                db.close()
        while True:
            events = self._tracker.executions[execution_id]
            while sent < len(events):
                event = events[sent]
                sent += 1
                yield event
                if event.get("final"):
                    return
            try:
                await asyncio.wait_for(queue.get(), timeout=15)
            except asyncio.TimeoutError:
                yield {"type": "heartbeat"}


runtime_execution_service = RuntimeExecutionService()
