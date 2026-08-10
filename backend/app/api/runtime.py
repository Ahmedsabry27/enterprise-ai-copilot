import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.application_service import AgentIdentity
from app.auth.dependencies import get_current_user
from app.database.dependencies import get_db
from app.models.runtime_execution import RuntimeContinuation, RuntimeExecution
from app.services.runtime_execution_service import runtime_execution_service

router = APIRouter(prefix="/api/runtime", tags=["Runtime"])


class ContinueRequest(BaseModel):
    continuation_id: UUID
    values: dict = Field(default_factory=dict)


def _runtime_response(db: Session, execution: RuntimeExecution) -> dict:
    continuation = (
        db.query(RuntimeContinuation)
        .filter(
            RuntimeContinuation.execution_id == execution.id,
            RuntimeContinuation.status == "pending",
            RuntimeContinuation.consumed_at.is_(None),
        )
        .order_by(RuntimeContinuation.created_at.desc())
        .first()
    )
    continuation_payload = None
    if continuation is not None:
        schema = continuation.schema or {}
        continuation_payload = {
            "kind": continuation.kind,
            "continuation_id": str(continuation.id),
            "fields": schema.get("fields", []),
            "known_values": {
                key: value
                for key, value in (continuation.known_values or {}).items()
                if not key.startswith("_")
            },
            "required_role": continuation.required_role,
            "title": (
                "Approval required"
                if continuation.kind == "approval"
                else "Additional information required"
            ),
            "description": (
                "A governed action requires approval."
                if continuation.kind == "approval"
                else "Provide the unresolved values needed to continue this plan."
            ),
        }
    return {
        "execution_id": str(execution.id), "workflow_id": str(execution.workflow_id),
        "status": execution.status, "agent": execution.agent,
        "agent_id": execution.selected_agent_id, "provider": execution.provider_name,
        "model": execution.model_name, "duration_ms": execution.duration_ms,
        "token_usage": execution.token_usage, "estimated_cost": execution.estimated_cost,
        "metadata": execution.runtime_metadata,
        "started_at": execution.started_at, "finished_at": execution.completed_at,
        "error": execution.error, "error_code": (execution.runtime_metadata or {}).get("error_code"),
        "result_message": execution.result_message,
        "continuation": continuation_payload,
    }


@router.get("")
def get_conversation_runtime(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    execution = db.query(RuntimeExecution).filter_by(
        conversation_id=conversation_id, user_id=user["sub"]
    ).order_by(RuntimeExecution.started_at.desc()).first()
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return _runtime_response(db, execution)


@router.get("/{execution_id}")
def get_runtime_execution(
    execution_id: UUID,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    execution = runtime_execution_service.get_for_user(db, execution_id, user["sub"])
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return _runtime_response(db, execution)


@router.post("/{execution_id}/continue")
async def continue_runtime_execution(
    execution_id: UUID,
    payload: ContinueRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    try:
        execution = await runtime_execution_service.continue_execution(
            db, execution_id=execution_id, user_id=user["sub"],
            continuation_id=payload.continuation_id, values=payload.values, action="input",
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return {"execution_id": str(execution.id), "workflow_id": str(execution.workflow_id), "status": execution.status}


@router.post("/{execution_id}/approve")
async def approve_runtime_execution(execution_id: UUID, payload: ContinueRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    try:
        execution = await runtime_execution_service.continue_execution(db, execution_id=execution_id, user_id=user["sub"], continuation_id=payload.continuation_id, values=payload.values, action="approve", resume_identity=AgentIdentity.from_claims(user))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return {"execution_id": str(execution.id), "workflow_id": str(execution.workflow_id), "status": execution.status}


@router.post("/{execution_id}/deny")
async def deny_runtime_execution(execution_id: UUID, payload: ContinueRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    try:
        execution = await runtime_execution_service.continue_execution(db, execution_id=execution_id, user_id=user["sub"], continuation_id=payload.continuation_id, values=payload.values, action="deny", resume_identity=AgentIdentity.from_claims(user))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return {"execution_id": str(execution.id), "status": execution.status}


@router.post("/cancel/{execution_id}")
async def cancel_runtime_execution(
    execution_id: UUID,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    execution = await runtime_execution_service.cancel(
        db, execution_id=execution_id, user_id=user["sub"]
    )
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return {"execution_id": str(execution.id), "status": execution.status}


@router.get("/events/{execution_id}")
async def runtime_events_stream(
    execution_id: UUID,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    execution = runtime_execution_service.get_for_user(db, execution_id, user["sub"])
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")

    async def event_generator():
        async for event in runtime_execution_service.stream(str(execution_id)):
            if event.get("type") == "heartbeat":
                yield ": heartbeat\n\n"
                continue
            payload = {
                **event,
                "execution_id": str(execution_id),
                "workflow_id": str(execution.workflow_id),
            }
            # A named SSE event makes the contract consumable by standard EventSource
            # clients as well as the authenticated fetch-based subscriber.
            yield f"event: {payload.get('type', 'step')}\ndata: {json.dumps(payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
