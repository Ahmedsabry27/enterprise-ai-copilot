import { useState } from "react";

import {
  Box,
  IconButton,
  Paper,
  TextField,
  Tooltip,
} from "@mui/material";

import SendIcon from "@mui/icons-material/Send";
import StopCircleIcon from "@mui/icons-material/StopCircle";

function ChatInput({
  onSend,
  onStop,
  loading,
}) {

  const [message, setMessage] = useState("");

  // --------------------------------------------------
  // Send
  // --------------------------------------------------

  async function send() {

    const text = message.trim();

    if (!text) return;

    setMessage("");

    await onSend?.(text);

  }

  // --------------------------------------------------
  // Keyboard
  // --------------------------------------------------

  function handleKeyDown(event) {

    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {

      event.preventDefault();

      send();

    }

  }

  return (

    <Box
      sx={{
        flexShrink: 0,
        bgcolor: "#fff",
        borderTop: "1px solid rgba(0,0,0,.08)",
        p: 2,
      }}
    >

      <Paper
        elevation={0}
        sx={{
          p: 2,
          borderRadius: 3,
          border: "1px solid #E5E7EB",
        }}
      >

        <Box
          sx={{
            display: "flex",
            alignItems: "flex-end",
            gap: 2,
          }}
        >

          <TextField
            fullWidth
            multiline
            maxRows={6}
            placeholder="Ask Enterprise AI Copilot..."
            value={message}
            disabled={loading}
            onChange={(e) =>
              setMessage(e.target.value)
            }
            onKeyDown={handleKeyDown}
          />

          {loading ? (

            <Tooltip title="Stop">

              <IconButton
                color="error"
                onClick={onStop}
              >
                <StopCircleIcon />
              </IconButton>

            </Tooltip>

          ) : (

            <Tooltip title="Send">

              <span>

                <IconButton
                  color="primary"
                  disabled={!message.trim()}
                  onClick={send}
                >
                  <SendIcon />
                </IconButton>

              </span>

            </Tooltip>

          )}

        </Box>

      </Paper>

    </Box>

  );

}

export default ChatInput;