import api from "./api";

export const listIntegrations=(params={})=>api.get("/api/integrations",{params}).then(({data})=>data);
export const getIntegration=(id:string)=>api.get(`/api/integrations/${id}`).then(({data})=>data);
export const getConnectorCatalog=()=>api.get("/api/integrations/catalog").then(({data})=>data);
export const createIntegration=(payload:Record<string,unknown>)=>api.post("/api/integrations",payload).then(({data})=>data);
export const updateIntegration=(id:string,payload:Record<string,unknown>)=>api.patch(`/api/integrations/${id}`,payload).then(({data})=>data);
export const disableIntegration=(id:string)=>api.delete(`/api/integrations/${id}`).then(({data})=>data);
export const testIntegration=(id:string)=>api.post(`/api/integrations/${id}/test`).then(({data})=>data);
export const discoverCapabilities=(id:string)=>api.post(`/api/integrations/${id}/discover`).then(({data})=>data);
export const getCapabilities=(id:string)=>api.get(`/api/integrations/${id}/capabilities`).then(({data})=>data);
export const updateCapability=(id:string,name:string,payload:Record<string,unknown>)=>api.patch(`/api/integrations/${id}/capabilities/${encodeURIComponent(name)}`,payload).then(({data})=>data);
export const getIntegrationAgents=(id:string)=>api.get(`/api/integrations/${id}/agents`).then(({data})=>data);
export const assignIntegrationAgent=(id:string,agentId:number,capability_names:string[])=>api.post(`/api/integrations/${id}/agents/${agentId}`,{capability_names}).then(({data})=>data);
export const removeIntegrationAgent=(id:string,agentId:number)=>api.delete(`/api/integrations/${id}/agents/${agentId}`).then(({data})=>data);
export const getIntegrationUsage=(id:string)=>api.get(`/api/integrations/${id}/usage`).then(({data})=>data);
