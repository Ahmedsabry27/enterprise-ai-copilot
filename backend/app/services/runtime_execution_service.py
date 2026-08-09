from __future__ import annotations

import asyncio
import re
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any, AsyncGenerator
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from jsonschema import ValidationError as JSONSchemaValidationError, validate as validate_json

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
from app.core.config import settings
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
from app.database.models.agent import Agent, AgentVersion
from app.database.models.agent_assignment import AgentKnowledgeAssignment, AgentToolAssignment
from app.agents.application_service import AgentIdentity, agent_application_service
from app.agents.execution_service import ExecutionRequest, agent_execution_service
from app.audit.events import append_audit_event
from app.database.models.tool import ToolDefinition, ToolExecution
from app.models.runtime_execution import RuntimeContinuation, RuntimeExecution, RuntimeExecutionEvent
from app.runtime.context import RuntimeContext
from app.runtime.intelligence import CapabilityIntelligence, IntentAnalysis, reconcile_parameters
from app.runtime.execution_tracker import ExecutionTracker
from app.services.chat_service import chat_service
from app.services.runtime_service import get_runtime
from app.tool_sdk.agent import authorized_model_tools
from app.tool_sdk.service import executor as tool_executor, registry as tool_registry
from app.contracts.tool_models import ExecutionContext as ToolExecutionContext


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

    _VALID_TRANSITIONS = {
        "PENDING": {"RUNNING", "CANCELLED"},
        "RUNNING": {"WAITING_FOR_INPUT", "WAITING_FOR_APPROVAL", "COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"},
        "WAITING_FOR_INPUT": {"RUNNING", "CANCELLED", "TIMED_OUT"},
        "WAITING_FOR_APPROVAL": {"RUNNING", "FAILED", "CANCELLED", "TIMED_OUT"},
        "COMPLETED": set(), "FAILED": set(), "CANCELLED": set(), "TIMED_OUT": set(),
    }

    @classmethod
    def _transition(cls, record: RuntimeExecution, status: str) -> None:
        current = record.status
        if status == current:
            return
        if status not in cls._VALID_TRANSITIONS.get(current, set()):
            raise ValueError(f"Invalid runtime transition: {current} -> {status}")
        record.status = status

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
        permissions: set[str] | None = None,
        tenant_id: str = "default",
        provider_name: str | None = None,
        model: str | None = None,
        agent_id: str | None = None,
        identity: Any | None = None,
        workspace_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RuntimeExecution:
        selected, candidates = self._select_agent(
            db, tenant_id=tenant_id, goal=message, requested_agent_id=agent_id, identity=identity
        )
        published_config = selected["model_configuration"] if selected else {}
        resolved_provider = self._resolve_provider_name(
            published_config.get("provider") or published_config.get("provider_name") or provider_name
        )
        resolved_model = self._resolve_model(
            provider_name=resolved_provider,
            model=published_config.get("model") or published_config.get("model_name") or model,
        )

        execution = RuntimeExecution(
            id=uuid4(),
            workflow_id=uuid4(),
            conversation_id=conversation_id,
            user_id=user_id,
            goal=message,
            status="RUNNING",
            steps=[],
            tenant_id=tenant_id,
            selected_agent_id=selected["agent_id"] if selected else None,
            agent=selected["name"] if selected else None,
            provider_name=resolved_provider,
            model_name=resolved_model,
            workspace_id=workspace_id,
            runtime_metadata={
                **(metadata or {}),
                "request": {"agent_id": agent_id, "provider": provider_name, "model": model},
                "resolved": {"provider": resolved_provider, "model": resolved_model},
                "selection_mode": "user_selected" if agent_id else ("automatic" if selected else "default_fallback"),
                "selected_agent": selected,
                "agent_candidates": candidates,
                "permissions": sorted(permissions or set()),
                "identity": {
                    "actor_id": identity.actor_id if identity else user_id,
                    "tenant_id": identity.tenant_id if identity else tenant_id,
                    "permissions": sorted(identity.permissions) if identity else sorted(permissions or set()),
                    "groups": sorted(identity.groups) if identity else [],
                    "roles": sorted(identity.roles) if identity else [],
                    "subject_type": identity.subject_type if identity else "user",
                },
            },
        )
        db.add(execution)
        from app.services.conversation_service import conversation_service
        conversation_service.save_user_message(db, conversation_id, message)
        append_audit_event(
            db, tenant_id=tenant_id, actor_id=user_id, action="runtime.started",
            target_type="runtime_execution", target_id=str(execution.id),
            correlation_id=str(execution.workflow_id),
            metadata={"agent_id": agent_id, "provider": resolved_provider, "model": resolved_model},
        )
        db.commit()
        db.refresh(execution)

        execution_id = str(execution.id)
        self._workflow_to_execution[str(execution.workflow_id)] = execution_id
        self._tasks[execution_id] = asyncio.create_task(
            self._execute(
                execution,
                message,
                permissions or set(),
                tenant_id,
                resolved_provider,
                resolved_model,
                selected,
                {},
            )
        )
        return execution

    @staticmethod
    def _select_agent(
        db: Session, *, tenant_id: str, goal: str, requested_agent_id: str | None,
        identity: AgentIdentity | None = None,
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        query = db.query(Agent).filter(
            Agent.tenant_id == tenant_id,
            Agent.lifecycle_status == "enabled",
            Agent.deleted_at.is_(None),
            Agent.published_version.is_not(None),
        )
        rows = query.all()
        if requested_agent_id:
            rows = [row for row in rows if requested_agent_id in {row.uuid, row.slug, str(row.id)}]
            if not rows:
                raise ValueError("Selected agent is unavailable or not authorized")

        intent = RuntimeExecutionService._classify_intent(goal)
        permitted = set(identity.permissions) if identity else {"tools.admin"}
        capability_definitions = authorized_model_tools(permissions=permitted)
        capability_analysis = CapabilityIntelligence.fallback(
            goal, CapabilityIntelligence._catalog(capability_definitions)
        )
        terms = {part.strip(".,!?()[]").lower() for part in goal.split() if len(part) > 2}
        terms.add(intent["intent"].replace("_", " "))
        candidates: list[dict[str, Any]] = []
        for row in rows:
            if row.operational_health in {"unhealthy", "error", "offline"}:
                continue
            if identity is not None:
                try:
                    agent_application_service.resolve_runtime(db, identity, row.uuid)
                except Exception:
                    continue
            version = db.query(AgentVersion).filter_by(
                agent_id=row.id, version=row.published_version, published=True
            ).first()
            if version is None:
                continue
            snapshot = version.configuration_snapshot or {}
            capabilities = snapshot.get("capabilities") or row.planner_configuration.get("capabilities", [])
            tools = db.query(AgentToolAssignment).filter_by(agent_id=row.id, tenant_id=tenant_id, enabled=True).all()
            knowledge = db.query(AgentKnowledgeAssignment).filter_by(agent_id=row.id, tenant_id=tenant_id, enabled=True).all()
            searchable = " ".join([
                row.name, row.description, row.slug,
                str(snapshot.get("instructions", "")),
                str(snapshot.get("tags", "")),
                str(snapshot.get("planner_configuration", "")),
                str(snapshot.get("environment_restrictions", "")),
                *map(str, capabilities), *[item.tool_name for item in tools],
                *[str(item.knowledge_source_id) for item in knowledge],
            ]).lower()
            matches = sum(1 for term in terms if term in searchable)
            capability_matches = sum(1 for capability in capabilities if any(term in str(capability).lower() for term in terms))
            tool_matches = sum(1 for item in tools if any(term in item.tool_name.lower() for term in terms))
            resolved_tool_match = bool(capability_analysis.selected_tool and any(item.tool_name == capability_analysis.selected_tool for item in tools))
            confidence = min(0.99, 0.15 + matches * 0.08 + capability_matches * 0.15 + tool_matches * 0.2 + (0.55 if resolved_tool_match else 0))
            candidate = {
                "agent_id": row.uuid,
                "name": row.name,
                "slug": row.slug,
                "capabilities": capabilities,
                "provider": (version.model_configuration or {}).get("provider", "openai"),
                "model": (version.model_configuration or {}).get("model"),
                "confidence": round(1.0 if requested_agent_id else confidence, 2),
                "reason": "User selected this published agent" if requested_agent_id else (
                    "Owns the resolved registered capability and matches the request" if resolved_tool_match else "Matches the request intent, published capabilities, and assigned resources" if matches else "Eligible published agent"
                ),
                "model_configuration": version.model_configuration or {},
                "published_version": row.published_version,
                "tools": [item.tool_name for item in tools],
                "knowledge_source_count": len(knowledge),
            }
            candidates.append(candidate)
        candidates.sort(key=lambda item: item["confidence"], reverse=True)
        if requested_agent_id:
            return (candidates[0] if candidates else None), candidates
        selected = candidates[0] if candidates and candidates[0]["confidence"] >= settings.AUTO_AGENT_MIN_CONFIDENCE else None
        return selected, candidates

    @staticmethod
    def _resolve_provider_name(
        provider_name: str | None,
    ) -> str:
        provider = (
            provider_name
            or settings.AI_PROVIDER
        ).strip().lower()

        if provider not in {"openai", "bedrock"}:
            raise ValueError(
                f"Unsupported AI provider: {provider}"
            )

        return provider

    @staticmethod
    def _resolve_model(
        *,
        provider_name: str,
        model: str | None,
    ) -> str:
        if model and model.strip():
            return model.strip()

        if provider_name == "openai":
            return settings.OPENAI_MODEL

        if provider_name == "bedrock":
            return settings.BEDROCK_MODEL_ID

        raise ValueError(
            f"Unsupported AI provider: {provider_name}"
        )

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

    @staticmethod
    def _runtime_metadata(execution_id: str) -> dict[str, Any]:
        db = SessionLocal()
        try:
            record = db.get(RuntimeExecution, UUID(execution_id))
            return dict(record.runtime_metadata or {}) if record else {}
        finally:
            db.close()

    @staticmethod
    def _matching_tool(message: str, tool_definitions: list[dict[str, Any]] | None = None, preferred: str | None = None) -> dict[str, Any] | None:
        if preferred:
            for definition in tool_definitions or []:
                function = definition.get("function") or {}
                if function.get("name") == preferred:
                    return function
        terms = {word.strip(".,!?()[]").lower() for word in message.split() if len(word) > 2}
        candidates = []
        for definition in tool_definitions or []:
            function = definition.get("function") or {}
            searchable = f"{function.get('name','')} {function.get('description','')}".lower()
            score = sum(1 for term in terms if term in searchable)
            if score:
                candidates.append((score, function))
        if not candidates:
            return None
        return max(candidates, key=lambda item: item[0])[1]

    @classmethod
    def _required_fields(cls, message: str, supplied: dict[str, Any], tool_definitions: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        """Derive missing fields from the best matching authorized tool JSON schema."""
        functions = [(item.get("function") or {}) for item in (tool_definitions or [])]
        function = functions[0] if len(functions) == 1 else cls._matching_tool(message, tool_definitions)
        if function is None:
            return []
        schema = function.get("parameters") or {}
        properties = schema.get("properties") or {}
        fields = []
        for name in schema.get("required", []):
            if supplied.get(name) not in (None, "", []):
                continue
            item = properties.get(name, {})
            kind = item.get("type", "string")
            if kind == "string":
                kind = item.get("format", "text")
            if item.get("enum"):
                kind = "select"
            fields.append({
                "name": name, "label": item.get("title") or name.replace("_", " ").title(),
                "type": kind, "required": True, "options": item.get("enum", []),
                "description": item.get("description"), "tool": function.get("name"),
            })
        return fields

    @staticmethod
    def _is_jira_create_request(message: str) -> bool:
        lowered = message.lower()
        return "jira" in lowered and any(word in lowered for word in ("create", "add", "open")) and any(
            word in lowered for word in ("ticket", "issue", "bug", "task", "story")
        )

    async def _execute_runtime_tool(
        self, execution_id: str, execution: RuntimeExecution, context: RuntimeContext,
        permissions: set[str], tenant_id: str, tool_name: str, inputs: dict[str, Any],
        *, stage: str = "default",
    ):
        tool = tool_registry.get(tool_name)
        category = "action" if str(tool.metadata.risk_level) != "read" else "tool"
        step_id = f"{category}:{tool_name}:{stage}"
        await self.publish_event(execution_id, {
            "type": f"{category}_started", "name": tool_name, "step_id": step_id,
            "description": f"Executing authorized {category}", "status": "running",
        })
        tool_db = SessionLocal()
        try:
            envelope = await tool_executor.execute(
                tool_name, inputs,
                ToolExecutionContext(
                    actor_id=execution.user_id, permissions=permissions,
                    tenant_id=tenant_id, conversation_id=str(execution.conversation_id),
                    correlation_id=str(execution.workflow_id), trace_id=context.trace_id,
                    idempotency_key=f"runtime:{execution_id}:{tool_name}:{stage}",
                ), tool_db,
            )
        except asyncio.CancelledError:
            await self.publish_event(execution_id, {
                "type": f"{category}_failed", "name": tool_name, "step_id": step_id,
                "description": f"{category.title()} execution was cancelled", "status": "cancelled",
                "error_code": "EXECUTION_CANCELLED",
            })
            raise
        except Exception as exc:
            await self.publish_event(execution_id, {
                "type": f"{category}_failed", "name": tool_name, "step_id": step_id,
                "description": getattr(exc, "safe_message", None) or "The tool could not complete the request",
                "status": "failed", "error_code": getattr(exc, "code", "TOOL_EXECUTION_FAILED"),
            })
            raise
        finally:
            tool_db.close()
        if envelope.status != "succeeded":
            await self.publish_event(execution_id, {
                "type": f"{category}_failed", "name": tool_name, "step_id": step_id,
                "description": envelope.error.message if envelope.error else f"{category.title()} failed",
                "status": "failed", "duration_ms": envelope.meta.get("duration_ms"),
                "error_code": envelope.error.code if envelope.error else "TOOL_EXECUTION_FAILED",
                "tool_execution_id": envelope.execution_id,
            })
            raise RuntimeError(envelope.error.message if envelope.error else f"{category.title()} execution failed")
        await self.publish_event(execution_id, {
            "type": f"{category}_completed", "name": tool_name, "step_id": step_id,
            "description": f"Authorized {category} completed", "status": "completed",
            "duration_ms": envelope.meta.get("duration_ms"), "result_summary": envelope.data,
            "tool_execution_id": envelope.execution_id,
        })
        return envelope.data

    async def _execute_jira_create_flow(
        self, execution_id: str, execution: RuntimeExecution, context: RuntimeContext,
        permissions: set[str], tenant_id: str, inputs: dict[str, Any], started_at: datetime,
        agent_name: str = "Governed Integration Runtime",
    ) -> None:
        await self.publish_step(execution_id, "Agent Selected", "Published agent owning the resolved Jira capability selected", "completed", agent=agent_name)
        await self.publish_step(execution_id, "Planner", "Resolving Jira project, issue type, and create fields", "completed", agent=agent_name)
        create_tool = tool_registry.get("jira.create_issue")
        create_definition = {"type":"function", "function":{
            "name":create_tool.metadata.name,
            "description":create_tool.metadata.description,
            "parameters":create_tool.metadata.parameters,
        }}
        base_missing = self._required_fields("", inputs, [create_definition])
        if not inputs.get("project_key"):
            await self._pause_for_input(execution_id, base_missing, inputs)
            return
        metadata_inputs = {"project_key": inputs["project_key"]}
        if inputs.get("issue_type_id"):
            metadata_inputs["issue_type_id"] = inputs["issue_type_id"]
        elif inputs.get("issue_type"):
            metadata_inputs["issue_type"] = inputs["issue_type"]
        metadata = await self._execute_runtime_tool(
            execution_id, execution, context, permissions, tenant_id,
            "jira.get_create_metadata", metadata_inputs,
            stage=str(inputs.get("issue_type_id") or inputs.get("issue_type") or "issue-types"),
        )
        if not inputs.get("issue_type") and not inputs.get("issue_type_id"):
            options = [{"label": item["name"], "value": item["name"]} for item in metadata.get("issue_types", []) if item.get("name")]
            if not options:
                raise RuntimeError("No Jira issue types are available for this project")
            enriched = []
            for field in base_missing:
                if field["name"] == "issue_type":
                    field = {**field, "type":"select", "options":options, "description":"Issue type available in this Jira project"}
                enriched.append(field)
            await self._pause_for_input(execution_id, enriched, inputs)
            return
        selected = metadata.get("selected_issue_type") or {}
        inputs = {**inputs, "issue_type": selected.get("name") or inputs.get("issue_type"), "issue_type_id": selected.get("id") or inputs.get("issue_type_id")}
        missing = self._required_fields("", inputs, [create_definition])
        ignored = {"project", "issuetype", "summary", "reporter"}
        for field in metadata.get("fields", []):
            field_id = field.get("fieldId") or field.get("key")
            if not field_id or field_id in ignored or not field.get("required") or field.get("hasDefaultValue"):
                continue
            if inputs.get(field_id) in (None, "", []):
                allowed = field.get("allowedValues") or []
                options = [{"label": str(item.get("name") or item.get("value") or item), "value": str(item.get("id") or item.get("value") or item)} for item in allowed]
                missing.append({"name":field_id,"label":field.get("name") or field_id,"type":"select" if options else "text","required":True,"options":options,"description":f"Required by Jira for {inputs['issue_type']}"})
        if missing:
            await self._pause_for_input(execution_id, missing, inputs)
            return
        known = {"project_key", "issue_type", "issue_type_id", "summary", "description", "priority", "assignee", "labels"}
        action_inputs = {key: value for key, value in inputs.items() if key in known and value not in (None, "", [])}
        action_inputs["jira_fields"] = {key: value for key, value in inputs.items() if key not in known and value not in (None, "", [])}
        issue = await self._execute_runtime_tool(
            execution_id, execution, context, permissions, tenant_id,
            "jira.create_issue", action_inputs, stage="create",
        )
        issue_key = issue.get("key")
        message = f"Created Jira issue {issue_key}." + (f" {issue.get('browse_url')}" if issue.get("browse_url") else "")
        duration_ms = round((datetime.now(UTC) - started_at).total_seconds() * 1000, 2)
        self._complete_execution(execution_id, status="COMPLETED", agent=agent_name, message=message, duration_ms=duration_ms)
        await self.publish_event(execution_id, {"type":"completed","name":"Result Generated","step_id":"result-generation","description":"Jira issue created successfully","status":"completed","agent":agent_name,"duration_ms":duration_ms,"message":message,"final":True})

    async def _pause_for_input(
        self, execution_id: str, fields: list[dict[str, Any]], known_values: dict[str, Any]
    ) -> None:
        db = SessionLocal()
        try:
            record = db.get(RuntimeExecution, UUID(execution_id))
            if record is None:
                return
            properties = {}
            required = []
            for field in fields:
                kind = field.get("type", "text")
                json_type = {"text":"string","email":"string","url":"string","date":"string","datetime":"string","date-range":"object","multiselect":"array","number":"number","integer":"integer","boolean":"boolean"}.get(kind,"string")
                definition = {"type": json_type}
                if field.get("options"):
                    definition["enum"] = [
                        option.get("value") if isinstance(option, dict) else option
                        for option in field["options"]
                    ]
                properties[field["name"]] = definition
                if field.get("required"):
                    required.append(field["name"])
            continuation = RuntimeContinuation(
                execution_id=record.id,
                tenant_id=record.tenant_id,
                kind="input",
                schema={"type": "object", "properties": properties, "required": required, "additionalProperties": True, "fields": fields,
                        "plan_id": (record.runtime_metadata or {}).get("plan_id"),
                        "intent": ((record.runtime_metadata or {}).get("intent") or {}).get("intent"),
                        "capability": ((record.runtime_metadata or {}).get("intent") or {}).get("selected_tool")},
                known_values=known_values,
                expires_at=datetime.utcnow() + timedelta(hours=24),
            )
            db.add(continuation)
            self._transition(record, "WAITING_FOR_INPUT")
            record.waiting_reason = "required_input"
            record.current_step = "Collect Information"
            db.commit()
            continuation_id = str(continuation.id)
        finally:
            db.close()
        metadata = self._runtime_metadata(execution_id)
        intent_name = (metadata.get("intent") or {}).get("intent")
        capability = (metadata.get("intent") or {}).get("selected_tool")
        domain = (metadata.get("intent") or {}).get("domain", "").title()
        await self.publish_event(execution_id, {
            "type": "required_input",
            "name": "Additional Information Required",
            "step_id": "required-information",
            "title": f"{domain} information required" if domain and domain != "General" else "Additional information required",
            "description": "Please provide only the unresolved values needed to continue this plan.",
            "status": "waiting",
            "continuation_id": continuation_id,
            "fields": fields,
            "known_values": known_values,
            "intent": intent_name, "capability": capability,
            "plan_id": metadata.get("plan_id"),
            "final": False,
        })

    async def _pause_for_approval(self, execution_id: str, inputs: dict[str, Any]) -> None:
        db = SessionLocal()
        try:
            record = db.get(RuntimeExecution, UUID(execution_id))
            if record is None:
                return
            continuation = RuntimeContinuation(
                execution_id=record.id, tenant_id=record.tenant_id, kind="approval",
                schema={"type": "approval", "action": "send_email"}, known_values=inputs,
                required_role="runtime.approver", expires_at=datetime.utcnow() + timedelta(hours=4),
            )
            db.add(continuation)
            self._transition(record, "WAITING_FOR_APPROVAL")
            record.waiting_reason = "approval_required"
            record.current_step = "Approval Check"
            db.commit()
            continuation_id = str(continuation.id)
        finally:
            db.close()
        await self.publish_event(execution_id, {
            "type": "approval_required", "name": "Send report approval",
            "description": "Sending the generated report is a governed business action.",
            "status": "waiting", "continuation_id": continuation_id,
            "action": "send_email", "risk": "medium", "business_impact": "Sends report data to external recipients",
            "required_role": "runtime.approver", "requested_parameters": {"recipients": inputs.get("recipients")},
            "summary": "Approve sending the deployment report to the confirmed recipients.", "final": False,
        })

    async def continue_execution(
        self, db: Session, *, execution_id: UUID, user_id: str,
        continuation_id: UUID, values: dict[str, Any], action: str = "input",
        resume_identity: AgentIdentity | None = None,
    ) -> RuntimeExecution | None:
        if resume_identity is not None and action in {"approve", "deny"}:
            record = db.query(RuntimeExecution).filter_by(
                id=execution_id, tenant_id=resume_identity.tenant_id
            ).first()
        else:
            record = self.get_for_user(db, execution_id, user_id)
        if record is None:
            return None
        expected_status = "WAITING_FOR_APPROVAL" if action in {"approve", "deny"} else "WAITING_FOR_INPUT"
        if record.status != expected_status:
            raise ValueError(f"Execution is not in {expected_status} state")
        continuation = db.query(RuntimeContinuation).filter_by(
            id=continuation_id, execution_id=execution_id, status="pending"
        ).with_for_update().first()
        if continuation is None or continuation.expires_at < datetime.utcnow():
            raise ValueError("Continuation is invalid or expired")
        agent_execution_id = continuation.schema.get("agent_execution_id")
        if agent_execution_id:
            metadata = dict(record.runtime_metadata or {})
            identity = resume_identity or self._identity(metadata)
            token = continuation.known_values.get("_resume_token")
            if not token:
                raise ValueError("Continuation cannot be resumed")
            result = await agent_execution_service.resume(
                db, execution_id=agent_execution_id, token=token, response=values,
                identity=identity, action=action,
            )
            continuation.status = "consumed"
            continuation.response = values
            continuation.consumed_at = datetime.utcnow()
            self._transition(record, "RUNNING")
            record.waiting_reason = None
            db.commit()
            await self.publish_event(str(record.id), {"type":"step","name":"Required Information","step_id":"required-information","description":"Submitted information was validated","status":"completed"})
            await self.publish_event(str(record.id), {"type":"step","name":"Runtime Resumed","step_id":"runtime-resumed","description":"Governed continuation accepted","status":"completed"})
            await self._map_agent_result(str(record.id), record, metadata.get("selected_agent") or {}, result)
            return record
        fields = continuation.schema.get("fields", [])
        if set(values) == {"natural_language"} and isinstance(values.get("natural_language"), str):
            pending_schema = {
                "type": "object", "properties": continuation.schema.get("properties", {}),
                "required": continuation.schema.get("required", []), "additionalProperties": False,
            }
            text = values["natural_language"].strip()
            extracted = CapabilityIntelligence._extract_schema_values(text, pending_schema)
            if len(fields) == 1 and not extracted:
                extracted[fields[0]["name"]] = text
            values = extracted
        missing = [field["name"] for field in fields if field.get("required") and values.get(field["name"]) in (None, "", [])]
        if missing:
            raise ValueError(f"Missing required values: {', '.join(missing)}")
        if not agent_execution_id:
            try:
                validate_json({**continuation.known_values, **values}, {k:v for k,v in continuation.schema.items() if k != "fields"})
            except JSONSchemaValidationError as exc:
                raise ValueError(f"Invalid continuation input: {exc.message}") from exc
        continuation.status = "consumed"
        continuation.response = values
        continuation.consumed_at = datetime.utcnow()
        self._transition(record, "RUNNING")
        record.waiting_reason = None
        metadata = dict(record.runtime_metadata or {})
        metadata["inputs"] = {**continuation.known_values, **values}
        if continuation.kind == "approval":
            metadata["approval_granted"] = True
        record.runtime_metadata = metadata
        db.commit()
        append_audit_event(
            db, tenant_id=record.tenant_id, actor_id=user_id,
            action="runtime.input_provided", target_type="runtime_execution",
            target_id=str(record.id), correlation_id=str(record.workflow_id),
            metadata={"continuation_id": str(continuation.id), "fields": sorted(values)},
        )
        db.commit()
        await self.publish_event(str(record.id), {
            "type": "step", "name": "Required Information", "step_id":"required-information", "description": "Submitted information was validated",
            "status": "completed", "final": False,
        })
        await self.publish_event(str(record.id), {"type":"step","name":"Runtime Resumed","step_id":"runtime-resumed","description":"Execution resumed from the blocked plan step","status":"completed","final":False})
        selected = metadata.get("selected_agent")
        execution_key = str(record.id)
        self._workflow_to_execution[str(record.workflow_id)] = execution_key
        self._tasks[execution_key] = asyncio.create_task(self._execute(
            record, record.goal or "", set(metadata.get("permissions", [])), record.tenant_id,
            record.provider_name or settings.AI_PROVIDER, record.model_name or self._resolve_model(provider_name=record.provider_name or settings.AI_PROVIDER, model=None),
            selected, metadata["inputs"],
        ))
        return record

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
            (
                datetime.now(UTC) - execution.started_at.replace(tzinfo=UTC)
            ).total_seconds()
            * 1000,
            2,
        )
        self._complete_execution(
            execution_key,
            status="CANCELLED",
            duration_ms=duration_ms,
            message="Execution cancelled by user.",
        )
        self._transition(execution, "CANCELLED")
        execution.completed_at = datetime.utcnow()
        execution.duration_ms = duration_ms
        if db is not None:
            db.query(RuntimeContinuation).filter_by(execution_id=execution_id, status="pending").update({
                "status": "cancelled", "consumed_at": datetime.utcnow()
            })
            db.commit()
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

    async def _execute(
        self,
        execution: RuntimeExecution,
        message: str,
        permissions: set[str],
        tenant_id: str,
        provider_name: str,
        model: str,
        selected_agent: dict[str, Any] | None,
        supplied_inputs: dict[str, Any],
    ) -> None:
        """Run outside the request lifecycle using a fresh database session."""
        execution_id = str(execution.id)
        started_at = datetime.now(UTC)
        visible_tool_definitions = authorized_model_tools(permissions=permissions)
        context = RuntimeContext(
            request_id=uuid4(),
            workflow_id=execution.workflow_id,
            session_id=uuid4(),
            conversation_id=execution.conversation_id,
            tenant_id=tenant_id,
            user_id=execution.user_id,
            goal=message,
            trace_id=str(uuid4()),
            available_agents=[selected_agent["slug"]] if selected_agent else ["default-agent"],
            available_tools=[
                item["function"]["name"] for item in visible_tool_definitions
            ],
            metadata={
                "tool_definitions": visible_tool_definitions,
                "ai_provider": provider_name,
                "ai_model": model,
                "inputs": supplied_inputs,
            },
        )

        try:
            await self.publish_step(
                execution_id,
                name="Request Received",
                description="User prompt received",
                status="completed",
                provider=provider_name,
                model=model,
            )
            if selected_agent:
                await self.publish_step(
                    execution_id,
                    name="Agent Selected",
                    description=selected_agent["reason"],
                    status="completed",
                    agent=selected_agent["name"],
                    agent_id=selected_agent["agent_id"],
                    confidence=selected_agent["confidence"],
                    selection_mode=(self._runtime_metadata(execution_id).get("selection_mode") or "automatic"),
                    selection_reason=selected_agent["reason"],
                    capabilities=selected_agent.get("capabilities", []),
                    assigned_tools=selected_agent.get("tools", []),
                    knowledge_source_count=selected_agent.get("knowledge_source_count", 0),
                    candidates=[{k: v for k, v in item.items() if k != "model_configuration"} for item in self._runtime_metadata(execution_id).get("agent_candidates", [])],
                    provider=provider_name,
                    model=model,
                )
            elif self._runtime_metadata(execution_id).get("selection_mode") == "default_fallback":
                await self.publish_step(
                    execution_id, name="Agent Selection",
                    description="No specialized agent met the routing threshold; using the governed default runtime.",
                    status="completed", selection_mode="default_fallback",
                    candidates=[{k: v for k, v in item.items() if k != "model_configuration"} for item in self._runtime_metadata(execution_id).get("agent_candidates", [])],
                    provider=provider_name, model=model,
                )
            await asyncio.to_thread(
                self._load_conversation_context,
                execution.conversation_id,
                execution.user_id,
            )
            await self.publish_step(
                execution_id,
                name="Conversation API",
                description="Conversation context loaded",
                status="completed",
            )

            runtime_metadata = self._runtime_metadata(execution_id)
            stored_intent = runtime_metadata.get("intent") or {}
            if stored_intent.get("selected_tool") and not stored_intent.get("ambiguous"):
                analysis = IntentAnalysis(
                    intent=stored_intent.get("intent", "general.assistance"),
                    domain=stored_intent.get("domain", "general"), operation=stored_intent.get("operation", "respond"),
                    resource=stored_intent.get("resource", "unknown"), entities=stored_intent.get("entities") or {},
                    confidence=stored_intent.get("confidence", 0.5), required_capabilities=stored_intent.get("required_capabilities") or [],
                    selected_tool=stored_intent.get("selected_tool"), ambiguous=stored_intent.get("ambiguous", False),
                )
            else:
                analysis_request = message
                if supplied_inputs:
                    import json
                    analysis_request += "\nUser clarification: " + json.dumps(supplied_inputs, default=str)
                analysis = await asyncio.to_thread(
                    CapabilityIntelligence().analyze, analysis_request, visible_tool_definitions,
                    provider_name=provider_name, model=model,
                )
            planned_function = self._matching_tool(message, visible_tool_definitions, analysis.selected_tool)
            schema = (planned_function or {}).get("parameters") or {"properties": {}}
            resolved_inputs, parameter_trace = reconcile_parameters(
                schema, prompt_values=analysis.entities, collected_values=supplied_inputs,
            )
            analysis.entities = resolved_inputs
            intent = analysis.safe_dict()
            missing_parameter_names = [
                key for key in schema.get("required", [])
                if resolved_inputs.get(key) in (None, "", [])
            ]
            context = replace(context, metadata={
                **context.metadata, "structured_intent": intent,
                "inputs": resolved_inputs, "permissions": sorted(permissions),
            })
            self._merge_runtime_metadata(execution_id, {"intent": intent, "inputs": resolved_inputs, "parameter_state": parameter_trace})
            await self.publish_step(
                execution_id, name="Intent Analysis",
                description=f"{intent['intent'].replace('_', ' ').replace('.', ' ').title()} identified",
                status="completed", intent=intent, extracted_parameters=parameter_trace,
                required_capabilities=intent.get("required_capabilities", []),
                missing_parameters=missing_parameter_names,
            )

            if analysis.ambiguous and analysis.domain != "general":
                await self._pause_for_input(execution_id, [{
                    "name":"report_scope", "label":f"{analysis.domain.title()} report scope",
                    "type":"text", "required":True,
                    "description":f"Describe the scope supported by {analysis.selected_tool or 'the available capability'}, such as project, status, assignee, release, or a custom query.",
                }], supplied_inputs)
                return

            if analysis.selected_tool == "jira.create_issue":
                await self._execute_jira_create_flow(
                    execution_id, execution, context, permissions, tenant_id,
                    resolved_inputs, started_at,
                    (selected_agent or {}).get("name") or "Governed Integration Runtime",
                )
                return

            if selected_agent:
                assigned_names = set(selected_agent.get("tools", []))
                assigned_definitions = [item for item in visible_tool_definitions if (item.get("function") or {}).get("name") in assigned_names]
                preflight_missing = self._required_fields(message, resolved_inputs, assigned_definitions)
                if preflight_missing:
                    planned_tool = self._matching_tool(message, assigned_definitions, analysis.selected_tool)
                    await self.publish_step(execution_id, "Planner", "Resolving published agent dependencies", "running", agent=selected_agent["name"])
                    await self.publish_step(execution_id, "Planner", "Execution plan created with unresolved required inputs", "completed", agent=selected_agent["name"], plan={"plan_id":str(uuid4()),"goal":message,"steps":[{"id":f"tool:{planned_tool['name']}","name":planned_tool["name"],"type":"tool","dependencies":[],"required":True,"required_capability":planned_tool.get("description"),"resolved_tool":planned_tool["name"],"status":"waiting_for_input"}]})
                    await self._pause_for_input(execution_id, preflight_missing, resolved_inputs)
                    return
                await self._execute_managed_agent(
                    execution_id, execution, message, resolved_inputs, selected_agent
                )
                return

            missing_fields = self._required_fields(message, resolved_inputs, [
                item for item in visible_tool_definitions
                if (item.get("function") or {}).get("name") == analysis.selected_tool
            ] if analysis.selected_tool else visible_tool_definitions)
            planned_tool = self._matching_tool(message, visible_tool_definitions, analysis.selected_tool)
            await self.publish_step(execution_id, "Planner", "Resolving authorized capabilities and dependencies", "running")
            plan_steps = [{
                "id": f"tool:{planned_tool['name']}", "name": planned_tool["name"],
                "type": "tool", "dependencies": [], "required": True,
                "required_capability": planned_tool.get("description"),
                "resolved_tool": planned_tool["name"], "status": "waiting_for_input" if missing_fields else "pending",
            }] if planned_tool else [{
                "id": "agent-response", "name": "Generate governed response",
                "type": "agent", "dependencies": [], "required": True, "status": "pending",
            }]
            await self.publish_step(
                execution_id, "Planner", "Execution plan created", "completed",
                plan={"plan_id": str(uuid4()), "goal": message, "steps": plan_steps},
            )
            if missing_fields:
                await self._pause_for_input(execution_id, missing_fields, resolved_inputs)
                return

            if planned_tool:
                tool_name = planned_tool["name"]
                tool = tool_registry.get(tool_name)
                category = "action" if str(tool.metadata.risk_level) != "read" else "tool"
                await self.publish_event(execution_id,{"type":f"{category}_started","name":tool_name,"step_id":f"{category}:{tool_name}","description":f"Executing authorized {category}","status":"running"})
                tool_db = SessionLocal()
                envelope = None
                try:
                    envelope = await tool_executor.execute(
                        tool_name, resolved_inputs,
                        ToolExecutionContext(
                            actor_id=execution.user_id, permissions=permissions,
                            tenant_id=tenant_id, conversation_id=str(execution.conversation_id),
                            correlation_id=str(execution.workflow_id), trace_id=context.trace_id,
                            idempotency_key=f"runtime:{execution_id}:{tool_name}",
                        ), tool_db,
                    )
                except asyncio.CancelledError:
                    await self.publish_event(execution_id,{"type":f"{category}_failed","name":tool_name,"step_id":f"{category}:{tool_name}","description":f"{category.title()} execution was cancelled","status":"cancelled","error_code":"EXECUTION_CANCELLED"})
                    raise
                except Exception as exc:
                    safe_tool_error = getattr(exc, "safe_message", None) or "The tool could not complete the request"
                    await self.publish_event(execution_id,{"type":f"{category}_failed","name":tool_name,"step_id":f"{category}:{tool_name}","description":safe_tool_error,"status":"failed","error_code":getattr(exc, "code", "TOOL_EXECUTION_FAILED")})
                    raise
                finally:
                    tool_db.close()
                if envelope.status != "succeeded":
                    await self.publish_event(execution_id,{"type":f"{category}_failed","name":tool_name,"step_id":f"{category}:{tool_name}","description":envelope.error.message if envelope.error else f"{category.title()} failed","status":"failed","duration_ms":envelope.meta.get("duration_ms")})
                    raise RuntimeError(envelope.error.message if envelope.error else f"{category.title()} execution failed")
                await self.publish_event(execution_id,{"type":f"{category}_completed","name":tool_name,"step_id":f"{category}:{tool_name}","description":f"Authorized {category} completed","status":"completed","duration_ms":envelope.meta.get("duration_ms"),"result_summary":envelope.data})
                tool_message = envelope.data.get("report") if isinstance(envelope.data,dict) else str(envelope.data)
                db_message = SessionLocal()
                try:
                    from app.services.conversation_service import conversation_service
                    conversation_service.save_assistant_message(db_message, execution.conversation_id, tool_message, execution_id)
                finally:
                    db_message.close()
                duration_ms = round((datetime.now(UTC)-started_at).total_seconds()*1000,2)
                self._complete_execution(execution_id,status="COMPLETED",agent="Governed Runtime",message=tool_message,duration_ms=duration_ms)
                await self.publish_event(execution_id,{"type":"completed","name":"Result Generated","step_id":"result-generation","description":"Verified tool result delivered","status":"completed","duration_ms":duration_ms,"message":tool_message,"final":True})
                return

            result = await self._runtime.run(context)
            task_results = result.output.get("results", [])
            agent = selected_agent["name"] if selected_agent else (task_results[0].get("agent") if task_results else "default-agent")

            await self.publish_step(
                execution_id,
                name="Result Generated",
                description="Generating assistant response",
                status="running",
                agent=agent,
            )
            inference_message = message
            if supplied_inputs:
                import json
                inference_message += "\n\nVerified runtime inputs:\n" + json.dumps(supplied_inputs, sort_keys=True, default=str)
            response = await asyncio.to_thread(
                self._generate_response,
                execution.conversation_id,
                execution.user_id,
                inference_message,
                provider_name,
                model,
            )
            if self._has_unresolved_business_placeholders(response.text, message):
                raise ValueError("Generated output contains unresolved business placeholders")
            duration_ms = round(
                (datetime.now(UTC) - started_at).total_seconds() * 1000, 2
            )
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            } if response.usage else {}
            await self.publish_event(execution_id, {
                "type":"metric", "name":"Provider Metrics", "status":"completed",
                "provider":provider_name, "model":response.model,
                "metadata":{"duration_ms":duration_ms,"provider_latency_ms":round(response.latency_seconds*1000,2),"token_usage":usage},
            })
            self._complete_execution(
                execution_id,
                status="COMPLETED",
                agent=agent,
                message=response.text,
                duration_ms=duration_ms,
            )
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
                provider=provider_name,
                model=response.model,
            )
        except asyncio.CancelledError:
            # cancel() already persisted and published the terminal event.
            raise
        except Exception as exc:
            duration_ms = round(
                (datetime.now(UTC) - started_at).total_seconds() * 1000, 2
            )
            safe_error = self._safe_error_message(exc)
            self._complete_execution(
                execution_id,
                status="FAILED",
                duration_ms=duration_ms,
                error=safe_error,
                error_code=self._error_code(exc),
            )
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
    def _generate_response(
        conversation_id: UUID,
        user_id: str,
        message: str,
        provider_name: str,
        model: str,
    ):
        db = SessionLocal()
        try:
            return chat_service.ask(
                db=db,
                user_id=user_id,
                message=message,
                conversation_id=conversation_id,
                provider_name=provider_name,
                model=model,
                persist_user=False,
            )
        finally:
            db.close()

    @staticmethod
    def _classify_intent(message: str) -> dict[str, Any]:
        """Produce safe structured classification metadata without model reasoning."""
        words = set(re.findall(r"[a-z0-9_-]+", message.lower()))
        definitions = {
            "deployment_report": {"deployment", "release", "report"},
            "analysis": {"analyze", "analysis", "compare", "risk", "variance"},
            "summarization": {"summarize", "summary", "explain"},
        }
        scored = {name: len(words & vocabulary) / len(vocabulary) for name, vocabulary in definitions.items()}
        intent, score = max(scored.items(), key=lambda item: item[1])
        if score == 0:
            intent, score = "general_assistance", 0.55
        entities: dict[str, Any] = {}
        environment = next((value for value in ("production", "staging", "development", "dev", "test") if value in words), None)
        if environment:
            entities["environment"] = environment
        if "last" in words and "week" in words:
            entities["date_range"] = "last_week"
        return {"intent": intent, "confidence": round(min(0.98, 0.55 + score * 0.4), 2), "entities": entities}

    @staticmethod
    def _has_unresolved_business_placeholders(output: str, request: str) -> bool:
        if "template" in request.lower():
            return False
        return bool(re.search(r"\[(?:project name|version number|date|description|pass/fail|environment|recipient)\]", output, re.IGNORECASE))

    @staticmethod
    def _identity(metadata: dict[str, Any]) -> AgentIdentity:
        item = metadata.get("identity") or {}
        return AgentIdentity(
            actor_id=item.get("actor_id", "unknown"),
            tenant_id=item.get("tenant_id", "default"),
            permissions=frozenset(item.get("permissions", [])),
            groups=frozenset(item.get("groups", [])),
            roles=frozenset(item.get("roles", [])),
            subject_type=item.get("subject_type", "user"),
        )

    def _merge_runtime_metadata(self, execution_id: str, values: dict[str, Any]) -> None:
        db = SessionLocal()
        try:
            record = db.get(RuntimeExecution, UUID(execution_id))
            if record:
                record.runtime_metadata = {**(record.runtime_metadata or {}), **values}
                db.commit()
        finally:
            db.close()

    async def _execute_managed_agent(
        self, execution_id: str, execution: RuntimeExecution, message: str,
        inputs: dict[str, Any], selected: dict[str, Any]
    ) -> None:
        metadata = self._runtime_metadata(execution_id)
        identity = self._identity(metadata)
        await self.publish_step(
            execution_id, "Planner", "Using the selected agent's published planner",
            "running", agent=selected["name"],
        )
        plan_steps = [{
            "id": f"tool:{name}", "name": name, "type": "tool",
            "required_capability": name, "resolved_tool": name,
            "dependencies": [], "required": True, "status": "pending",
        } for name in selected.get("tools", [])]
        if not plan_steps:
            plan_steps = [{
                "id": "managed_agent", "name": "Generate governed agent response",
                "type": "agent", "dependencies": [], "required": True,
                "status": "pending",
            }]
        await self.publish_step(
            execution_id, "Planner", "Published agent plan created", "completed",
            agent=selected["name"],
            plan={"plan_id": str(uuid4()), "goal": message, "steps": plan_steps},
        )
        await self.publish_step(
            execution_id, "Agent Execution", "Executing published agent plan",
            "running", agent=selected["name"], provider=selected.get("provider"),
            model=selected.get("model"),
        )
        db = SessionLocal()
        try:
            result = await agent_execution_service.start(
                db, agent_id=selected["agent_id"],
                request=ExecutionRequest(
                    message=message, inputs=dict(inputs),
                    conversation_id=str(execution.conversation_id),
                    runtime_execution_id=execution_id,
                ),
                identity=identity,
            )
        finally:
            db.close()
        await self._map_agent_result(execution_id, execution, selected, result)

    async def _persist_agent_continuation(
        self, execution_id: str, result: dict[str, Any], continuation: dict[str, Any]
    ) -> None:
        schema = continuation.get("schema") or {}
        properties = schema.get("properties") or {}
        missing = continuation.get("missing_fields") or []
        fields = []
        for name in missing:
            definition = properties.get(name, {})
            field_type = definition.get("type", "text")
            if field_type == "string":
                field_type = definition.get("format", "text")
            fields.append({
                "name": name, "label": definition.get("title") or name.replace("_", " ").title(),
                "type": field_type, "required": name in schema.get("required", []),
                "options": definition.get("enum", []), "description": definition.get("description"),
            })
        kind = continuation.get("kind", "input")
        db = SessionLocal()
        try:
            record = db.get(RuntimeExecution, UUID(execution_id))
            row = RuntimeContinuation(
                execution_id=record.id, tenant_id=record.tenant_id, kind=kind,
                schema={"agent_execution_id": result.get("execution_id"), "fields": fields},
                known_values={"_resume_token": continuation.get("resume_token")},
                required_role=continuation.get("required_approver"),
                expires_at=datetime.fromisoformat(str(continuation["expires_at"])) if isinstance(continuation.get("expires_at"), str) else continuation.get("expires_at") or datetime.utcnow()+timedelta(minutes=30),
            )
            db.add(row)
            self._transition(record, "WAITING_FOR_APPROVAL" if kind == "approval" else "WAITING_FOR_INPUT")
            record.waiting_reason = kind
            db.commit()
            continuation_id = str(row.id)
        finally:
            db.close()
        if kind == "approval":
            await self.publish_event(execution_id, {
                "type":"approval_required", "name": continuation.get("question") or "Approval required",
                "description": continuation.get("question") or "A governed action requires approval.",
                "status":"waiting", "continuation_id":continuation_id,
                "action": continuation.get("tool_name"), "risk":"governed",
                "required_role": continuation.get("required_approver"), "final":False,
            })
        else:
            await self.publish_event(execution_id, {
                "type":"required_input", "name":"Additional Information Required",
                "description":continuation.get("question") or "Provide the required tool inputs.",
                "status":"waiting", "continuation_id":continuation_id,
                "fields":fields, "final":False,
            })

    async def _map_agent_result(
        self, execution_id: str, execution: RuntimeExecution,
        selected: dict[str, Any], result: dict[str, Any]
    ) -> None:
        self._merge_runtime_metadata(execution_id, {"agent_execution_id": result.get("execution_id")})
        if result.get("continuation"):
            await self._persist_agent_continuation(execution_id, result, result["continuation"])
            return
        db = SessionLocal()
        try:
            ids = result.get("tool_execution_ids") or []
            rows = db.query(ToolExecution).filter(ToolExecution.id.in_(ids)).all() if ids else []
            for row in rows:
                definition = db.query(ToolDefinition).filter_by(
                    tenant_id=row.tenant_id, name=row.tool_name, version=row.tool_version
                ).first()
                category = "action" if definition and definition.risk_level != "read" else "tool"
                await self.publish_event(execution_id, {
                    "type":f"{category}_started", "name":row.tool_name,
                    "description":f"{category.title()} execution started", "status":"running",
                    "tool_execution_id":row.id, "started_at":row.started_at.isoformat(),
                })
                await self.publish_event(execution_id, {
                    "type":f"{category}_completed" if row.status=="succeeded" else f"{category}_failed",
                    "name":row.tool_name, "description":"Tool execution completed" if row.status=="succeeded" else (row.error_message or "Tool execution failed"),
                    "status":"completed" if row.status=="succeeded" else "failed",
                    "tool_execution_id":row.id, "duration_ms":row.duration_ms,
                    "retry_count":row.retry_count, "result_summary":row.output_summary,
                })
        finally:
            db.close()
        if result.get("status") == "failed":
            error = (result.get("error") or {}).get("message") or "Managed agent execution failed"
            error_code = (result.get("error") or {}).get("code") or "AGENT_EXECUTION_FAILED"
            await self.publish_step(execution_id, "Agent Execution", error, "failed", agent=selected.get("name"))
            self._complete_execution(execution_id, status="FAILED", agent=selected.get("name"), duration_ms=result.get("duration_ms"), error=error, error_code=error_code)
            await self.publish_event(execution_id, {"type":"error","name":"Runtime Execution","step_id":"runtime","description":error,"status":"failed","error":error,"error_code":error_code,"provider":result.get("model_provider"),"model":result.get("model_name"),"message":error,"duration_ms":result.get("duration_ms"),"final":True})
            return
        output = result.get("result") or {}
        message = output.get("message") or "Execution completed."
        if self._has_unresolved_business_placeholders(message, execution.goal or ""):
            error = "The generated result was incomplete and requires verified business data."
            await self.publish_step(execution_id, "Agent Execution", error, "failed", agent=selected.get("name"))
            self._complete_execution(execution_id, status="FAILED", agent=selected.get("name"), duration_ms=result.get("duration_ms"), error=error, error_code="INVALID_BUSINESS_RESULT")
            await self.publish_event(execution_id, {"type":"error","name":"Runtime Execution","step_id":"runtime","description":error,"status":"failed","error":error,"error_code":"OUTPUT_VALIDATION_FAILED","provider":result.get("model_provider"),"model":result.get("model_name"),"final":True})
            return
        db = SessionLocal()
        try:
            from app.services.conversation_service import conversation_service
            conversation_service.save_assistant_message(db, execution.conversation_id, message, execution_id)
        finally:
            db.close()
        await self.publish_step(execution_id, "Agent Execution", "Published agent execution completed", "completed", agent=selected.get("name"), provider=result.get("model_provider"), model=result.get("model_name"))
        await self.publish_event(execution_id, {"type":"metric","name":"Provider Metrics","step_id":"provider-metrics","status":"completed","metadata":{"token_usage":result.get("token_usage") or {},"duration_ms":result.get("duration_ms"),"estimated_cost":result.get("estimated_cost"),"actual_cost":result.get("actual_cost")},"provider":result.get("model_provider"),"model":result.get("model_name")})
        for source in output.get("citations") or []:
            await self.publish_event(execution_id, {"type":"knowledge_retrieval_completed","name":source.get("name","Knowledge source"),"description":"Authorized knowledge source retrieved","status":"completed","source":source})
        self._complete_execution(execution_id, status="COMPLETED", agent=selected.get("name"), message=message, duration_ms=result.get("duration_ms"))
        await self.publish_event(execution_id, {"type":"completed","name":"Result Generated","step_id":"result-generation","description":"Managed agent response delivered","status":"completed","agent":selected.get("name"),"agent_id":selected.get("agent_id"),"provider":result.get("model_provider"),"model":result.get("model_name"),"duration_ms":result.get("duration_ms"),"message":message,"final":True})

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

    @staticmethod
    def _error_code(error: Exception) -> str:
        if isinstance(error, AIAuthenticationError): return "PROVIDER_AUTH_FAILED"
        if isinstance(error, AIRateLimitError): return "PROVIDER_RATE_LIMITED"
        if isinstance(error, AITimeoutError): return "RUNTIME_TIMEOUT"
        if isinstance(error, AIConnectionError): return "PROVIDER_UNAVAILABLE"
        if isinstance(error, AIProviderError): return "MODEL_INVOCATION_FAILED"
        return "RUNTIME_EXECUTION_FAILED"

    async def _handle_runtime_event(self, event: Any) -> None:
        payload = event.payload
        execution_id = self._workflow_to_execution.get(payload.get("workflow_id", ""))
        if execution_id is None:
            return

        if isinstance(event, PlanningStarted):
            await self.publish_step(
                execution_id, "Planner", "Creating execution plan", "running"
            )
        elif isinstance(event, PlanningCompleted):
            await self.publish_step(
                execution_id, "Planner", "Execution plan created", "completed",
                plan=payload.get("plan"),
            )
        elif isinstance(event, PlanningFailed):
            await self.publish_step(
                execution_id, "Planner", "Planning failed", "failed"
            )
        elif isinstance(event, WorkflowStarted):
            await self.publish_step(
                execution_id, "Runtime Orchestrator", "Workflow started", "running"
            )
        elif isinstance(event, TaskStarted):
            agent = payload.get("agent") or "default-agent"
            await self.publish_step(
                execution_id,
                "Agent Selected",
                f"Selected {agent}",
                "completed",
                agent=agent,
            )
            await self.publish_step(
                execution_id,
                "Agent Execution",
                "Executing agent workflow",
                "running",
                agent=agent,
            )
        elif isinstance(event, TaskCompleted):
            await self.publish_step(
                execution_id,
                "Agent Execution",
                "Agent workflow completed",
                "completed",
                agent=payload.get("agent"),
            )
        elif isinstance(event, TaskFailed):
            await self.publish_step(
                execution_id,
                "Agent Execution",
                payload.get("error", "Agent failed"),
                "failed",
                agent=payload.get("agent"),
            )
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
        event.setdefault("step_id", self._step_id(name))
        if agent:
            event["agent"] = agent
        await self.publish_event(execution_id, event)

    async def publish_event(self, execution_id: str, event: dict[str, Any]) -> None:
        event.setdefault("timestamp", datetime.now(UTC).isoformat())
        event.setdefault("final", False)
        event = self._append_step(execution_id, event)
        await self._tracker.publish(execution_id, event)

    @staticmethod
    def _step_id(name: str) -> str:
        return "-".join(part for part in name.lower().replace("/", " ").split() if part)

    def _append_step(self, execution_id: str, event: dict[str, Any]) -> dict[str, Any]:
        db = SessionLocal()
        try:
            record = db.get(RuntimeExecution, UUID(execution_id))
            if record is None:
                return event
            steps = list(record.steps or [])
            step_id = event.get("step_id") or self._step_id(event.get("name") or event.get("type", "event"))
            event["step_id"] = step_id
            existing_index = next(
                (i for i, step in enumerate(steps) if step.get("id") == step_id), None
            )
            persisted_step = {
                "id": step_id,
                "name": event["name"],
                "description": event.get("description", ""),
                "status": event.get("status", "running"),
                "timestamp": event["timestamp"],
            }
            if event.get("type") not in {"metric", "log", "heartbeat", "knowledge_retrieval_completed", "knowledge_retrieval_started"}:
                if existing_index is None:
                    steps.append(persisted_step)
                else:
                    steps[existing_index] = persisted_step
                record.steps = steps
            if event.get("type") == "metric":
                metric = event.get("metadata") or {}
                record.token_usage = metric.get("token_usage") or record.token_usage
                record.estimated_cost = metric.get("estimated_cost", record.estimated_cost)
                record.actual_cost = metric.get("actual_cost", record.actual_cost)
                record.provider_name = event.get("provider") or record.provider_name
                record.model_name = event.get("model") or record.model_name
            sequence = db.query(RuntimeExecutionEvent).filter_by(execution_id=record.id).count() + 1
            event_id = uuid4()
            event["event_id"] = str(event_id)
            event["sequence"] = sequence
            db.add(RuntimeExecutionEvent(
                id=event_id,
                execution_id=record.id,
                sequence=sequence,
                event_type=event.get("type", "step"),
                name=event.get("name"),
                status=event.get("status"),
                description=event.get("description"),
                payload=event,
            ))
            db.commit()
            return event
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
        error_code: str | None = None,
    ) -> None:
        db = SessionLocal()
        try:
            record = db.get(RuntimeExecution, UUID(execution_id))
            if record is None:
                return
            self._transition(record, status)
            record.agent = agent or record.agent
            record.result_message = message
            record.error = error
            if error_code:
                record.runtime_metadata = {**(record.runtime_metadata or {}), "error_code": error_code}
            record.duration_ms = duration_ms
            record.completed_at = datetime.utcnow()
            append_audit_event(
                db, tenant_id=record.tenant_id, actor_id=record.user_id,
                action=f"runtime.{status.lower()}", target_type="runtime_execution",
                target_id=execution_id, correlation_id=str(record.workflow_id),
                metadata={"agent_id":record.selected_agent_id,"provider":record.provider_name,"model":record.model_name,"duration_ms":duration_ms,"error":error},
            )
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
                    persisted = db.query(RuntimeExecutionEvent).filter_by(execution_id=record.id).order_by(RuntimeExecutionEvent.sequence).all()
                    persisted_final = False
                    for item in persisted:
                        yield item.payload
                        persisted_final = persisted_final or bool(item.payload.get("final"))
                    if persisted_final:
                        return
                    if record.status in {"COMPLETED", "FAILED", "CANCELLED"}:
                        yield {
                            "type": "completed"
                            if record.status == "COMPLETED"
                            else "step",
                            "name": "Result Generated"
                            if record.status == "COMPLETED"
                            else "Runtime Execution",
                            "description": (
                                "Response delivered"
                                if record.status == "COMPLETED"
                                else self._safe_error_message(
                                    Exception(record.error or "")
                                )
                            ),
                            "status": (
                                "completed"
                                if record.status == "COMPLETED"
                                else "cancelled"
                                if record.status == "CANCELLED"
                                else "failed"
                            ),
                            "timestamp": (
                                record.completed_at or record.started_at
                            ).isoformat(),
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
