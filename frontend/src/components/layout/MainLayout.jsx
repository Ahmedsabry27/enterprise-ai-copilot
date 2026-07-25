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
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);

  // Load conversations for the sidebar
  const {
    conversations,
    loading: conversationsLoading,
    refreshConversations,
  } = useConversations();

  /**
   * Start a new conversation
   */
  function handleNewChat() {
    setMessages([]);
    setConversationId(null);
  }

  /**
   * Load a conversation when the user clicks it
   */
  async function handleConversationSelect(conversation) {
    console.log("🟢 Conversation clicked:", conversation);

    try {
      setLoading(true);

      const data = await getConversationMessages(conversation.id);

      console.log("📨 API Response:", data);

      setConversationId(conversation.id);
      setMessages(data);

      console.log("✅ Messages loaded successfully");
    } catch (error) {
      console.error("❌ Failed to load conversation:", error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <SidebarProvider>
      <Sidebar
        conversations={conversations}
        loading={conversationsLoading}
        onConversationSelect={handleConversationSelect}
        onNewChat={handleNewChat}
        conversationId={conversationId}
      />

      <SidebarInset className="flex h-screen flex-col">
        <Header />

        <main className="flex flex-1 flex-col overflow-hidden">
          <ChatWindow
            messages={messages}
            loading={loading}
          />

          <Composer
            setMessages={setMessages}
            loading={loading}
            setLoading={setLoading}
            conversationId={conversationId}
            setConversationId={setConversationId}
            refreshConversations={refreshConversations}
          />
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}