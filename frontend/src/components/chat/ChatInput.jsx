import { useState } from "react";
import { Box, Button, TextField } from "@mui/material";

function ChatInput({ onSend }) {
  const [message, setMessage] = useState("");

  const handleSend = () => {
    if (!message.trim()) return;

    onSend(message);
    setMessage("");
  };

  return (
    <Box
      sx={{
        display: "flex",
        gap: 2,
        p: 2,
        borderTop: "1px solid #ddd",
      }}
    >
      <TextField
        fullWidth
        value={message}
        placeholder="Ask your Enterprise AI Copilot..."
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            handleSend();
          }
        }}
      />

      <Button variant="contained" onClick={handleSend}>
        Send
      </Button>
    </Box>
  );
}

export default ChatInput;