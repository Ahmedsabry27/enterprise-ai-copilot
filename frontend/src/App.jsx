import { useState } from "react";
import { Box } from "@mui/material";

import Header from "./components/layout/Header";
import ChatWindow from "./components/chat/ChatWindow";
import ChatInput from "./components/chat/ChatInput";

import { sendMessage } from "./api/chatApi";

function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  async function handleSend(userMessage) {
    // Add the user's message immediately
    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        text: userMessage,
      },
    ]);

    setLoading(true);

    try {
      const result = await sendMessage(userMessage);

      // Add the AI response
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: result.response,
        },
      ]);
    } catch (error) {
      console.error(error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "Unable to contact the AI service.",
        },
      ]);
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
        backgroundColor: "#f5f5f5",
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