import { Box, Typography } from "@mui/material";
import MessageList from "./MessageList";
import TypingIndicator from "./TypingIndicator";

function ChatWindow({ messages, loading }) {
  return (
    <Box
      sx={{
        flex: 1,
        overflowY: "auto",
        p: 3,
      }}
    >
      {messages.length === 0 ? (
        <>
          <Typography variant="h4">
            Welcome Ahmed 👋
          </Typography>

          <Typography sx={{ mt: 2 }}>
            Ask me anything about Agile, SAP, AI,
            AEM, Product Management or Software Engineering.
          </Typography>
        </>
      ) : (
        <MessageList messages={messages} />
      )}

      {loading && <TypingIndicator />}
    </Box>
  );
}

export default ChatWindow;