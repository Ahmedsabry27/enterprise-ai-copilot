import api from "./api";
export const getKnowledge=(search="")=>api.get("/api/knowledge",{params:{search}}).then(r=>r.data);
export const createKnowledge=x=>api.post("/api/knowledge",x).then(r=>r.data);
export const deleteKnowledge=id=>api.delete(`/api/knowledge/${id}`);
