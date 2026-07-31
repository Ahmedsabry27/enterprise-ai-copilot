import api from "./api";
export const getAgents=()=>api.get("/api/agents").then(({data})=>data);
export const getAgent=(id)=>api.get(`/api/agents/${id}`).then(({data})=>data);
export const getAgentExecutions=(id)=>api.get(`/api/agents/${id}/executions`).then(({data})=>data);
export const createAgent=(payload)=>api.post("/api/agents",payload).then(({data})=>data);
export const updateAgent=(id,payload)=>api.patch(`/api/agents/${id}`,payload).then(({data})=>data);
export const deleteAgent=(id)=>api.delete(`/api/agents/${id}`);
