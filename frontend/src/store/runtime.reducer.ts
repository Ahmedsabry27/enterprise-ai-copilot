import type { RuntimeEvent, RuntimeExecutionViewModel } from "../types/runtime";

export const initialRuntimeState: RuntimeExecutionViewModel = {
  status: "PENDING", candidates: [], steps: [], plan: [], tools: [], actions: [], logs: [], metrics: {}, sources: [],
};

export function runtimeReducer(state: RuntimeExecutionViewModel, action: {type:"started"; executionId:string; workflowId:string} | {type:"event"; event:RuntimeEvent} | {type:"reset"}): RuntimeExecutionViewModel {
  if (action.type === "reset") return initialRuntimeState;
  if (action.type === "started") return {...initialRuntimeState, executionId:action.executionId, workflowId:action.workflowId, status:"RUNNING"};
  const event = action.event;
  const logicalType = event.type.startsWith("tool_") ? "tool" : event.type.startsWith("action_") ? "action" : event.type;
  const key = event.step_id || `${logicalType}:${event.name || ""}`;
  const identity = (item:RuntimeEvent) => item.step_id || `${item.type.startsWith("tool_") ? "tool" : item.type.startsWith("action_") ? "action" : item.type}:${item.name || ""}`;
  const merge = (items:RuntimeEvent[]) => {
    const index=items.findIndex(item=>identity(item)===key);
    if(index<0)return [...items,event];
    const copy=[...items];copy[index]={...copy[index],...event};return copy;
  };
  const next: RuntimeExecutionViewModel = {...state};
  if (event.type === "required_input") { next.requiredInput=event; next.status="WAITING_FOR_INPUT"; }
  else if (event.type === "approval_required") { next.approval=event; next.status="WAITING_FOR_APPROVAL"; }
  else if (event.type.startsWith("tool_")) next.tools=merge(state.tools);
  else if (event.type.startsWith("action_")) next.actions=merge(state.actions);
  else if (event.type === "log") next.logs=merge(state.logs);
  else if (event.type === "metric") next.metrics={...state.metrics,...(event.metadata || {})};
  else if (event.type === "knowledge_retrieval_completed" && event.source) next.sources=[...state.sources,event.source];
  else if (event.type !== "heartbeat" && event.type !== "error") next.steps=merge(state.steps);
  if (event.plan) next.plan=(event.plan as {steps?:unknown[]}).steps || [];
  if (event.agent) next.selectedAgent={...state.selectedAgent,name:event.agent,id:event.agent_id,provider:event.provider,model:event.model,confidence:event.confidence,selectionMode:event.selection_mode,reason:event.selection_reason,capabilities:event.capabilities,tools:event.assigned_tools,knowledgeSourceCount:event.knowledge_source_count};
  if (event.candidates) next.candidates=event.candidates;
  if (event.provider) next.metrics={...next.metrics,provider:event.provider};
  if (event.model) next.metrics={...next.metrics,model:event.model};
  if (event.final) {
    next.status=event.type === "error" || event.status === "failed" ? "FAILED" : event.status === "cancelled" ? "CANCELLED" : "COMPLETED";
    if(next.status!=="COMPLETED") {
      const terminalStatus=next.status==="CANCELLED"?"cancelled":"failed";
      next.tools=next.tools.map(item=>item.status==="running"?{...item,status:terminalStatus,description:item.description||"Execution ended before the tool returned"}:item);
      next.actions=next.actions.map(item=>item.status==="running"?{...item,status:terminalStatus,description:item.description||"Execution ended before the action returned"}:item);
    }
    next.finalResponse=next.status==="COMPLETED"?event.message:undefined;
    next.error=next.status==="COMPLETED"?undefined:(event.error||event.description);
  }
  return next;
}
