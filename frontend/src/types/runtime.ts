export type RuntimeStatus = "PENDING" | "RUNNING" | "WAITING_FOR_INPUT" | "WAITING_FOR_APPROVAL" | "COMPLETED" | "FAILED" | "CANCELLED" | "TIMED_OUT";
export type RuntimeStepStatus = "pending" | "running" | "completed" | "failed" | "waiting" | "cancelled";
export type RuntimeEventType = "step" | "completed" | "required_input" | "approval_required" | "tool_started" | "tool_completed" | "tool_failed" | "action_started" | "action_completed" | "action_failed" | "log" | "metric" | "knowledge_retrieval_started" | "knowledge_retrieval_completed" | "error" | "heartbeat";

export interface AgentCandidate { agent_id: string; name: string; slug: string; capabilities: string[]; provider: string; model?: string; confidence: number; reason: string }
export interface RequiredField { name: string; label: string; type: string; required?: boolean; options?: Array<string | {label:string;value:string}>; description?: string }
export interface RuntimeEvent {
  type: RuntimeEventType; execution_id: string; workflow_id: string; event_id?: string; sequence?: number; step_id?: string; name?: string; description?: string;
  status?: RuntimeStepStatus; timestamp?: string; agent?: string; agent_id?: string; provider?: string; model?: string;
  confidence?: number; candidates?: AgentCandidate[]; duration_ms?: number; message?: string; error?: string; final?: boolean;
  continuation_id?: string; fields?: RequiredField[]; metadata?: Record<string, unknown>; [key: string]: unknown;
}

export interface RuntimeExecutionViewModel {
  executionId?: string; workflowId?: string; status: RuntimeStatus; selectedAgent?: Record<string, unknown>;
  candidates: AgentCandidate[]; steps: RuntimeEvent[]; plan: unknown[]; requiredInput?: RuntimeEvent;
  approval?: RuntimeEvent; tools: RuntimeEvent[]; actions: RuntimeEvent[]; logs: RuntimeEvent[];
  metrics: Record<string, unknown>; sources: unknown[]; finalResponse?: string; error?: string;
}
