import Box from "@mui/material/Box";
import MessageBubble from "./MessageBubble";

function MessageList({ messages }) {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: 1,
      }}
    >
      {messages.map((message, index) => (
        <MessageBubble
          key={message.id ?? index}
          role={message.role}
          text={message.text}
          timestamp={message.timestamp}
          streaming={message.isStreaming}
        />
      ))}
    </Box>
  );
}

export default MessageList;