import { useEffect, useReducer, useRef, useState } from "react";

import { updateConversationTitle } from "../api/conversationApi";
import { startExecution } from "../services/chat.service";
import { approveRuntime, cancelRuntime, continueRuntime, denyRuntime, getConversationRuntime, getRuntime, subscribeRuntime } from "../services/runtime.service";
import { initialRuntimeState, runtimeReducer } from "../store/runtime.reducer";
import createConversationTitle from "../utils/createConversationTitle";

const timestamp = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

export default function useChat(conversation) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [responseId, setResponseId] = useState(null);
  const [activeExecution,setActiveExecution]=useState(null);
  const [runtime,dispatchRuntime]=useReducer(runtimeReducer,initialRuntimeState);
  const runtimeRef = useRef(null);
  const executionRef = useRef(null);
  const lastRequestRef=useRef(null);

  function connectRuntime(assistantId, execution) {
    runtimeRef.current?.();
    executionRef.current = execution.execution_id;
    runtimeRef.current = subscribeRuntime(
      execution.execution_id,
      (event) => applyEvent(assistantId, execution, event),
      (error) => failExecution(assistantId, error.message),
    );
  }

  function applyEvent(assistantId,execution,event){
    dispatchRuntime({type:"event",event});
    if(event.type==="required_input"||event.type==="approval_required"){
      setActiveExecution(current=>({...current,...execution,assistant_id:assistantId,continuation:{kind:event.type==="required_input"?"input":"approval",continuation_id:event.continuation_id,fields:event.fields||[],...event}}));setLoading(false);
    }
    setMessages(current=>current.map(message=>{if(message.id!==assistantId)return message;const metadata={...message.metadata,execution_id:execution.execution_id,workflow_id:execution.workflow_id,status:event.final?(event.status==="failed"?"FAILED":event.status==="cancelled"?"CANCELLED":"COMPLETED"):event.status==="waiting"?(event.type==="approval_required"?"WAITING_FOR_APPROVAL":"WAITING_FOR_INPUT"):"RUNNING",error:event.error??message.metadata?.error,agent:event.agent??message.metadata?.agent,agent_id:event.agent_id??message.metadata?.agent_id,provider:event.provider??message.metadata?.provider,model:event.model??message.metadata?.model,confidence:event.confidence??message.metadata?.confidence,candidates:event.candidates??message.metadata?.candidates,duration_ms:event.duration_ms??message.metadata?.duration_ms,tools:event.type?.startsWith("tool_")?[...(message.metadata?.tools||[]),event]:message.metadata?.tools,actions:event.type?.startsWith("action_")?[...(message.metadata?.actions||[]),event]:message.metadata?.actions,plan:event.plan??message.metadata?.plan};if(event.type==="heartbeat")return message;const isTimelineEvent=!(["error","metric","log","knowledge_retrieval_started","knowledge_retrieval_completed"].includes(event.type));const step={id:event.step_id||event.name||event.type,name:event.name||event.type,description:event.description,status:event.status,timestamp:event.timestamp,intent:event.intent,extracted_parameters:event.extracted_parameters,required_capabilities:event.required_capabilities,missing_parameters:event.missing_parameters};const old=metadata.steps||[];const steps=!isTimelineEvent?old:old.some(item=>item.id===step.id)?old.map(item=>item.id===step.id?{...item,...step}:item):[...old,step];return {...message,text:event.final&&event.status!=="failed"?(event.message||"Completed successfully"):message.text,metadata:{...metadata,steps}}}));
    if(event.final){setLoading(false);setActiveExecution(current=>current?{...current,status:event.status==="failed"?"FAILED":event.status==="cancelled"?"CANCELLED":"COMPLETED",continuation:null}:current);void reconcileRuntime(execution.execution_id,assistantId);runtimeRef.current?.();runtimeRef.current=null;executionRef.current=null;}
  }

  async function reconcileRuntime(executionId,assistantId){
    try{const authoritative=await getRuntime(executionId);setActiveExecution(current=>current?{...current,...authoritative,continuation:null}:current);setMessages(current=>current.map(message=>message.id===assistantId?{...message,text:authoritative.status==="COMPLETED"?(authoritative.result_message||message.text):message.text,metadata:{...message.metadata,status:authoritative.status,duration_ms:authoritative.duration_ms,error:authoritative.error,provider:authoritative.provider,model:authoritative.model}}:message));}
    catch(error){console.error("Unable to reconcile authoritative runtime state",error);}
  }

  function loadMessages(data) {
    const normalized=(data || []).map(message=>({...message,text:message.text??message.content,timestamp:message.timestamp??(message.created_at?new Date(message.created_at).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"}):undefined)}));
    setMessages(normalized);
    setResponseId([...(data || [])].reverse().find((message) => message.role === "assistant")?.response_id ?? null);
    return normalized;
  }

  async function handleStream(userMessage, options={}) {
    if (!userMessage?.trim() || loading) return;
    let assistantId = null;
    lastRequestRef.current={message:userMessage,options};
    try {
      runtimeRef.current?.();
      const conversationId = await conversation.ensureConversation();
      const active = conversation.conversations.find((item) => item.id === conversationId);
      if (active?.title === "New Conversation") {
        await updateConversationTitle(conversationId, createConversationTitle(userMessage));
        await conversation.refreshConversations();
      }

      assistantId = crypto.randomUUID();
      setMessages((current) => [...current,
        { id: crypto.randomUUID(), role: "user", text: userMessage, timestamp: timestamp() },
        { id: assistantId, role: "assistant", text: "", timestamp: timestamp(), metadata: { status: "RUNNING", steps: [] } },
      ]);
      setLoading(true);
      const execution = await startExecution({ message: userMessage, conversation_id: conversationId, agent_id: options.agentId||null, provider:options.provider||null, model:options.model||null, workspace_id:options.workspace||null });
      setResponseId(execution.execution_id);
      setActiveExecution({...execution,agent_id:options.agentId||null,assistant_id:assistantId});
      dispatchRuntime({type:"started",executionId:execution.execution_id,workflowId:execution.workflow_id});
      connectRuntime(assistantId, execution);
    } catch (error) {
      console.error("Unable to start runtime execution", error);
      if (assistantId) {
        failExecution(
          assistantId,
          error instanceof Error ? error.message : "Unable to start runtime execution",
        );
      }
      setLoading(false);
    }
  }

  function statusMessage(status){
    const normalized=String(status||"").toLowerCase();
    if(normalized.startsWith("waiting_for_"))return `Execution paused: ${normalized.replaceAll("_"," ")}.`;
    if(normalized==="failed")return "Execution failed. Review the runtime error for details.";
    if(normalized==="cancelled")return "Execution cancelled.";
    if(normalized==="timed_out")return "Execution timed out.";
    return normalized==="completed"?"Execution completed.":"Execution is running.";
  }

  async function resumeAgentExecution(values){
    if(!activeExecution?.continuation)return;
    setLoading(true);
    try{
      const next=await continueRuntime(activeExecution.execution_id,activeExecution.continuation.continuation_id,values);
      const resumed={...next,agent_id:activeExecution.agent_id,assistant_id:activeExecution.assistant_id,continuation:null};
      setActiveExecution(resumed);
      setMessages(current=>current.map(message=>message.id===activeExecution.assistant_id?{...message,text:next.result?.message||statusMessage(next.status),metadata:{...message.metadata,status:next.status.toUpperCase(),continuation:next.continuation}}:message));
      dispatchRuntime({type:"started",executionId:next.execution_id,workflowId:next.workflow_id});
      connectRuntime(activeExecution.assistant_id, resumed);
    }catch(error){setLoading(false);throw error;}
  }

  async function decideApproval(decision){
    const continuation=activeExecution?.continuation;if(!continuation)return;
    const fn=decision==="approve"?approveRuntime:denyRuntime;
    const next=await fn(activeExecution.execution_id,continuation.continuation_id);
    const resumed={...activeExecution,...next,continuation:null};
    setActiveExecution(resumed);
    if(decision==="approve"){
      setLoading(true);
      dispatchRuntime({type:"started",executionId:next.execution_id,workflowId:next.workflow_id||activeExecution.workflow_id});
      connectRuntime(activeExecution.assistant_id, resumed);
    }else{
      setLoading(false);
    }
  }

  function failExecution(assistantId, description) {
    setMessages((current) => current.map((message) => message.id === assistantId ? {
      ...message,
      text: "Enterprise AI Runtime failed.",
      metadata: { ...message.metadata, status: "FAILED", steps: [...(message.metadata?.steps || []), { id: "runtime-error", name: "Runtime Execution", description, status: "failed", timestamp: new Date().toISOString() }] },
    } : message));
    setLoading(false);
  }

  function stopGeneration() {
    const executionId = executionRef.current;
    runtimeRef.current?.();
    runtimeRef.current = null;
    executionRef.current = null;
    if (executionId) {
      void cancelRuntime(executionId).catch((error) => console.error("Runtime cancellation failed", error));
    }
    setMessages((current) => current.map((message) => message.metadata?.status === "RUNNING" ? {
      ...message,
      metadata: { ...message.metadata, status: "CANCELLED" },
    } : message));
    setLoading(false);
  }

  function clearChat() { setMessages([]); setResponseId(null); setLoading(false);dispatchRuntime({type:"reset"});setActiveExecution(null); }
  function retryExecution(){const request=lastRequestRef.current;if(request&&!loading)return handleStream(request.message,request.options);}
  async function restoreRuntime(conversationId,assistantId){
    const execution=await getConversationRuntime(conversationId);if(!execution)return;
    const restoredAssistantId=assistantId||crypto.randomUUID();
    if(!assistantId)setMessages(current=>[...current,{id:restoredAssistantId,role:"assistant",text:"",timestamp:timestamp(),metadata:{status:execution.status?.toUpperCase()||"RUNNING",execution_id:execution.execution_id,workflow_id:execution.workflow_id,steps:[]}}]);
    executionRef.current=execution.execution_id;setActiveExecution({...execution,assistant_id:restoredAssistantId});dispatchRuntime({type:"started",executionId:execution.execution_id,workflowId:execution.workflow_id});runtimeRef.current?.();runtimeRef.current=subscribeRuntime(execution.execution_id,event=>applyEvent(restoredAssistantId,execution,event),error=>failExecution(restoredAssistantId,error.message));
  }
  useEffect(() => () => runtimeRef.current?.(), []);
  return { messages, loading, responseId, activeExecution, runtime, loadMessages, clearChat, restoreRuntime, handleStream, handleSend: handleStream, retryExecution, resumeAgentExecution, decideApproval, stopGeneration };
}
