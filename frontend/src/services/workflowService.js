import api from "./api";
export const getWorkflows=()=>api.get("/api/workflows").then(({data})=>data);
export const createWorkflow=(payload)=>api.post("/api/workflows",payload).then(({data})=>data);
export const executeWorkflow=(id)=>api.post(`/api/workflows/${id}/execute`).then(({data})=>data);
export const deleteWorkflow=(id)=>api.delete(`/api/workflows/${id}`);
export const getWorkflow=(id)=>api.get(`/api/workflows/${id}`).then(({data})=>data);
export const updateWorkflow=(id,payload)=>api.put(`/api/workflows/${id}`,payload).then(({data})=>data);
