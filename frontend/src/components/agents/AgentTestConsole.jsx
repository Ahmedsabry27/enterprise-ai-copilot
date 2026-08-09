import { useState } from "react";
import { Play, Square } from "lucide-react";
import { cancelAgentExecution, resumeAgent, testAgent } from "../../services/agentService";

export default function AgentTestConsole({agent}){
  const [prompt,setPrompt]=useState("Generate a deployment report");
  const [result,setResult]=useState(null);
  const [fields,setFields]=useState({});
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");
  const agentId=agent.uuid;
  async function run(){setBusy(true);setError("");try{setResult(await testAgent(agentId,{message:prompt,inputs:{}}));}catch(e){setError(e.response?.data?.detail?.message||"Test execution failed safely.");}finally{setBusy(false);}}
  async function submit(){setBusy(true);try{const c=result.continuation;setResult(await resumeAgent(result.execution_id,c.kind,{resume_token:c.resume_token,response:fields}));}catch(e){setError(e.response?.data?.detail?.message||"Resume failed safely.");}finally{setBusy(false);}}
  async function cancel(){setResult(await cancelAgentExecution(agentId,result.execution_id));}
  const continuation=result?.continuation;
  return <section className="mt-5 rounded-2xl border border-violet-400/30 bg-white/5 p-5" aria-label="Agent Test Console">
    <div className="flex items-center justify-between"><div><h2 className="font-semibold">Test Console</h2><p className="text-sm text-slate-400">Exact published version {agent.published_version||"—"} · persisted test mode</p></div>{result&&!['succeeded','failed','cancelled'].includes(result.status)&&<button onClick={cancel} className="rounded-lg border border-red-400/40 px-3 py-2 text-red-300"><Square size={14}/> Cancel</button>}</div>
    <label className="mt-4 block text-sm">Prompt<textarea className="mt-2 min-h-24 w-full rounded-xl border border-white/10 bg-slate-950/50 p-3" value={prompt} onChange={e=>setPrompt(e.target.value)}/></label>
    <button disabled={busy||!agentId} onClick={run} className="mt-3 inline-flex items-center gap-2 rounded-lg bg-violet-600 px-4 py-2 disabled:opacity-50"><Play size={14}/>{busy?"Running…":"Run test"}</button>
    {error&&<p role="alert" className="mt-3 text-red-300">{error}</p>}
    {result&&<div className="mt-4 rounded-xl bg-slate-950/50 p-4 text-sm"><p><strong>Status:</strong> {result.status}</p><p><strong>Execution:</strong> {result.execution_id}</p><p><strong>Correlation:</strong> {result.correlation_id}</p>{result.result?.message&&<pre className="mt-3 whitespace-pre-wrap">{result.result.message}</pre>}</div>}
    {continuation?.kind==="input"&&<form className="mt-4 space-y-3" onSubmit={e=>{e.preventDefault();submit();}}>{continuation.missing_fields.map(name=><label className="block text-sm" key={name}>{name.replaceAll('_',' ')}<input required className="mt-1 w-full rounded-lg border border-white/10 bg-slate-950/50 p-2" value={fields[name]||""} onChange={e=>setFields({...fields,[name]:e.target.value})}/></label>)}<button className="rounded-lg bg-violet-600 px-4 py-2">Resume execution</button></form>}
    {continuation?.kind==="approval"&&<p className="mt-4 rounded-lg border border-amber-400/30 bg-amber-400/10 p-3 text-amber-200">Approval required. A different authorized approver must review this execution.</p>}
  </section>;
}
