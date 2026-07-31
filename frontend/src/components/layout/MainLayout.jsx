import { useState } from "react";

import {
  SidebarProvider,
  SidebarInset,
} from "@/components/ui/sidebar";

import Sidebar from "../sidebar/Sidebar";
import Header from "./Header";

import ChatWindow from "../chat/ChatWindow";
import Composer from "../chat/Composer";

import useConversations from "../../hooks/useConversation";

import {
  getConversationMessages,
} from "../../services/conversationService";


export default function MainLayout() {


  const [
    messages,
    setMessages
  ] = useState([]);


  const [
    loading,
    setLoading
  ] = useState(false);


  const [
    conversationId,
    setConversationId
  ] = useState(null);



  const {
    conversations,
    loading:
      conversationsLoading,
    refreshConversations,

  } = useConversations();




  // ---------------------------------------------
  // New Chat
  // ---------------------------------------------

  function handleNewChat() {

    setMessages([]);

    setConversationId(null);

  }




  // ---------------------------------------------
  // Select Conversation
  // ---------------------------------------------

  async function handleConversationSelect(
    conversation
  ) {

    try {

      setLoading(true);


      const data =
        await getConversationMessages(
          conversation.id
        );


      setConversationId(
        conversation.id
      );


      setMessages(
        data
      );


    } catch(error) {

      console.error(
        "Failed loading conversation",
        error
      );


    } finally {

      setLoading(false);

    }

  }





  return (


    <SidebarProvider
      className="
        h-screen
        overflow-hidden
      "
    >



      <Sidebar

        conversations={
          conversations
        }

        loading={
          conversationsLoading
        }

        onConversationSelect={
          handleConversationSelect
        }

        onNewChat={
          handleNewChat
        }

        conversationId={
          conversationId
        }

      />





      <SidebarInset

        className="
          flex
          h-screen
          min-h-0
          flex-1
          flex-col
          overflow-hidden
        "

      >



        {/* Header */}

        <Header />





        {/* Main Chat Area */}

        <main

          className="
            flex
            min-h-0
            flex-1
            flex-col
            overflow-hidden
          "

        >



          {/* Messages */}

          <div

            className="
              min-h-0
              flex-1
              overflow-hidden
            "

          >

            <ChatWindow

              messages={
                messages
              }

              loading={
                loading
              }

            />

          </div>





          {/* Composer */}

          <div

            className="
              shrink-0
              border-t
              bg-background
            "

          >

            <Composer

              setMessages={
                setMessages
              }

              loading={
                loading
              }

              setLoading={
                setLoading
              }

              conversationId={
                conversationId
              }

              setConversationId={
                setConversationId
              }

              refreshConversations={
                refreshConversations
              }

            />


          </div>




        </main>



      </SidebarInset>


    </SidebarProvider>

  );

}