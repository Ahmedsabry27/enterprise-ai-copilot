import { useEffect, useRef } from "react";
import {
  Box,
  Paper,
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
        pt: 4,
        pb: 18,
        bgcolor: "#F7F9FC",
      }}
    >
      {messages.length === 0 ? (
        <Paper
          elevation={0}
          sx={{
            width: "100%",
            maxWidth: 900,
            mx: "auto",
            mt: 8,
            p: 6,
            borderRadius: 4,
            textAlign: "center",
            bgcolor: "#fff",
            border: "1px solid rgba(0,0,0,.08)",
            boxShadow: "0 8px 30px rgba(0,0,0,.05)",
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
              mb: 4,
              color: "text.secondary",
              maxWidth: 600,
              mx: "auto",
              lineHeight: 1.7,
            }}
          >
            Your Enterprise AI Copilot can help with Agile,
            Product Management, SAP, AWS, AEM, AI,
            Software Engineering, Architecture and much more.
          </Typography>

          {/* Suggested Prompts */}
          <Box
            sx={{
              display: "flex",
              flexWrap: "wrap",
              justifyContent: "center",
              alignItems: "center",
              gap: 2,
              width: "100%",
              maxWidth: 700,
              mx: "auto",
            }}
          >
            {suggestions.map((prompt) => (
              <Chip
                key={prompt}
                label={prompt}
                clickable
                color="primary"
                variant="outlined"
                onClick={() => onPromptClick?.(prompt)}
                sx={{
                  cursor: "pointer",
                  fontWeight: 500,
                  px: 1,
                  py: 2.5,
                  transition: "all .25s ease",

                  "&:hover": {
                    bgcolor: "#1976d2",
                    color: "#fff",
                    transform: "translateY(-2px)",
                    boxShadow: "0 6px 18px rgba(25,118,210,.25)",
                  },
                }}
              />
            ))}
          </Box>
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