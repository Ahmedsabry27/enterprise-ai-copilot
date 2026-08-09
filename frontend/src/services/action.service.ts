import api from "./api";
export const getActions=()=>api.get("/api/actions").then(r=>r.data);
export const createAction=(x:unknown)=>api.post("/api/actions",x).then(r=>r.data);
export const updateAction=(id:string|number,x:unknown)=>api.patch(`/api/actions/${id}`,x).then(r=>r.data);
export const executeAction=(id:string|number)=>api.post(`/api/actions/${id}/execute`).then(r=>r.data);
