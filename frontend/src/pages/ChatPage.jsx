import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getAuthorizedAgents } from "../services/agentService";

import ChatWindow from "../components/chat/ChatWindow";
import ChatInput from "../components/chat/ChatInput";
import ExecutionInspector from "../components/chat/ExecutionInspector";
import RequiredInformationCard from "../components/chat/RequiredInformationCard";
import ConversationSidebar from "../components/chat/ConversationSidebar";
import ChatHeader from "../components/chat/ChatHeader";

import useConversation from "../hooks/useConversation";
import useChat from "../hooks/useChat";


export default function ChatPage() {


  const conversation =
    useConversation();


  const chat =
    useChat(conversation);
  const {data:agents=[]}=useQuery({queryKey:["authorized-agents"],queryFn:getAuthorizedAgents});
  const [agentId,setAgentId]=useState("");
  const [provider,setProvider]=useState("automatic");
  const [model,setModel]=useState("automatic");
  const [workspace,setWorkspace]=useState("Finance Operations");

  const conversationRef = useRef(conversation);
  const chatRef = useRef(chat);

  useEffect(() => {
    conversationRef.current = conversation;
    chatRef.current = chat;
  });



  // ---------------------------------------
  // Load selected conversation
  // ---------------------------------------

  useEffect(() => {

    async function loadConversation() {

      if (!conversationRef.current.selectedConversation) {
        return;
      }


      const messages =
        await conversationRef.current.openConversation(
          conversationRef.current.selectedConversation
            .id
        );


      const normalized=chatRef.current.loadMessages(messages);
      const assistant=[...normalized].reverse().find(item=>item.role==="assistant");
      await chatRef.current.restoreRuntime(conversationRef.current.selectedConversation.id,assistant?.id);

    }


    loadConversation();


  }, [
    conversation.selectedConversation
  ]);

  useEffect(()=>{if(!conversation.selectedConversation&&!conversation.conversationId)chatRef.current.clearChat();},[conversation.selectedConversation,conversation.conversationId]);





  // ---------------------------------------
  // Send message
  // ---------------------------------------

  async function handleSend(message) {
    if(chat.activeExecution?.continuation?.kind==="input"){
      await chat.resumeAgentExecution({natural_language:message},"input");
      return;
    }
    await chat.handleStream(message,{agentId,provider:agentId||provider==="automatic"?null:provider,model:agentId||model==="automatic"?null:model,workspace});

  }





  // ---------------------------------------
  // New chat
  // ---------------------------------------

  return (

    <div className="flex h-full overflow-hidden">

      <ConversationSidebar conversation={conversation}/>


      {/* Chat Workspace */}

      <section className="relative flex min-w-0 flex-1 flex-col overflow-hidden">

        <ChatHeader agents={agents} agentId={agentId} setAgentId={setAgentId} provider={provider} setProvider={setProvider} model={model} setModel={setModel} workspace={workspace} setWorkspace={setWorkspace} runtime={chat.runtime}/>


        <ChatWindow

          messages={
            chat.messages
          }


          loading={
            chat.loading
          }


          onPromptClick={
            handleSend
          }

        />




        {chat.activeExecution?.continuation?.kind==="input"&&<div className="border-t border-white/10 p-4"><RequiredInformationCard request={chat.activeExecution.continuation} onSubmit={values=>chat.resumeAgentExecution(values,"input")} onCancel={chat.stopGeneration}/></div>}
        {chat.activeExecution?.continuation?.kind==="approval"&&<div className="border-t border-amber-400/20 bg-amber-400/10 p-4 text-amber-100"><p className="font-medium">Approval required</p><p className="mt-1 text-sm">{chat.activeExecution.continuation.summary||"A governed business action is waiting for an authorized decision."}</p><div className="mt-3 flex gap-2"><button onClick={()=>chat.decideApproval("approve")} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm">Approve</button><button onClick={()=>chat.decideApproval("deny")} className="rounded-lg border border-rose-400/30 px-4 py-2 text-sm text-rose-200">Deny</button></div></div>}
        {chat.activeExecution?.continuation?.kind==="clarification"&&<div className="flex gap-2 border-t border-white/10 p-4"><span className="text-sm">{chat.activeExecution.continuation.question}</span>{chat.activeExecution.continuation.alternatives.map(choice=><button key={choice.id} onClick={()=>chat.resumeAgentExecution({selected_tool:choice.id},"clarification")} className="rounded-lg bg-violet-600 px-3 py-2">{choice.label}</button>)}</div>}
        {chat.runtime.status==="FAILED"&&<div className="flex items-center justify-between gap-4 border-t border-rose-400/20 bg-rose-400/10 p-4"><div><p className="text-sm font-medium text-rose-200">{chat.runtime.error||"The runtime could not complete this request."}</p><p className="mt-1 text-xs text-slate-500">Execution ID: {chat.runtime.executionId}</p></div><button onClick={chat.retryExecution} className="rounded-lg border border-rose-300/30 px-4 py-2 text-sm text-rose-100">Retry</button></div>}

        <ChatInput onSend={handleSend} onStop={chat.stopGeneration} loading={chat.loading} disabled={Boolean(chat.activeExecution?.continuation)&&chat.activeExecution?.continuation?.kind!=="input"}/>


      </section>

      <ExecutionInspector runtime={chat.runtime}/>


    </div>

  );

}
