import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createAgent, deleteAgent, getAgent, getAgentExecutions, getAgents, updateAgent } from "../services/agentService";
export function useAgents(){const qc=useQueryClient(), key=["agents"]; const refresh=()=>qc.invalidateQueries({queryKey:key}); return {query:useQuery({queryKey:key,queryFn:getAgents}),create:useMutation({mutationFn:createAgent,onSuccess:refresh}),update:useMutation({mutationFn:({id,payload})=>updateAgent(id,payload),onSuccess:refresh}),remove:useMutation({mutationFn:deleteAgent,onSuccess:refresh})};}
export const useAgent=(id)=>useQuery({queryKey:["agents",id],queryFn:()=>getAgent(id),enabled:Boolean(id)});
export const useAgentExecutions=(id)=>useQuery({queryKey:["agents",id,"executions"],queryFn:()=>getAgentExecutions(id),enabled:Boolean(id),refetchInterval:15_000});
