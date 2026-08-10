import { getAccessToken } from "./auth";

import type { RuntimeEvent } from "../types/runtime";

export type RuntimeSubscription = () => void;

export async function cancelRuntime(executionId: string): Promise<void> {
  const token = await getAccessToken();
  const baseUrl = import.meta.env.VITE_API_URL || "";
  const response = await fetch(`${baseUrl}/api/runtime/cancel/${executionId}`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) throw new Error(`Runtime cancellation failed (${response.status})`);
}

async function postContinuation(executionId:string, route:string, continuationId:string, values:Record<string,unknown>={}) {
  const token=await getAccessToken(); const baseUrl=import.meta.env.VITE_API_URL || "";
  const response=await fetch(`${baseUrl}/api/runtime/${executionId}/${route}`,{method:"POST",headers:{"Content-Type":"application/json",...(token?{Authorization:`Bearer ${token}`}:{})},body:JSON.stringify({continuation_id:continuationId,values})});
  if(!response.ok){const body=await response.json().catch(()=>({}));throw new Error(body.detail || `Runtime ${route} failed (${response.status})`)}
  return response.json();
}
export const continueRuntime=(executionId:string,continuationId:string,values:Record<string,unknown>)=>postContinuation(executionId,"continue",continuationId,values);
export const approveRuntime=(executionId:string,continuationId:string)=>postContinuation(executionId,"approve",continuationId);
export const denyRuntime=(executionId:string,continuationId:string)=>postContinuation(executionId,"deny",continuationId);
export async function getRuntime(executionId:string){const token=await getAccessToken();const response=await fetch(`${import.meta.env.VITE_API_URL || ""}/api/runtime/${executionId}`,{headers:token?{Authorization:`Bearer ${token}`}:{}});if(!response.ok)throw new Error(`Runtime fetch failed (${response.status})`);return response.json()}
export async function getConversationRuntime(conversationId:string){const token=await getAccessToken();const response=await fetch(`${import.meta.env.VITE_API_URL || ""}/api/runtime?conversation_id=${encodeURIComponent(conversationId)}`,{headers:token?{Authorization:`Bearer ${token}`}:{}});if(response.status===404)return null;if(!response.ok)throw new Error(`Runtime fetch failed (${response.status})`);return response.json()}

/**
 * SSE is read with fetch so Cognito's Authorization header is retained.
 * The returned unsubscribe function aborts the request immediately.
 */
export function subscribeRuntime(
  executionId: string,
  callback: (event: RuntimeEvent) => void,
  onError?: (error: Error) => void,
): RuntimeSubscription {
  const controller = new AbortController();
  const baseUrl = import.meta.env.VITE_API_URL || "";
  let lastContinuationId: string | null = null;
  let terminal = false;

  void (async () => {
    while (!controller.signal.aborted && !terminal) {
      try {
        const authoritative = await getRuntime(executionId);
        const continuation = authoritative.continuation;
        if (
          continuation?.continuation_id &&
          continuation.continuation_id !== lastContinuationId &&
          (authoritative.status === "WAITING_FOR_INPUT" ||
            authoritative.status === "WAITING_FOR_APPROVAL")
        ) {
          lastContinuationId = continuation.continuation_id;
          callback({
            ...continuation,
            type:
              authoritative.status === "WAITING_FOR_APPROVAL"
                ? "approval_required"
                : "required_input",
            execution_id: executionId,
            workflow_id: authoritative.workflow_id,
            status: "waiting",
            final: false,
          } as RuntimeEvent);
        } else if (["COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"].includes(authoritative.status)) {
          terminal = true;
          callback({
            type: authoritative.status === "FAILED" ? "error" : "completed",
            execution_id: executionId,
            workflow_id: authoritative.workflow_id,
            status: authoritative.status.toLowerCase(),
            message: authoritative.result_message,
            error: authoritative.error,
            duration_ms: authoritative.duration_ms,
            final: true,
          } as RuntimeEvent);
          controller.abort();
          return;
        }
      } catch {
        // The authenticated SSE path remains primary; polling is a resilience fallback.
      }
      await new Promise((resolve) => window.setTimeout(resolve, 2000));
    }
  })();

  void (async () => {
    let attempts=0;
    while(!controller.signal.aborted&&!terminal&&attempts<4){try {
      const token = await getAccessToken();
      const response = await fetch(`${baseUrl}/api/runtime/events/${executionId}`, {
        headers: {
          Accept: "text/event-stream",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        signal: controller.signal,
      });
      if (!response.ok || !response.body) {
        throw new Error(`Runtime stream failed (${response.status})`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (!controller.signal.aborted) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const frames = buffer.split("\n\n");
        buffer = frames.pop() ?? "";
        for (const frame of frames) {
          const data = frame.split("\n").find((line) => line.startsWith("data:"));
          if (!data) continue;
          const event=JSON.parse(data.slice(5).trim()) as RuntimeEvent;
          callback(event);terminal=Boolean(event.final);
        }
      }
      if(!terminal&&!controller.signal.aborted)throw new Error("Runtime stream disconnected");
    } catch (error) {
      attempts+=1;
      if (!controller.signal.aborted&&attempts>=4) {
        onError?.(error instanceof Error ? error : new Error("Runtime stream failed"));
      }else if(!controller.signal.aborted){
        await new Promise(resolve=>window.setTimeout(resolve,Math.min(1000*attempts,3000)));
      }
    }}
  })();

  return () => controller.abort();
}
