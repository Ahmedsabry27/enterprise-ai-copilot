from __future__ import annotations

import re
from datetime import UTC, datetime
from time import perf_counter
from urllib.parse import urlparse

from app.api.tools import identity
from app.auth.dependencies import get_current_user
from app.database.dependencies import get_db
from app.database.models.agent import Agent
from app.database.models.agent_assignment import AgentToolAssignment
from app.database.models.audit import AuditLog
from app.database.models.integration import (
    IntegrationAgentAssignment,
    IntegrationCapability,
    IntegrationConnection,
    IntegrationUsage,
)
from app.integrations.errors import IntegrationError
from app.integrations.provisioning import (
    disable_connection_capabilities,
    provision_capability,
    sync_connection_assignments,
    unprovision_capability,
)
from app.integrations.registry import connector_registry
from app.integrations.secrets import secret_provider
from app.tool_discovery.indexing import index_tools
from app.tool_sdk.service import registry
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/integrations", tags=["Integrations"])

CATALOG = [
    {
        "type": "jira",
        "name": "Jira Cloud",
        "category": "Work Management",
        "description": "Search, create and manage Jira Cloud issues.",
        "auth_methods": ["api_token"],
        "planned_auth_methods": ["oauth2"],
        "read_capabilities": 5,
        "write_capabilities": 5,
    },
    {
        "type": "servicenow",
        "name": "ServiceNow",
        "category": "ITSM",
        "description": "Service management records and workflows.",
        "auth_methods": ["oauth2", "api_token"],
    },
    {
        "type": "github",
        "name": "GitHub",
        "category": "Developer Tools",
        "description": "Repositories, issues, pull requests and workflows.",
        "auth_methods": ["oauth2", "api_token"],
    },
    {
        "type": "microsoft_graph",
        "name": "Microsoft Graph",
        "category": "Productivity",
        "description": "Microsoft 365 resources through Graph.",
        "auth_methods": ["oauth2"],
    },
    {
        "type": "sharepoint",
        "name": "SharePoint",
        "category": "Knowledge",
        "description": "Sites, libraries and enterprise content.",
        "auth_methods": ["oauth2"],
    },
    {
        "type": "azure_blob",
        "name": "Azure Blob",
        "category": "Cloud Storage",
        "description": "Azure object storage containers and blobs.",
        "auth_methods": ["managed_identity", "oauth2"],
    },
    {
        "type": "azure_key_vault",
        "name": "Azure Key Vault",
        "category": "Secrets",
        "description": "Governed access to Azure secrets and keys.",
        "auth_methods": ["managed_identity", "oauth2"],
    },
    {
        "type": "slack",
        "name": "Slack",
        "category": "Collaboration",
        "description": "Channels, messages and collaboration workflows.",
        "auth_methods": ["oauth2"],
    },
    {
        "type": "salesforce",
        "name": "Salesforce",
        "category": "CRM",
        "description": "CRM objects, search and business workflows.",
        "auth_methods": ["oauth2"],
    },
    {
        "type": "sap",
        "name": "SAP",
        "category": "ERP",
        "description": "Enterprise resource planning capabilities.",
        "auth_methods": ["oauth2", "client_credentials"],
    },
    {
        "type": "rest_api",
        "name": "Generic REST API",
        "category": "Custom",
        "description": "Schema-driven governed REST capabilities.",
        "auth_methods": ["api_token", "oauth2"],
    },
]


def require(user: dict, permission: str):
    ctx = identity(user)
    if "tools.admin" not in ctx.permissions and permission not in ctx.permissions:
        raise HTTPException(
            403,
            {
                "code": "PERMISSION_DENIED",
                "message": f"{permission} permission is required",
            },
        )
    return ctx


def audit(
    db: Session,
    ctx,
    event: str,
    row: IntegrationConnection,
    metadata: dict | None = None,
):
    db.add(
        AuditLog(
            tenant_id=ctx.tenant_id,
            user_id=ctx.actor_id,
            event_type=event,
            entity="integration_connection",
            entity_id=row.id,
            timestamp=datetime.now(UTC),
            actor_id=ctx.actor_id,
            action=event,
            target_type="integration_connection",
            target_id=row.id,
            metadata_json=metadata or {},
            created_at=datetime.now(UTC),
        )
    )


def get_row(db: Session, tenant_id: str, connection_id: str) -> IntegrationConnection:
    row = (
        db.query(IntegrationConnection)
        .filter_by(id=connection_id, tenant_id=tenant_id)
        .first()
    )
    if not row:
        raise HTTPException(
            404,
            {
                "code": "INTEGRATION_NOT_FOUND",
                "message": "Integration connection not found",
            },
        )
    return row


def counts(db: Session, row: IntegrationConnection) -> dict:
    capabilities = (
        db.query(IntegrationCapability)
        .filter_by(connection_id=row.id, tenant_id=row.tenant_id)
        .all()
    )
    return {
        "tools_count": sum(
            x.capability_type == "tool" and x.provisioned for x in capabilities
        ),
        "actions_count": sum(
            x.capability_type == "action" and x.provisioned for x in capabilities
        ),
        "agents_count": db.query(IntegrationAgentAssignment)
        .filter_by(connection_id=row.id, tenant_id=row.tenant_id)
        .count(),
    }


def serialize(db: Session, row: IntegrationConnection) -> dict:
    return {
        "id": row.id,
        "connector_type": row.connector_type,
        "name": row.name,
        "display_name": row.display_name,
        "description": row.description,
        "auth_type": row.auth_type,
        "status": row.status,
        "health_status": row.health_status,
        "base_url": row.base_url,
        "credential_configured": bool(row.secret_ref),
        "configuration": row.configuration,
        "metadata": row.safe_metadata,
        "last_verified_at": row.last_verified_at,
        "last_error_code": row.last_error_code,
        "last_error_message_safe": row.last_error_message_safe,
        "created_by": row.created_by,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "enabled": row.enabled,
        "lock_version": row.lock_version,
        **counts(db, row),
    }


class ConnectionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    connector_type: str = Field(min_length=1, max_length=80)
    name: str | None = Field(None, max_length=120)
    display_name: str = Field(min_length=1, max_length=160)
    description: str = Field("", max_length=2000)
    auth_type: str
    base_url: str
    secret_ref: str | None = None
    credential_email: str | None = Field(None, max_length=320)
    credential_token: SecretStr | None = Field(None, repr=False)
    configuration: dict = Field(default_factory=dict)
    enabled: bool = False

    @field_validator("base_url")
    @classmethod
    def public_https(cls, value: str):
        parsed = urlparse(value)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.hostname in {"localhost", "127.0.0.1"}
        ):
            raise ValueError("base_url must be a public HTTPS URL")
        return value.rstrip("/")

    @field_validator("secret_ref")
    @classmethod
    def valid_secret_reference(cls, value: str | None):
        if value and not value.startswith(("env://", "aws-secrets://")):
            raise ValueError(
                "Use Jira email and API token fields for credentials, or provide an env:// or aws-secrets:// reference"
            )
        return value


class ConnectionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str | None = Field(None, min_length=1, max_length=160)
    description: str | None = Field(None, max_length=2000)
    auth_type: str | None = None
    base_url: str | None = None
    secret_ref: str | None = None
    configuration: dict | None = None
    enabled: bool | None = None
    lock_version: int


class CapabilityUpdate(BaseModel):
    enabled: bool | None = None
    approval_required: bool | None = None
    governance: dict | None = None


class AssignmentPayload(BaseModel):
    capability_names: list[str] = Field(default_factory=list)


class ExecutionPayload(BaseModel):
    arguments: dict = Field(default_factory=dict)
    agent_id: str | None = None
    execution_id: str | None = None


@router.get("/catalog")
def catalog(user: dict = Depends(get_current_user)):
    require(user, "integrations.read")
    implemented = connector_registry.implemented()
    return [
        {
            **item,
            "implementation_status": "available"
            if item["type"] in implemented
            else "coming_soon",
        }
        for item in CATALOG
    ]


@router.get("")
def list_connections(
    search: str | None = None,
    status: str | None = None,
    connector_type: str | None = None,
    health: str | None = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    ctx = require(user, "integrations.read")
    query = db.query(IntegrationConnection).filter_by(tenant_id=ctx.tenant_id)
    if search:
        query = query.filter(IntegrationConnection.display_name.ilike(f"%{search}%"))
    if status:
        query = query.filter_by(status=status)
    if connector_type:
        query = query.filter_by(connector_type=connector_type)
    if health:
        query = query.filter_by(health_status=health)
    return [
        serialize(db, row)
        for row in query.order_by(IntegrationConnection.updated_at.desc()).all()
    ]


@router.post("", status_code=201)
def create_connection(
    payload: ConnectionCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    ctx = require(user, "integrations.manage")
    connector_registry.get(payload.connector_type)
    slug = payload.name or re.sub(
        r"[^a-z0-9]+", "-", payload.display_name.lower()
    ).strip("-")
    if not payload.secret_ref and not (
        payload.credential_email and payload.credential_token
    ):
        raise HTTPException(
            422,
            {
                "code": "INVALID_CONFIGURATION",
                "message": "Provide Jira account email and API token, or a secure secret reference",
            },
        )
    row = IntegrationConnection(
        tenant_id=ctx.tenant_id,
        connector_type=payload.connector_type,
        name=slug,
        display_name=payload.display_name,
        description=payload.description,
        auth_type=payload.auth_type,
        base_url=payload.base_url,
        secret_ref=payload.secret_ref,
        configuration=payload.configuration,
        enabled=payload.enabled,
        status="configured",
        health_status="unknown",
        created_by=ctx.actor_id,
    )
    db.add(row)
    db.flush()
    if payload.credential_email and payload.credential_token:
        try:
            row.secret_ref = secret_provider.store(
                ctx.tenant_id,
                row.id,
                {
                    "email": payload.credential_email,
                    "api_token": payload.credential_token.get_secret_value(),
                },
            )
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                503,
                {
                    "code": "SECRET_STORAGE_UNAVAILABLE",
                    "message": "The credential could not be stored securely in AWS Secrets Manager",
                },
            ) from exc
    audit(db, ctx, "integration.created", row)
    db.commit()
    db.refresh(row)
    return serialize(db, row)


@router.get("/{connection_id}")
def get_connection(
    connection_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    ctx = require(user, "integrations.read")
    return serialize(db, get_row(db, ctx.tenant_id, connection_id))


@router.patch("/{connection_id}")
def update_connection(
    connection_id: str,
    payload: ConnectionUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    ctx = require(user, "integrations.manage")
    row = get_row(db, ctx.tenant_id, connection_id)
    if row.lock_version != payload.lock_version:
        raise HTTPException(
            409,
            {
                "code": "LOCK_VERSION_CONFLICT",
                "message": "Connection was updated by another user",
            },
        )
    for key, value in payload.model_dump(
        exclude_unset=True, exclude={"lock_version"}
    ).items():
        setattr(row, key, value)
    row.lock_version += 1
    row.status = "configured" if row.enabled else "disabled"
    audit(db, ctx, "integration.updated", row)
    db.commit()
    db.refresh(row)
    return serialize(db, row)


@router.delete("/{connection_id}")
def disable_connection(
    connection_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    ctx = require(user, "integrations.manage")
    row = get_row(db, ctx.tenant_id, connection_id)
    row.enabled = False
    row.status = "disabled"
    row.health_status = "unknown"
    disable_connection_capabilities(db, row, registry)
    row.lock_version += 1
    audit(db, ctx, "integration.disconnected", row)
    db.commit()
    return serialize(db, row)


@router.post("/{connection_id}/test")
async def test_connection(
    connection_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    ctx = require(user, "integrations.test")
    row = get_row(db, ctx.tenant_id, connection_id)
    connector = connector_registry.get(row.connector_type)
    try:
        result = await connector.test_connection(
            row, secret_provider.resolve(row.secret_ref)
        )
        row.health_status = "healthy"
        row.status = "connected"
        row.enabled = True
        row.last_error_code = row.last_error_message_safe = None
        row.safe_metadata = {**row.safe_metadata, **result}
        event = "integration.connected"
    except IntegrationError as exc:
        row.health_status = "unhealthy"
        row.status = "error"
        row.last_error_code = exc.code
        row.last_error_message_safe = exc.safe_message
        result = {"healthy": False, "code": exc.code, "message": exc.safe_message}
        event = "integration.tested"
    row.last_verified_at = datetime.now(UTC)
    audit(
        db,
        ctx,
        event,
        row,
        {"healthy": result.get("healthy", True), "error_code": row.last_error_code},
    )
    db.commit()
    if not result.get("healthy", True):
        raise HTTPException(502, result)
    return result


@router.post("/{connection_id}/discover")
async def discover(
    connection_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    ctx = require(user, "integrations.capabilities.manage")
    row = get_row(db, ctx.tenant_id, connection_id)
    connector = connector_registry.get(row.connector_type)
    try:
        definitions, metadata = await connector.discover_capabilities(
            row, secret_provider.resolve(row.secret_ref)
        )
    except IntegrationError as exc:
        raise HTTPException(
            exc.status_code, {"code": exc.code, "message": exc.safe_message}
        ) from None
    for item in definitions:
        capability = (
            db.query(IntegrationCapability)
            .filter_by(connection_id=row.id, external_name=item.name)
            .first()
        )
        if not capability:
            capability = IntegrationCapability(
                connection_id=row.id,
                tenant_id=ctx.tenant_id,
                external_name=item.name,
                display_name=item.display_name,
                description=item.description,
                capability_type=item.capability_type,
            )
            db.add(capability)
        capability.version = item.version
        capability.input_schema = item.input_schema
        capability.output_schema = item.output_schema
        capability.risk_level = item.risk_level
        capability.approval_required = item.approval_required
        provision_capability(db, row, capability, ctx.actor_id, registry)
    row.safe_metadata = {**row.safe_metadata, **metadata}
    sync_connection_assignments(db, row, ctx.actor_id)
    audit(
        db, ctx, "integration.capabilities.discovered", row, {"count": len(definitions)}
    )
    db.commit()
    await index_tools(db, ctx.tenant_id, batch_size=500)
    return {"capabilities": len(definitions), "metadata": metadata}


@router.get("/{connection_id}/capabilities")
def capabilities(
    connection_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    ctx = require(user, "integrations.read")
    get_row(db, ctx.tenant_id, connection_id)
    return [
        {
            "id": x.id,
            "name": x.external_name,
            "display_name": x.display_name,
            "description": x.description,
            "type": x.capability_type,
            "version": x.version,
            "input_schema": x.input_schema,
            "output_schema": x.output_schema,
            "risk": x.risk_level,
            "approval_required": x.approval_required,
            "governance": x.governance,
            "enabled": x.enabled,
            "provisioned": x.provisioned,
        }
        for x in db.query(IntegrationCapability)
        .filter_by(connection_id=connection_id, tenant_id=ctx.tenant_id)
        .all()
    ]


@router.patch("/{connection_id}/capabilities/{capability_name:path}")
def update_capability(
    connection_id: str,
    capability_name: str,
    payload: CapabilityUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    ctx = require(user, "integrations.capabilities.manage")
    row = get_row(db, ctx.tenant_id, connection_id)
    cap = (
        db.query(IntegrationCapability)
        .filter_by(
            connection_id=row.id, tenant_id=ctx.tenant_id, external_name=capability_name
        )
        .first()
    )
    if not cap:
        raise HTTPException(
            404,
            {
                "code": "CAPABILITY_UNAVAILABLE",
                "message": "Capability has not been discovered",
            },
        )
    for key, value in payload.model_dump(
        exclude_unset=True, exclude={"enabled"}
    ).items():
        setattr(cap, key, value)
    if payload.enabled is not None:
        if payload.enabled:
            provision_capability(db, row, cap, ctx.actor_id, registry)
        else:
            unprovision_capability(db, row, cap, registry)
        audit(
            db,
            ctx,
            f"integration.capability.{'enabled' if payload.enabled else 'disabled'}",
            row,
            {"capability": cap.external_name},
        )
    db.commit()
    return {
        "name": cap.external_name,
        "enabled": cap.enabled,
        "provisioned": cap.provisioned,
    }


@router.get("/{connection_id}/agents")
def connection_agents(
    connection_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    ctx = require(user, "integrations.read")
    get_row(db, ctx.tenant_id, connection_id)
    assignments = {
        x.agent_id: x
        for x in db.query(IntegrationAgentAssignment)
        .filter_by(connection_id=connection_id, tenant_id=ctx.tenant_id)
        .all()
    }
    return [
        {
            "id": a.id,
            "uuid": a.uuid,
            "name": a.name,
            "status": a.lifecycle_status,
            "assigned": a.id in assignments,
            "capability_names": assignments[a.id].capability_names
            if a.id in assignments
            else [],
        }
        for a in db.query(Agent).filter_by(tenant_id=ctx.tenant_id).all()
    ]


@router.post("/{connection_id}/agents/{agent_id}")
def assign_agent(
    connection_id: str,
    agent_id: int,
    payload: AssignmentPayload,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    ctx = require(user, "integrations.agents.manage")
    row = get_row(db, ctx.tenant_id, connection_id)
    agent = db.query(Agent).filter_by(id=agent_id, tenant_id=ctx.tenant_id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")
    valid = {
        x.external_name: x
        for x in db.query(IntegrationCapability)
        .filter_by(
            connection_id=row.id,
            tenant_id=ctx.tenant_id,
            enabled=True,
            provisioned=True,
        )
        .all()
    }
    if not set(payload.capability_names) <= set(valid):
        raise HTTPException(
            422,
            {
                "code": "CAPABILITY_UNAVAILABLE",
                "message": "Assign only enabled, provisioned capabilities",
            },
        )
    assignment = (
        db.query(IntegrationAgentAssignment)
        .filter_by(connection_id=row.id, agent_id=agent.id)
        .first()
    )
    if not assignment:
        assignment = IntegrationAgentAssignment(
            connection_id=row.id,
            agent_id=agent.id,
            tenant_id=ctx.tenant_id,
            created_by=ctx.actor_id,
        )
        db.add(assignment)
    assignment.capability_names = payload.capability_names
    for name in payload.capability_names:
        cap = valid[name]
        tool_assignment = (
            db.query(AgentToolAssignment)
            .filter_by(agent_id=agent.id, tool_name=name, assignment_action="execute")
            .first()
        )
        if not tool_assignment:
            db.add(
                AgentToolAssignment(
                    agent_id=agent.id,
                    agent_version=agent.current_version,
                    tenant_id=ctx.tenant_id,
                    tool_name=name,
                    version_restriction=cap.version,
                    assignment_action="execute",
                    enabled=True,
                    risk_mode="write" if cap.capability_type == "action" else "read",
                    approval_required=cap.approval_required,
                    added_by=ctx.actor_id,
                )
            )
    audit(
        db,
        ctx,
        "integration.agent.assigned",
        row,
        {"agent_id": agent.uuid, "capabilities": payload.capability_names},
    )
    db.commit()
    return {"assigned": True}


@router.delete("/{connection_id}/agents/{agent_id}")
def unassign_agent(
    connection_id: str,
    agent_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    ctx = require(user, "integrations.agents.manage")
    row = get_row(db, ctx.tenant_id, connection_id)
    assignment = (
        db.query(IntegrationAgentAssignment)
        .filter_by(connection_id=row.id, agent_id=agent_id, tenant_id=ctx.tenant_id)
        .first()
    )
    if assignment:
        db.delete(assignment)
    audit(db, ctx, "integration.agent.unassigned", row, {"agent_id": agent_id})
    db.commit()
    return {"assigned": False}


@router.post("/{connection_id}/execute/{capability_name:path}")
async def execute(
    connection_id: str,
    capability_name: str,
    payload: ExecutionPayload,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    ctx = require(user, "integrations.execute")
    row = get_row(db, ctx.tenant_id, connection_id)
    cap = (
        db.query(IntegrationCapability)
        .filter_by(
            connection_id=row.id,
            tenant_id=ctx.tenant_id,
            external_name=capability_name,
            enabled=True,
            provisioned=True,
        )
        .first()
    )
    if not cap:
        raise HTTPException(
            422,
            {"code": "CAPABILITY_UNAVAILABLE", "message": "Capability is not enabled"},
        )
    required = cap.input_schema.get("required", [])
    missing = [name for name in required if payload.arguments.get(name) in (None, "")]
    if missing:
        return {
            "status": "WAITING_FOR_INPUT",
            "missing_fields": missing,
            "input_schema": cap.input_schema,
            "connection_id": row.id,
            "capability": cap.external_name,
            "execution_id": payload.execution_id,
        }
    if cap.capability_type == "action" and cap.approval_required:
        return {
            "status": "WAITING_FOR_APPROVAL",
            "connection_id": row.id,
            "capability": cap.external_name,
            "execution_id": payload.execution_id,
        }
    started = perf_counter()
    connector = connector_registry.get(row.connector_type)
    try:
        secret = secret_provider.resolve(row.secret_ref)
        result = await (
            connector.execute_tool(row, cap.external_name, payload.arguments, secret)
            if cap.capability_type == "tool"
            else connector.execute_action(
                row, cap.external_name, payload.arguments, secret
            )
        )
        status = "succeeded"
        error_code = None
    except IntegrationError as exc:
        result = None
        status = "failed"
        error_code = exc.code
        db.add(
            IntegrationUsage(
                connection_id=row.id,
                tenant_id=ctx.tenant_id,
                capability_name=cap.external_name,
                capability_type=cap.capability_type,
                agent_id=payload.agent_id,
                actor_id=ctx.actor_id,
                execution_id=payload.execution_id,
                status=status,
                latency_ms=(perf_counter() - started) * 1000,
                error_code=error_code,
            )
        )
        audit(
            db,
            ctx,
            f"integration.{cap.capability_type}.executed",
            row,
            {
                "capability": cap.external_name,
                "status": status,
                "error_code": error_code,
            },
        )
        db.commit()
        raise HTTPException(
            exc.status_code, {"code": exc.code, "message": exc.safe_message}
        ) from None
    db.add(
        IntegrationUsage(
            connection_id=row.id,
            tenant_id=ctx.tenant_id,
            capability_name=cap.external_name,
            capability_type=cap.capability_type,
            agent_id=payload.agent_id,
            actor_id=ctx.actor_id,
            execution_id=payload.execution_id,
            status=status,
            latency_ms=(perf_counter() - started) * 1000,
        )
    )
    audit(
        db,
        ctx,
        f"integration.{cap.capability_type}.executed",
        row,
        {"capability": cap.external_name, "status": status},
    )
    db.commit()
    return {
        "status": "SUCCEEDED",
        "result": result,
        "connection_id": row.id,
        "capability": cap.external_name,
    }


@router.get("/{connection_id}/usage")
def usage(
    connection_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    ctx = require(user, "integrations.read")
    get_row(db, ctx.tenant_id, connection_id)
    rows = (
        db.query(IntegrationUsage)
        .filter_by(connection_id=connection_id, tenant_id=ctx.tenant_id)
        .all()
    )
    succeeded = sum(x.status == "succeeded" for x in rows)
    failed = len(rows) - succeeded
    return {
        "requests": len(rows),
        "successful": succeeded,
        "failed": failed,
        "average_latency_ms": round(sum(x.latency_ms or 0 for x in rows) / len(rows), 2)
        if rows
        else 0,
        "recent": [
            {
                "capability": x.capability_name,
                "type": x.capability_type,
                "agent_id": x.agent_id,
                "status": x.status,
                "latency_ms": x.latency_ms,
                "error_code": x.error_code,
                "timestamp": x.created_at,
            }
            for x in rows[-50:][::-1]
        ],
    }
