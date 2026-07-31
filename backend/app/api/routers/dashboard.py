from collections import Counter
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.dependencies import get_db
from app.models.runtime_execution import RuntimeExecution
from app.services.runtime_service import get_agent_registry


router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


def _executions(db: Session, user_id: str) -> list[RuntimeExecution]:
    return (
        db.query(RuntimeExecution)
        .filter(RuntimeExecution.user_id == user_id)
        .order_by(RuntimeExecution.started_at.desc())
        .all()
    )


@router.get("/metrics")
def dashboard_metrics(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    executions = _executions(db, user["sub"])
    status = Counter(execution.status for execution in executions)
    terminal = status["COMPLETED"] + status["FAILED"]
    actions = sum(
        1
        for execution in executions
        for step in execution.steps or []
        if step.get("name") == "Generate Report Action" and step.get("status") == "completed"
    )
    return {
        "total_workflows": len(executions),
        "active_workflows": status["RUNNING"],
        "active_agents": len(get_agent_registry().list_agents()),
        "actions_executed": actions,
        "success_rate": round((status["COMPLETED"] / terminal * 100) if terminal else 0, 1),
        "trends": {"workflows": 0, "agents": 0, "actions": 0, "success": 0},
    }


@router.get("/executions/trends")
def execution_trends(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    executions = _executions(db, user["sub"])
    today = datetime.now(UTC).date()
    buckets = []
    for days_ago in range(6, -1, -1):
        day = today - timedelta(days=days_ago)
        rows = [item for item in executions if item.started_at.date() == day]
        statuses = Counter(item.status for item in rows)
        buckets.append({
            "date": day.strftime("%b %d"),
            "successful": statuses["COMPLETED"],
            "running": statuses["RUNNING"],
            "failed": statuses["FAILED"],
        })
    return buckets


@router.get("/workflow-distribution")
def workflow_distribution(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    status = Counter(item.status for item in _executions(db, user["sub"]))
    return {
        "completed": status["COMPLETED"],
        "running": status["RUNNING"],
        "pending": status["PENDING"],
        "failed": status["FAILED"] + status["CANCELLED"],
    }


@router.get("/recent-executions")
def recent_executions(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    now = datetime.now(UTC)
    return [
        {
            "id": str(item.id),
            "workflow": item.goal or f"Workflow {str(item.workflow_id)[:8]}",
            "agent": item.agent or "default-agent",
            "status": item.status.lower(),
            "duration_ms": item.duration_ms,
            "started_at": item.started_at.isoformat(),
            "age_seconds": max(0, int((now.replace(tzinfo=None) - item.started_at).total_seconds())),
        }
        for item in _executions(db, user["sub"])[:6]
    ]


@router.get("/agents/status")
def agent_status(user: dict = Depends(get_current_user)):
    registry = get_agent_registry()
    return [
        {"name": name, "status": registry.get_status(name).value.lower()}
        for name in registry.list_agents()
        if registry.get_status(name) is not None
    ]
