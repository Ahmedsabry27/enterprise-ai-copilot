import { useEffect, useState } from "react";

import {
  createConversation,
  getConversations,
  getMessages,
} from "../api/conversationApi";

export default function useConversation() {

  // --------------------------------------------------
  // State
  // --------------------------------------------------

  const [conversations, setConversations] =
    useState([]);

  const [
    loadingConversations,
    setLoadingConversations,
  ] = useState(false);

  const [
    conversationId,
    setConversationId,
  ] = useState(null);

  const [
    selectedConversation,
    setSelectedConversation,
  ] = useState(null);

  // --------------------------------------------------
  // Helpers
  // --------------------------------------------------

  function mapMessage(message) {

    return {

      id: message.id,

      role: message.role,

      text: message.content,

      timestamp: new Date(
        message.created_at
      ).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),

      response_id: message.response_id,

      isStreaming: false,

    };

  }

  // --------------------------------------------------
  // Load Conversations
  // --------------------------------------------------

  async function loadConversations() {

    try {

      setLoadingConversations(true);

      const data =
        await getConversations();

      setConversations(data);

    } catch (err) {

      console.error(
        "Failed to load conversations",
        err
      );

    } finally {

      setLoadingConversations(false);

    }

  }

  // --------------------------------------------------
  // Select Conversation
  // --------------------------------------------------

  function selectConversation(
    conversation
  ) {

    setConversationId(
      conversation.id
    );

    setSelectedConversation(
      conversation
    );

  }

  // --------------------------------------------------
  // Load Conversation Messages
  // --------------------------------------------------

  async function openConversation(
    conversation
  ) {

    try {

      const data =
        await getMessages(
          conversation.id
        );

      return data.map(
        mapMessage
      );

    } catch (err) {

      console.error(
        "Failed loading messages",
        err
      );

      return [];

    }

  }

  // --------------------------------------------------
  // New Chat
  // --------------------------------------------------

  function newChat() {

  console.log("🔥 NEW CHAT CLICKED");

  setConversationId(null);

  setSelectedConversation(null);

  }

  // --------------------------------------------------
  // Ensure Conversation Exists
  // --------------------------------------------------

  async function ensureConversation() {

    if (conversationId) {

      return conversationId;

    }

    const conversation =
      await createConversation(
        "New Conversation"
      );

    setConversationId(
      conversation.id
    );

    setSelectedConversation(
      conversation
    );

    await loadConversations();

    return conversation.id;

  }

  // --------------------------------------------------
  // Initial Load
  // --------------------------------------------------

  useEffect(() => {

    loadConversations();

  }, []);

  // --------------------------------------------------
  // Return
  // --------------------------------------------------

  return {

    conversations,

    loadingConversations,

    conversationId,

    selectedConversation,

    loadConversations,

    selectConversation,

    openConversation,

    ensureConversation,

    newChat,

  };

}