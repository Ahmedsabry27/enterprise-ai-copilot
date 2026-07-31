import { getAccessToken } from "./auth";

export type RuntimeStepStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

export interface RuntimeEvent {
  type: "step" | "completed";
  execution_id: string;
  workflow_id: string;
  name: string;
  description: string;
  status: RuntimeStepStatus;
  timestamp: string;
  agent?: string;
  duration_ms?: number;
  message?: string;
  error?: string;
  final?: boolean;
}

export type RuntimeSubscription = () => void;

export async function cancelRuntime(executionId: string): Promise<void> {
  const token = await getAccessToken();
  const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const response = await fetch(`${baseUrl}/api/runtime/cancel/${executionId}`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) throw new Error(`Runtime cancellation failed (${response.status})`);
}

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
  const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

  void (async () => {
    try {
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
          callback(JSON.parse(data.slice(5).trim()) as RuntimeEvent);
        }
      }
    } catch (error) {
      if (!controller.signal.aborted) {
        onError?.(error instanceof Error ? error : new Error("Runtime stream failed"));
      }
    }
  })();

  return () => controller.abort();
}
