import { Box, Typography } from "@mui/material";

import ConversationList from "./ConversationList";
import NewChatButton from "./NewChatButton";

function Sidebar({
  conversations = [],
  selectedConversationId,
  onConversationSelect,
  onNewChat,
}) {
  return (
    <Box
      sx={{
        width: 300,
        flexShrink: 0,
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        bgcolor: "#fff",
        borderRight: "1px solid #E5E7EB",
      }}
    >
      <Typography
        variant="h5"
        sx={{
          p: 2,
          fontWeight: 700,
        }}
      >
        Conversations
      </Typography>

      {false && (
       <NewChatButton onClick={onNewChat} />
       )}

      <Box
        sx={{
          flex: 1,
          overflowY: "auto",
          minHeight: 0,
        }}
      >
        <ConversationList
          conversations={conversations}
          selectedId={selectedConversationId}
          onSelect={onConversationSelect}
        />
      </Box>
    </Box>
  );
}

export default Sidebar;