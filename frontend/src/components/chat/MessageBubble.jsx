import { Box, Paper, Typography } from "@mui/material";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function MessageBubble({ role, text }) {
  const isUser = role === "user";

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        mb: 2,
      }}
    >
      <Paper
        elevation={2}
        sx={{
          maxWidth: "80%",
          p: 2,
          borderRadius: 3,
          backgroundColor: isUser ? "#1976d2" : "#F5F5F5",
          color: isUser ? "white" : "black",
        }}
      >
        <Typography
          variant="subtitle2"
          sx={{ fontWeight: "bold", mb: 1 }}
        >
          {isUser ? "You" : "Enterprise AI Copilot"}
        </Typography>

        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {text}
        </ReactMarkdown>
      </Paper>
    </Box>
  );
}

export default MessageBubble;