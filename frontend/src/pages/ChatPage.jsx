import { useEffect } from "react";

import ChatWindow from "../components/chat/ChatWindow";
import ChatInput from "../components/chat/ChatInput";

import useConversation from "../hooks/useConversation";
import useChat from "../hooks/useChat";


export default function ChatPage() {


  const conversation =
    useConversation();


  const chat =
    useChat(conversation);



  // ---------------------------------------
  // Load selected conversation
  // ---------------------------------------

  useEffect(() => {

    async function loadConversation() {

      if (!conversation.selectedConversation) {
        return;
      }


      const messages =
        await conversation.openConversation(
          conversation.selectedConversation
        );


      chat.loadMessages(messages);

    }


    loadConversation();


  }, [
    conversation.selectedConversation
  ]);





  // ---------------------------------------
  // Send message
  // ---------------------------------------

  async function handleSend(message) {

    await chat.handleStream(message);

  }





  // ---------------------------------------
  // New chat
  // ---------------------------------------

  function handleNewChat() {

    conversation.newChat();

    chat.clearChat();

  }





  return (

    <div
      className="
        flex
        h-full
        flex-col
        overflow-hidden
      "
    >


      {/* Chat Workspace */}

      <section
        className="
          flex
          flex-1
          flex-col
          overflow-hidden
        "
      >


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




        <ChatInput

          onSend={
            handleSend
          }


          onStop={
            chat.stopGeneration
          }


          loading={
            chat.loading
          }

        />


      </section>


    </div>

  );

}