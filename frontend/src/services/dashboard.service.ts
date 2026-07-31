import api from "./api";

export const getDashboardMetrics = () => api.get("/api/dashboard/metrics").then(({ data }) => data);
export const getExecutionTrends = () => api.get("/api/dashboard/executions/trends").then(({ data }) => data);
export const getRecentExecutions = () => api.get("/api/executions/recent").then(({ data }) => data);
export const getAgentStatus = () => api.get("/api/agents/status").then(({ data }) => data);
export const getWorkflowDistribution = () => api.get("/api/dashboard/workflow-distribution").then(({ data }) => data);
