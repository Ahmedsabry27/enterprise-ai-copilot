import { useEffect } from "react";
import { Box } from "@mui/material";

import MainLayout from "../components/layout/MainLayout";
import ChatWindow from "../components/chat/ChatWindow";
import ChatInput from "../components/chat/ChatInput";

import useConversation from "../hooks/useConversation";
import useChat from "../hooks/useChat";

function ChatPage() {

  // --------------------------------------------------
  // Hooks
  // --------------------------------------------------

  const conversation = useConversation();
  const chat = useChat(conversation);

  // --------------------------------------------------
  // Load Selected Conversation
  // --------------------------------------------------

  useEffect(() => {

    async function syncConversation() {

      if (!conversation.selectedConversation) {
        return;
      }

      const messages =
        await conversation.openConversation(
          conversation.selectedConversation
        );

      chat.loadMessages(messages);

    }

    syncConversation();

  }, [conversation.selectedConversation]);

  // --------------------------------------------------
  // Send Message
  // --------------------------------------------------

  async function handleSend(message) {

    await chat.handleStream(message);

  }

  // --------------------------------------------------
  // New Chat
  // --------------------------------------------------

  function handleNewChat() {

    conversation.newChat();

    chat.clearChat();

  }

  // --------------------------------------------------
  // Render
  // --------------------------------------------------

  return (

    <MainLayout

      conversations={
        conversation.conversations
      }

      selectedConversationId={
        conversation.conversationId
      }

      onConversationSelect={
        conversation.selectConversation
      }

      onNewChat={
        handleNewChat
      }

    >

      <Box
        sx={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          minWidth: 0,
          minHeight: 0,
          overflow: "hidden",
          bgcolor: "#F5F7FA",
        }}
      >

        <ChatWindow
          messages={chat.messages}
          loading={chat.loading}
          onPromptClick={handleSend}
        />

        <ChatInput
          onSend={handleSend}
          onStop={chat.stopGeneration}
          loading={chat.loading}
        />

      </Box>

    </MainLayout>

  );

}

export default ChatPage;