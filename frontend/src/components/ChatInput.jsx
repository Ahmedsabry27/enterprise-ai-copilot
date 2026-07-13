import { Box, TextField, Button } from "@mui/material";

function ChatInput() {
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
        placeholder="Ask your Enterprise AI Copilot..."
      />

      <Button variant="contained">
        Send
      </Button>
    </Box>
  );
}

export default ChatInput;