import { useEffect, useRef, useState } from "react";

import { updateConversationTitle } from "../api/conversationApi";
import { startExecution } from "../services/chat.service";
import { cancelRuntime, subscribeRuntime } from "../services/runtime.service";
import createConversationTitle from "../utils/createConversationTitle";

const timestamp = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

// The card renders supplied metadata only. These initial states let the user see
// the planned lifecycle immediately, before the first SSE frame arrives.
const initialRuntimeSteps = () => [
  { id: "Request Received", name: "Request Received", description: "User prompt received", status: "completed", timestamp: new Date().toISOString() },
  { id: "Conversation API", name: "Conversation API", description: "Loading conversation context", status: "running", timestamp: new Date().toISOString() },
  { id: "Planner", name: "Planner", description: "Waiting to create execution plan", status: "pending" },
  { id: "Agent Execution", name: "Agent Execution", description: "Waiting for agent selection", status: "pending" },
  { id: "Generate Report Action", name: "Generate Report Action", description: "Waiting to execute enterprise action", status: "pending" },
  { id: "Result Generated", name: "Result Generated", description: "Waiting for final response", status: "pending" },
];

export default function useChat(conversation) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [responseId, setResponseId] = useState(null);
  const runtimeRef = useRef(null);
  const executionRef = useRef(null);

  function loadMessages(data) {
    setMessages(data || []);
    setResponseId([...(data || [])].reverse().find((message) => message.role === "assistant")?.response_id ?? null);
  }

  async function handleStream(userMessage) {
    if (!userMessage?.trim() || loading) return;
    let assistantId = null;
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
        { id: assistantId, role: "assistant", text: "", timestamp: timestamp(), metadata: { status: "RUNNING", steps: initialRuntimeSteps() } },
      ]);
      setLoading(true);
      const execution = await startExecution({ message: userMessage, conversation_id: conversationId });
      setResponseId(execution.execution_id);
      executionRef.current = execution.execution_id;
      runtimeRef.current = subscribeRuntime(execution.execution_id, (event) => {
        setMessages((current) => current.map((message) => {
          if (message.id !== assistantId) return message;
          const metadata = {
            ...message.metadata,
            execution_id: execution.execution_id,
            workflow_id: execution.workflow_id,
            status: event.final
              ? event.status === "failed"
                ? "FAILED"
                : event.status === "cancelled"
                  ? "CANCELLED"
                  : "COMPLETED"
              : "RUNNING",
            agent: event.agent ?? message.metadata?.agent,
            duration_ms: event.duration_ms ?? message.metadata?.duration_ms,
          };
          const step = { id: event.name, name: event.name, description: event.description, status: event.status, timestamp: event.timestamp };
          const oldSteps = metadata.steps || [];
          const steps = oldSteps.some((item) => item.id === step.id)
            ? oldSteps.map((item) => item.id === step.id ? { ...item, ...step } : item)
            : [...oldSteps, step];
          return {
            ...message,
            text: event.final ? (event.message || (event.status === "failed" ? "Enterprise AI Runtime failed." : "Completed successfully")) : message.text,
            metadata: { ...metadata, steps },
          };
        }));
        if (event.final) {
          setLoading(false);
          runtimeRef.current?.();
          runtimeRef.current = null;
          executionRef.current = null;
        }
      }, (error) => failExecution(assistantId, error.message));
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

  function clearChat() { setMessages([]); setResponseId(null); setLoading(false); }
  useEffect(() => () => runtimeRef.current?.(), []);
  return { messages, loading, responseId, loadMessages, clearChat, handleStream, handleSend: handleStream, stopGeneration };
}
