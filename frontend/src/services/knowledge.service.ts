import api from "./api";
export const getKnowledge=(search="")=>api.get("/api/knowledge",{params:{search}}).then(r=>r.data);
export const createKnowledge=(x:unknown)=>api.post("/api/knowledge",x).then(r=>r.data);
export const deleteKnowledge=(id:string|number)=>api.delete(`/api/knowledge/${id}`);
