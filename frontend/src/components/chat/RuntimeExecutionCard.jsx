import { AlertCircle, CheckCircle, Clock, Loader2 } from "lucide-react";

const statusStyle = {
  pending: "bg-slate-700/40 border-white/10 text-slate-400",
  running: "bg-blue-500/20 border-blue-400/40 text-blue-300",
  completed: "bg-emerald-400/20 border-emerald-400/40 text-emerald-300",
  failed: "bg-red-500/20 border-red-400/40 text-red-300",
  cancelled: "bg-orange-400/20 border-orange-400/40 text-orange-300",
};

function StepIcon({ status }) {
  if (status === "failed") return <AlertCircle className="h-5 w-5" />;
  if (status === "running") return <Loader2 className="h-5 w-5 animate-spin" />;
  if (status === "completed") return <CheckCircle className="h-5 w-5" />;
  return <Clock className="h-5 w-5" />;
}

export default function RuntimeExecutionCard({ metadata = {} }) {
  const steps = metadata.steps || [];
  const badge = metadata.status === "FAILED"
    ? "border-red-400/30 bg-red-400/10 text-red-300"
    : metadata.status === "CANCELLED"
      ? "border-orange-400/30 bg-orange-400/10 text-orange-300"
    : metadata.status === "RUNNING"
      ? "border-blue-400/30 bg-blue-400/10 text-blue-300"
      : "border-emerald-400/30 bg-emerald-400/10 text-emerald-300";

  return (
    <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-slate-900/80 via-blue-950/70 to-purple-950/60 p-6 shadow-2xl backdrop-blur-xl">
      <div className="mb-8 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 text-xl">🤖</div>
          <div>
            <h2 className="text-lg font-semibold text-white">AI Runtime Orchestrator</h2>
            <p className="text-xs text-slate-400">Live execution trace</p>
          </div>
        </div>
        <span className={`rounded-full border px-4 py-2 text-xs font-medium ${badge}`}>● {metadata.status || "RUNNING"}</span>
      </div>

      {steps.length === 0 ? (
        <p className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-400">Waiting for runtime events…</p>
      ) : (
        <div className="space-y-2">
          {steps.map((step, index) => (
            <div key={step.id || `${step.name}-${index}`} className="relative flex gap-4 pb-5">
              {index !== steps.length - 1 && <div className="absolute left-5 top-10 h-full w-px bg-white/10" />}
              <div className={`relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full border ${statusStyle[step.status] || statusStyle.pending}`}>
                <StepIcon status={step.status} />
              </div>
              <div className="flex-1 rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-medium text-white">{step.name}</p>
                  <span className="text-[10px] uppercase tracking-wide text-slate-400">{step.status}</span>
                </div>
                <p className="mt-1 text-sm text-slate-400">{step.description}</p>
                {(step.intent||step.extracted_parameters)&&<details className="mt-2 text-xs text-slate-400"><summary className="cursor-pointer text-violet-300">Structured decision</summary><div className="mt-2 space-y-1 rounded-lg bg-black/20 p-2">{step.intent?.intent&&<p>Intent: {step.intent.intent}</p>}{Object.entries(step.extracted_parameters||{}).map(([key,item])=><p key={key}>{key.replaceAll("_"," ")}: {String(item.value)} <span className="text-slate-600">({item.source})</span></p>)}{step.missing_parameters?.length>0&&<p>Missing: {step.missing_parameters.join(", ")}</p>}{step.required_capabilities?.length>0&&<p>Capabilities: {step.required_capabilities.join(", ")}</p>}</div></details>}
                {step.timestamp && <p className="mt-2 text-[11px] text-slate-500">{new Date(step.timestamp).toLocaleTimeString()}</p>}
              </div>
            </div>
          ))}
        </div>
      )}

      {(metadata.agent || metadata.duration_ms != null || metadata.workflow_id) && (
        <div className="mt-4 grid gap-3 border-t border-white/10 pt-4 text-sm sm:grid-cols-3">
          <div className="rounded-xl bg-black/10 p-3"><p className="text-xs text-slate-500">Agent</p><p className="mt-1 truncate text-slate-200">{metadata.agent || "Selecting agent…"}</p></div>
          <div className="rounded-xl bg-black/10 p-3"><p className="text-xs text-slate-500">Duration</p><p className="mt-1 text-slate-200">{metadata.duration_ms == null ? (["FAILED","COMPLETED","CANCELLED","TIMED_OUT"].includes(metadata.status)?"Unavailable":"In progress") : `${Math.max(1,Math.round(metadata.duration_ms))} ms`}</p></div>
          <div className="rounded-xl bg-black/10 p-3"><p className="text-xs text-slate-500">Workflow ID</p><p className="mt-1 truncate text-slate-200" title={metadata.workflow_id}>{metadata.workflow_id}</p></div>
        </div>
      )}
      {metadata.agent && <div className="mt-4 rounded-2xl border border-violet-400/20 bg-violet-500/10 p-4"><div className="flex items-start justify-between gap-3"><div><p className="text-xs uppercase tracking-wide text-violet-300">Selected agent</p><p className="mt-1 font-semibold">{metadata.agent}</p><p className="mt-1 text-xs text-slate-400">{metadata.provider || "Configured provider"} · {metadata.model || "Published model"}</p></div>{metadata.confidence!=null&&<span className="rounded-full bg-emerald-400/10 px-3 py-1 text-xs text-emerald-300">{Math.round(metadata.confidence*100)}% match</span>}</div>{metadata.candidates?.length>1&&<details className="mt-3 text-sm"><summary className="cursor-pointer text-slate-300">Other candidates ({metadata.candidates.length-1})</summary><div className="mt-2 space-y-2">{metadata.candidates.slice(1).map(candidate=><div key={candidate.agent_id} className="flex justify-between rounded-lg bg-black/10 p-2"><span>{candidate.name}<small className="ml-2 text-slate-500">{candidate.reason}</small></span><span>{Math.round(candidate.confidence*100)}%</span></div>)}</div></details>}</div>}
      {metadata.status==="FAILED"&&<div className="mt-4 rounded-xl border border-rose-400/20 bg-rose-400/10 p-3 text-sm text-rose-200"><p>{metadata.error||"The runtime failed safely."}</p><p className="mt-1 text-xs text-slate-500">Support reference: {metadata.execution_id}</p></div>}
    </div>
  );
}
