import { useRef, useState } from "react";

import { streamMessage } from "../api/chatApi";

import {
  updateConversationTitle,
} from "../api/conversationApi";

import createConversationTitle from "../utils/createConversationTitle";

export default function useChat(conversation) {

  // --------------------------------------------------
  // State
  // --------------------------------------------------

  const [messages, setMessages] =
    useState([]);

  const [loading, setLoading] =
    useState(false);

  const [responseId, setResponseId] =
    useState(null);

  const controllerRef =
    useRef(null);

  // --------------------------------------------------
  // Helpers
  // --------------------------------------------------

  const getTimestamp = () =>
    new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

  // --------------------------------------------------
  // Load Existing Messages
  // --------------------------------------------------

  function loadMessages(existingMessages) {

    setMessages(existingMessages);

    const lastAssistant =
      [...existingMessages]
        .reverse()
        .find(
          message =>
            message.role === "assistant"
        );

    if (lastAssistant?.response_id) {

      setResponseId(
        lastAssistant.response_id
      );

    } else {

      setResponseId(null);

    }

  }

  // --------------------------------------------------
  // Stream Message
  // --------------------------------------------------

  async function handleStream(
    userMessage
  ) {

    if (!userMessage.trim()) {
      return;
    }

    // ---------------------------------------------
    // Ensure Conversation Exists
    // ---------------------------------------------

    const id =
      await conversation.ensureConversation();

    // ---------------------------------------------
    // Rename Conversation
    // (Only the first time)
    // ---------------------------------------------

    const currentConversation =
      conversation.conversations.find(
        c => c.id === id
      );

    if (
      currentConversation &&
      currentConversation.title ===
        "New Conversation"
    ) {

      try {

        const title =
          createConversationTitle(
            userMessage
          );

        await updateConversationTitle(
          id,
          title
        );

        await conversation.loadConversations();

      } catch (error) {

        console.error(
          "Failed to update conversation title",
          error
        );

      }

    }

    // ---------------------------------------------
    // Streaming
    // ---------------------------------------------

    const controller =
      new AbortController();

    controllerRef.current =
      controller;

    const user = {

      id: crypto.randomUUID(),

      role: "user",

      text: userMessage,

      timestamp: getTimestamp(),

    };

    const assistantId =
      crypto.randomUUID();

    const assistant = {

      id: assistantId,

      role: "assistant",

      text: "",

      timestamp: getTimestamp(),

      isStreaming: true,

    };

    setMessages(prev => [
      ...prev,
      user,
      assistant,
    ]);

    setLoading(true);

    try {

      await streamMessage({

        message: userMessage,

        conversationId: id,

        previousResponseId:
          responseId,

        signal:
          controller.signal,

        onStart() {

          console.log(
            "Streaming started"
          );

        },

        onDelta(chunk) {

          setMessages(prev =>
            prev.map(message =>
              message.id === assistantId
                ? {
                    ...message,
                    text:
                      message.text +
                      chunk,
                  }
                : message
            )
          );

        },

        async onCompleted(
          newResponseId
        ) {

          if (newResponseId) {

            setResponseId(
              newResponseId
            );

          }

          setMessages(prev =>
            prev.map(message =>
              message.id === assistantId
                ? {
                    ...message,
                    isStreaming: false,
                  }
                : message
            )
          );

          await conversation.loadConversations();

        },

        onError(errorMessage) {

          setMessages(prev =>
            prev.map(message =>
              message.id === assistantId
                ? {
                    ...message,

                    text:
                      "❌ " +
                      (
                        errorMessage ||
                        "Streaming failed."
                      ),

                    isStreaming: false,

                  }
                : message
            )
          );

        },

      });

    } catch (error) {

      console.error(error);

      setMessages(prev =>
        prev.map(message =>
          message.id === assistantId
            ? {
                ...message,

                text:
                  "❌ Unable to contact the AI service.",

                isStreaming: false,

              }
            : message
        )
      );

    } finally {

      controllerRef.current =
        null;

      setLoading(false);

    }

  }

  // --------------------------------------------------
  // Wrapper
  // --------------------------------------------------

  async function handleSend(
    userMessage
  ) {

    await handleStream(
      userMessage
    );

  }

  // --------------------------------------------------
  // Stop Generation
  // --------------------------------------------------

  function stopGeneration() {

    controllerRef.current?.abort();

  }

  // --------------------------------------------------
  // Return
  // --------------------------------------------------

  return {

  messages,

  loading,

  loadMessages,

  clearChat,

  handleSend,

  handleStream,

  stopGeneration,

};

}
// --------------------------------------------------
// Clear Chat
// --------------------------------------------------

function clearChat() {

  setMessages([]);

  setResponseId(null);

  setLoading(false);

}