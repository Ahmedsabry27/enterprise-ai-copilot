import {describe,expect,it} from "vitest";
import {initialRuntimeState,runtimeReducer} from "./runtime.reducer";

describe("runtimeReducer",()=>{
  it("keeps the unified execution identity and merges duplicate events",()=>{
    let state=runtimeReducer(initialRuntimeState,{type:"started",executionId:"runtime-1",workflowId:"workflow-1"});
    const event={type:"step" as const,execution_id:"runtime-1",workflow_id:"workflow-1",name:"Planner",status:"completed" as const,timestamp:"2026-08-08T10:00:00Z"};
    state=runtimeReducer(state,{type:"event",event});
    state=runtimeReducer(state,{type:"event",event});
    expect(state.executionId).toBe("runtime-1");
    expect(state.steps).toHaveLength(1);
  });

  it("pauses for dynamic input and resumes to a terminal response",()=>{
    let state=runtimeReducer({...initialRuntimeState,status:"RUNNING"},{type:"event",event:{type:"required_input",execution_id:"runtime-1",workflow_id:"workflow-1",continuation_id:"continuation-1",fields:[{name:"environment",label:"Environment",type:"select",required:true}],status:"waiting"}});
    expect(state.status).toBe("WAITING_FOR_INPUT");
    expect(state.requiredInput?.continuation_id).toBe("continuation-1");
    state=runtimeReducer(state,{type:"event",event:{type:"completed",execution_id:"runtime-1",workflow_id:"workflow-1",status:"completed",message:"Report delivered",final:true}});
    expect(state.status).toBe("COMPLETED");
    expect(state.finalResponse).toBe("Report delivered");
  });

  it("tracks selected-agent candidates, tools, actions, logs, and metrics",()=>{
    const selected=runtimeReducer(initialRuntimeState,{type:"event",event:{type:"step",execution_id:"runtime-1",workflow_id:"workflow-1",agent:"Deployment Agent",agent_id:"agent-1",provider:"bedrock",model:"amazon.nova-lite-v1:0",confidence:.94,candidates:[]}});
    expect(selected.selectedAgent?.provider).toBe("bedrock");
    const tool=runtimeReducer(selected,{type:"event",event:{type:"tool_completed",execution_id:"runtime-1",workflow_id:"workflow-1",name:"get_deployment_history",status:"completed"}});
    expect(tool.tools).toHaveLength(1);
  });

  it("merges planner status transitions even when timestamps differ",()=>{
    let state=runtimeReducer(initialRuntimeState,{type:"event",event:{type:"step",execution_id:"runtime-1",workflow_id:"workflow-1",step_id:"planner",name:"Planner",status:"running",timestamp:"2026-08-08T10:00:00Z"}});
    state=runtimeReducer(state,{type:"event",event:{type:"step",execution_id:"runtime-1",workflow_id:"workflow-1",step_id:"planner",name:"Planner",status:"completed",timestamp:"2026-08-08T10:00:01Z"}});
    expect(state.steps).toHaveLength(1);
    expect(state.steps[0].status).toBe("completed");
  });

  it("never converts a terminal error into completed or a metric into a workflow step",()=>{
    let state=runtimeReducer(initialRuntimeState,{type:"event",event:{type:"metric",execution_id:"runtime-1",workflow_id:"workflow-1",name:"Provider Metrics",status:"completed",metadata:{duration_ms:12}}});
    expect(state.steps).toHaveLength(0);
    state=runtimeReducer(state,{type:"event",event:{type:"error",execution_id:"runtime-1",workflow_id:"workflow-1",status:"failed",error:"Safe failure",final:true}});
    expect(state.status).toBe("FAILED");
    expect(state.finalResponse).toBeUndefined();
  });
});

it("terminates running tools when a final failure arrives",()=>{
  const started=runtimeReducer(initialRuntimeState,{type:"started",executionId:"runtime-1",workflowId:"workflow-1"});
  const running=runtimeReducer(started,{type:"event",event:{type:"tool_started",execution_id:"runtime-1",workflow_id:"workflow-1",step_id:"tool:jira:metadata",name:"jira.get_create_metadata",status:"running"}});
  const failed=runtimeReducer(running,{type:"event",event:{type:"completed",execution_id:"runtime-1",workflow_id:"workflow-1",name:"Result Generated",status:"failed",description:"Jira request failed",final:true}});
  expect(failed.status).toBe("FAILED");
  expect(failed.tools[0].status).toBe("failed");
  expect(failed.finalResponse).toBeUndefined();
});
