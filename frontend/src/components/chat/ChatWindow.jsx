import { useEffect, useRef } from "react";
import {
  Box,
  Paper,
  Stack,
  Typography,
  Chip,
} from "@mui/material";

import SmartToyIcon from "@mui/icons-material/SmartToy";

import MessageList from "./MessageList";
import TypingIndicator from "./TypingIndicator";

const suggestions = [
  "Generate Scrum User Stories",
  "Explain SAP S/4HANA",
  "Create a Jira Epic",
  "Write Python Code",
  "Design an AWS Architecture",
  "Explain AEM",
];

function ChatWindow({
  messages,
  loading,
  onPromptClick,
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  return (
    <Box
      sx={{
        flex: 1,
        overflowY: "auto",
        px: 3,
        py: 4,
        bgcolor: "#F7F9FC",
      }}
    >
      {messages.length === 0 ? (
        <Paper
          elevation={0}
          sx={{
            maxWidth: 800,
            mx: "auto",
            mt: 8,
            p: 5,
            borderRadius: 4,
            textAlign: "center",
            bgcolor: "#fff",
            border: "1px solid rgba(0,0,0,.08)",
          }}
        >
          <SmartToyIcon
            sx={{
              fontSize: 70,
              color: "#1976d2",
              mb: 2,
            }}
          />

          <Typography
            variant="h4"
            fontWeight={700}
          >
            Welcome Ahmed 👋
          </Typography>

          <Typography
            sx={{
              mt: 2,
              color: "text.secondary",
              maxWidth: 550,
              mx: "auto",
            }}
          >
            Your Enterprise AI Copilot can help with
            Agile, Product Management, SAP,
            AWS, AEM, AI, Software Engineering,
            Architecture and much more.
          </Typography>

          <Stack
            direction="row"
            spacing={1.5}
            justifyContent="center"
            flexWrap="wrap"
            sx={{
              mt: 5,
              gap: 1.5,
            }}
          >
            {suggestions.map((prompt) => (
              <Chip
                key={prompt}
                label={prompt}
                clickable
                color="primary"
                variant="outlined"
                onClick={() =>
                  onPromptClick?.(prompt)
                }
              />
            ))}
          </Stack>
        </Paper>
      ) : (
        <MessageList messages={messages} />
      )}

      {loading && <TypingIndicator />}

      <div ref={bottomRef} />
    </Box>
  );
}

export default ChatWindow;