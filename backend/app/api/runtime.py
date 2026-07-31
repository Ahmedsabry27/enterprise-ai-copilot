import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.dependencies import get_db
from app.services.runtime_execution_service import runtime_execution_service

router = APIRouter(prefix="/api/runtime", tags=["Runtime"])


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
