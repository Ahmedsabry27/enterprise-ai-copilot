import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  continueRuntime: vi.fn(),
  startExecution: vi.fn(),
  subscribeRuntime: vi.fn(),
  unsubscribe: vi.fn(),
}));

vi.mock("../api/conversationApi", () => ({
  updateConversationTitle: vi.fn(),
}));

vi.mock("../services/chat.service", () => ({
  startExecution: mocks.startExecution,
}));

vi.mock("../services/runtime.service", () => ({
  approveRuntime: vi.fn(),
  cancelRuntime: vi.fn(),
  continueRuntime: mocks.continueRuntime,
  denyRuntime: vi.fn(),
  getConversationRuntime: vi.fn(),
  getRuntime: vi.fn(),
  subscribeRuntime: mocks.subscribeRuntime,
}));

import useChat from "./useChat";

describe("useChat runtime continuation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.subscribeRuntime.mockReturnValue(mocks.unsubscribe);
    mocks.startExecution.mockResolvedValue({
      execution_id: "execution-1",
      workflow_id: "workflow-1",
      status: "RUNNING",
    });
    mocks.continueRuntime.mockResolvedValue({
      execution_id: "execution-1",
      workflow_id: "workflow-1",
      status: "RUNNING",
    });
  });

  it("reconnects to runtime events after submitting required Jira details", async () => {
    const conversation = {
      conversations: [{ id: "conversation-1", title: "Create a Jira ticket" }],
      ensureConversation: vi.fn().mockResolvedValue("conversation-1"),
      refreshConversations: vi.fn(),
    };
    const { result } = renderHook(() => useChat(conversation));

    await act(() => result.current.handleStream("Create a Jira ticket"));

    const firstEvent = mocks.subscribeRuntime.mock.calls[0][1];
    act(() => firstEvent({
      type: "required_input",
      continuation_id: "continuation-1",
      fields: [{ name: "project_key", required: true }],
      status: "waiting",
    }));

    await act(() => result.current.resumeAgentExecution({ project_key: "OPS" }));

    expect(mocks.continueRuntime).toHaveBeenCalledWith(
      "execution-1",
      "continuation-1",
      { project_key: "OPS" },
    );
    expect(mocks.unsubscribe).toHaveBeenCalled();
    expect(mocks.subscribeRuntime).toHaveBeenCalledTimes(2);
    expect(mocks.subscribeRuntime.mock.calls[1][0]).toBe("execution-1");

    const replayedEvent = mocks.subscribeRuntime.mock.calls[1][1];
    act(() => replayedEvent({
      type: "required_input",
      continuation_id: "continuation-1",
      fields: [{ name: "project_key", required: true }],
      status: "waiting",
    }));

    expect(result.current.activeExecution.continuation).toBeNull();
    expect(result.current.loading).toBe(true);
  });
});
