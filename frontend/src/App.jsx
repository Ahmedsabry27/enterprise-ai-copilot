import { useState } from "react";
import { Box } from "@mui/material";

import Header from "./components/layout/Header";
import ChatWindow from "./components/chat/ChatWindow";
import ChatInput from "./components/chat/ChatInput";

import { sendMessage } from "./api/chatApi";

function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const getTimestamp = () =>
    new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

  async function handleSend(userMessage) {
    if (!userMessage.trim()) return;

    const newUserMessage = {
      id: crypto.randomUUID(),
      role: "user",
      text: userMessage,
      timestamp: getTimestamp(),
    };

    setMessages((prev) => [...prev, newUserMessage]);

    setLoading(true);

    try {
      const result = await sendMessage(userMessage);

      const assistantMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        text: result.response,
        timestamp: getTimestamp(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error(error);

      const errorMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        text: "❌ Unable to contact the AI service.",
        timestamp: getTimestamp(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Box
      sx={{
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        bgcolor: "#F5F7FA",
      }}
    >
      <Header />

      <ChatWindow
        messages={messages}
        loading={loading}
        onPromptClick={handleSend}
      />

      <ChatInput
        onSend={handleSend}
      />
    </Box>
  );
}

export default App;