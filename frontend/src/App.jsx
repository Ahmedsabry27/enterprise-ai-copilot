import { useState } from "react";
import { Box } from "@mui/material";

import Header from "./components/layout/Header";
import ChatWindow from "./components/chat/ChatWindow";
import ChatInput from "./components/chat/ChatInput";

import { sendMessage } from "./api/chatApi";

function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  // Returns current time like 10:45 AM
  const getTimestamp = () =>
    new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

  async function handleSend(userMessage) {
    if (!userMessage.trim()) return;

    // User message
    const newUserMessage = {
      role: "user",
      text: userMessage,
      timestamp: getTimestamp(),
    };

    setMessages((prev) => [...prev, newUserMessage]);

    setLoading(true);

    try {
      const result = await sendMessage(userMessage);

      // AI response
      const assistantMessage = {
        role: "assistant",
        text: result.response,
        timestamp: getTimestamp(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error(error);

      const errorMessage = {
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
      />

      <ChatInput
        onSend={handleSend}
      />
    </Box>
  );
}

export default App;