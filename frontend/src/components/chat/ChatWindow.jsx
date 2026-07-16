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

  const isEmpty =
    messages.length === 0;

  return (

    <Box
      sx={{
        flex: 1,
        minHeight: 0,
        overflowY: "auto",
        px: 3,
        pt: 4,
        pb: 18,
        bgcolor: "#F7F9FC",
      }}
    >

      {isEmpty ? (

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
            boxShadow:
              "0 8px 30px rgba(0,0,0,.05)",
          }}
        >

          <SmartToyIcon
            sx={{
              fontSize: 70,
              color: "primary.main",
              mb: 2,
            }}
          />

          <Typography
            variant="h4"
            sx={{
              fontWeight: 700,
            }}
          >
            Enterprise AI Copilot
          </Typography>

          <Typography
            sx={{
              mt: 2,
              mb: 5,
              color: "text.secondary",
              maxWidth: 650,
              mx: "auto",
              lineHeight: 1.8,
            }}
          >
            Ask about Agile, SAP, AWS, AEM,
            Product Management, Software
            Engineering, AI, Architecture,
            APIs and much more.
          </Typography>

          <Box
            sx={{
              display: "flex",
              flexWrap: "wrap",
              justifyContent: "center",
              gap: 2,
            }}
          >

            {suggestions.map(
              (suggestion) => (

                <Chip

                  key={suggestion}

                  label={suggestion}

                  clickable

                  color="primary"

                  variant="outlined"

                  onClick={() =>
                    onPromptClick?.(
                      suggestion
                    )
                  }

                  sx={{

                    cursor: "pointer",

                    transition:
                      "all .2s ease",

                    "&:hover": {

                      bgcolor:
                        "primary.main",

                      color: "#fff",

                      transform:
                        "translateY(-2px)",

                    },

                  }}

                />

              )
            )}

          </Box>

        </Paper>

      ) : (

        <MessageList
          messages={messages}
        />

      )}

      {loading && (
        <TypingIndicator />
      )}

      <div ref={bottomRef} />

    </Box>

  );

}

export default ChatWindow;