import api from "./api";

export interface StartExecutionRequest {
  message: string;
  conversation_id: string;
}

export interface StartExecutionResponse {
  execution_id: string;
  workflow_id: string;
  status: "RUNNING";
}

export async function startExecution(
  payload: StartExecutionRequest,
): Promise<StartExecutionResponse> {
  const response = await api.post<StartExecutionResponse>("/api/chat/start", payload);
  return response.data;
}
