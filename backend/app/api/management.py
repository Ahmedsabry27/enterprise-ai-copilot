from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.dependencies import get_db
from app.database.models.agent import Agent
from app.database.models.workflow import Workflow
from app.database.models.action import Action
from app.database.models.knowledge_source import KnowledgeSource
from app.models.runtime_execution import RuntimeExecution
from app.services.runtime_service import get_agent_registry
from app.api.runtime import runtime_events_stream
from uuid import UUID

router = APIRouter(prefix="/api", tags=["Management"])


class AgentPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: str = "Workflow"
    description: str = ""
    capabilities: list[str] = Field(default_factory=list)
    purpose: str = ""
    model: str = "GPT-5.5"
    memory_enabled: bool = True
    instructions: str = ""
    tools: list[str] = Field(default_factory=list)
    knowledge_sources: list[str] = Field(default_factory=list)
    permissions: dict[str, bool] = Field(default_factory=dict)


class AgentPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    status: str | None = None
    type: str | None = None
    description: str | None = None
    capabilities: list[str] | None = None
    purpose: str | None = None
    model: str | None = None
    memory_enabled: bool | None = None
    instructions: str | None = None
    tools: list[str] | None = None
    knowledge_sources: list[str] | None = None
    permissions: dict[str, bool] | None = None


class WorkflowPayload(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    assigned_agent: str | None = None
    trigger_type: str = "MANUAL"
    definition: dict = Field(default_factory=dict)
class ActionPayload(BaseModel):
    name: str
    type: str
    permissions: dict = Field(default_factory=dict)
class KnowledgePayload(BaseModel):
    name: str
    source_type: str = "DOCUMENT"
    location: str | None = None


def _agent_response(agent: Agent, executions: list[RuntimeExecution]) -> dict:
    config = json.loads(agent.configuration or "{}")
    related = [item for item in executions if item.agent == agent.name]
    finished = [item for item in related if item.status in {"COMPLETED", "FAILED"}]
    success_rate = round(100 * sum(item.status == "COMPLETED" for item in finished) / len(finished), 1) if finished else 0
    last_active = max((item.started_at for item in related), default=agent.created_at)
    return {"id": agent.id, "name": agent.name, "status": agent.status.lower(), "type": config.get("type", "Workflow"), "description": config.get("description", ""), "purpose": config.get("purpose", ""), "model": config.get("model", "GPT-5.5"), "memory_enabled": config.get("memory_enabled", True), "instructions": config.get("instructions", ""), "capabilities": config.get("capabilities", []), "tools": config.get("tools", []), "knowledge_sources": config.get("knowledge_sources", []), "permissions": config.get("permissions", {}), "executions": len(related), "success_rate": success_rate, "last_active": last_active.isoformat(), "created_at": agent.created_at.isoformat()}


def _ensure_default_agent(db: Session) -> None:
    """Persist the runtime's default agent once so Chat history has an agent owner."""
    if db.query(Agent).filter(Agent.name == "default-agent").first() is None:
        db.add(Agent(name="default-agent", status="ONLINE", health="HEALTHY", configuration=json.dumps({"type": "Runtime", "description": "Default enterprise runtime agent", "purpose": "Execute general AI workflow tasks", "model": "GPT-5.5", "memory_enabled": True, "capabilities": ["task-execution"], "tools": ["generate-deployment-report"], "knowledge_sources": [], "permissions": {"Read Workflows": True, "Execute Actions": True, "Access Audit Logs": True, "Manage Agents": False}})))
        db.commit()


@router.get("/agents")
def list_agents(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    _ensure_default_agent(db)
    executions = db.query(RuntimeExecution).filter(RuntimeExecution.user_id == user["sub"]).all()
    return [_agent_response(agent, executions) for agent in db.query(Agent).order_by(Agent.name).all()]


@router.get("/agents/{agent_id}")
def get_agent(agent_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    _ensure_default_agent(db)
    agent = db.get(Agent, agent_id)
    if not agent: raise HTTPException(404, "Agent not found")
    executions = db.query(RuntimeExecution).filter(RuntimeExecution.user_id == user["sub"]).all()
    return _agent_response(agent, executions)


@router.get("/agents/{agent_id}/executions")
def get_agent_executions(agent_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    agent = db.get(Agent, agent_id)
    if not agent: raise HTTPException(404, "Agent not found")
    rows = db.query(RuntimeExecution).filter(RuntimeExecution.user_id == user["sub"], RuntimeExecution.agent == agent.name).order_by(RuntimeExecution.started_at.desc()).all()
    return [{"execution_id": str(row.id), "status": row.status.lower(), "started_at": row.started_at.isoformat(), "duration": row.duration_ms, "result": "SUCCESS" if row.status == "COMPLETED" else "FAILED" if row.status == "FAILED" else row.status} for row in rows]


@router.get("/executions/{execution_id}/events")
async def execution_events(execution_id: UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Compatibility route for execution detail screens; delegates to the durable runtime SSE stream."""
    return await runtime_events_stream(execution_id, db, user)

@router.get("/actions")
def list_actions(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return [{"id":x.id,"name":x.name,"type":x.type,"permissions":x.permissions,"status":x.status.lower(),"usage":x.usage} for x in db.query(Action).order_by(Action.name).all()]
@router.post("/actions",status_code=201)
def create_action(payload: ActionPayload, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    action=Action(name=payload.name,type=payload.type,permissions=payload.permissions,status="ENABLED",usage=0);db.add(action);db.commit();db.refresh(action);return {"id":action.id,"name":action.name,"type":action.type,"permissions":action.permissions,"status":"enabled","usage":0}
@router.patch("/actions/{action_id}")
def update_action(action_id:int, payload:dict, db:Session=Depends(get_db), user:dict=Depends(get_current_user)):
    action=db.get(Action,action_id)
    if not action: raise HTTPException(404,"Action not found")
    if "status" in payload: action.status=payload["status"].upper()
    db.commit();return {"id":action.id,"status":action.status.lower()}
@router.post("/actions/{action_id}/execute")
def execute_action(action_id:int, db:Session=Depends(get_db), user:dict=Depends(get_current_user)):
    action=db.get(Action,action_id)
    if not action: raise HTTPException(404,"Action not found")
    if action.status != "ENABLED": raise HTTPException(409,"Action is disabled")
    action.usage+=1;db.commit();return {"id":action.id,"status":"completed","usage":action.usage}
@router.get("/knowledge")
def list_knowledge(search:str|None=None,db:Session=Depends(get_db),user:dict=Depends(get_current_user)):
    rows=db.query(KnowledgeSource).order_by(KnowledgeSource.created_at.desc()).all()
    return [{"id":x.id,"name":x.name,"type":x.source_type,"location":x.location,"created_at":x.created_at.isoformat()} for x in rows if not search or search.lower() in x.name.lower()]
@router.post("/knowledge",status_code=201)
def create_knowledge(payload:KnowledgePayload,db:Session=Depends(get_db),user:dict=Depends(get_current_user)):
    item=KnowledgeSource(name=payload.name,source_type=payload.source_type,location=payload.location);db.add(item);db.commit();db.refresh(item);return {"id":item.id,"name":item.name,"type":item.source_type,"location":item.location}
@router.delete("/knowledge/{source_id}",status_code=204)
def delete_knowledge(source_id:int,db:Session=Depends(get_db),user:dict=Depends(get_current_user)):
    item=db.get(KnowledgeSource,source_id)
    if not item: raise HTTPException(404,"Knowledge source not found")
    db.delete(item);db.commit()


@router.post("/agents", status_code=status.HTTP_201_CREATED)
def create_agent(payload: AgentPayload, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if db.query(Agent).filter(Agent.name == payload.name).first():
        raise HTTPException(409, "An agent with this name already exists")
    agent = Agent(name=payload.name, status="ONLINE", health="HEALTHY", configuration=json.dumps(payload.model_dump(exclude={"name"})))
    db.add(agent); db.commit(); db.refresh(agent)
    return _agent_response(agent, [])


@router.patch("/agents/{agent_id}")
def update_agent(agent_id: int, payload: AgentPatch, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    agent = db.get(Agent, agent_id)
    if not agent: raise HTTPException(404, "Agent not found")
    data = payload.model_dump(exclude_none=True); config = json.loads(agent.configuration or "{}")
    for key in ("type", "description", "capabilities", "purpose", "model", "memory_enabled", "instructions", "tools", "knowledge_sources", "permissions"):
        if key in data: config[key] = data.pop(key)
    if "name" in data: agent.name = data["name"]
    if "status" in data: agent.status = data["status"].upper()
    agent.configuration = json.dumps(config); db.commit(); db.refresh(agent)
    return _agent_response(agent, [])


@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(agent_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    agent = db.get(Agent, agent_id)
    if not agent: raise HTTPException(404, "Agent not found")
    db.delete(agent); db.commit()


def _workflow_response(workflow: Workflow) -> dict:
    return {"id": workflow.id, "name": workflow.goal, "description": workflow.description or "", "assigned_agent": workflow.assigned_agent, "trigger_type": workflow.trigger_type, "definition": workflow.definition or {"nodes":[],"edges":[]}, "status": workflow.status.lower(), "executions": 0, "success_rate": 0, "last_modified": workflow.completed_at or workflow.created_at}


@router.get("/workflows")
def list_managed_workflows(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return [_workflow_response(item) for item in db.query(Workflow).order_by(Workflow.created_at.desc()).all()]


@router.post("/workflows", status_code=status.HTTP_201_CREATED)
def create_managed_workflow(payload: WorkflowPayload, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    workflow = Workflow(goal=payload.name, description=payload.description, assigned_agent=payload.assigned_agent, trigger_type=payload.trigger_type.upper(), definition=payload.definition, status="ACTIVE", created_by=user["sub"])
    db.add(workflow); db.commit(); db.refresh(workflow)
    return _workflow_response(workflow)

@router.get("/workflows/{workflow_id}")
def get_managed_workflow(workflow_id:int, db:Session=Depends(get_db), user:dict=Depends(get_current_user)):
    workflow=db.get(Workflow,workflow_id)
    if not workflow: raise HTTPException(404,"Workflow not found")
    return _workflow_response(workflow)

@router.put("/workflows/{workflow_id}")
def update_managed_workflow(workflow_id:int,payload:WorkflowPayload,db:Session=Depends(get_db),user:dict=Depends(get_current_user)):
    workflow=db.get(Workflow,workflow_id)
    if not workflow: raise HTTPException(404,"Workflow not found")
    workflow.goal=payload.name;workflow.description=payload.description;workflow.assigned_agent=payload.assigned_agent;workflow.trigger_type=payload.trigger_type.upper();workflow.definition=payload.definition;db.commit();db.refresh(workflow);return _workflow_response(workflow)


@router.post("/workflows/{workflow_id}/execute")
def execute_managed_workflow(workflow_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    workflow = db.get(Workflow, workflow_id)
    if not workflow: raise HTTPException(404, "Workflow not found")
    workflow.status = "RUNNING"; db.commit(); db.refresh(workflow)
    return _workflow_response(workflow)


@router.delete("/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_managed_workflow(workflow_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    workflow = db.get(Workflow, workflow_id)
    if not workflow: raise HTTPException(404, "Workflow not found")
    db.delete(workflow); db.commit()


@router.get("/audit")
def list_audit_logs(action: str | None = None, agent: str | None = None, date: str = "7d", search: str | None = None, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=30 if date == "30d" else 7)
    executions = db.query(RuntimeExecution).filter(RuntimeExecution.user_id == user["sub"], RuntimeExecution.started_at >= cutoff).order_by(RuntimeExecution.started_at.desc()).all()
    rows = [{"id": str(item.id), "time": item.started_at.isoformat(), "action": item.goal or "Runtime execution", "agent": item.agent or "default-agent", "status": item.status.lower(), "details": item.error or item.result_message or "Workflow execution recorded"} for item in executions]
    def matches(row):
        value = " ".join(str(v) for v in row.values()).lower()
        return (not action or action.lower() in row["action"].lower()) and (not agent or agent.lower() == row["agent"].lower()) and (not search or search.lower() in value)
    return [row for row in rows if matches(row)]
