import {
  List,
  Typography,
  Box,
} from "@mui/material";

import ConversationItem from "./ConversationItem";
import groupConversations from "../../utils/groupConversations";

function ConversationList({
  conversations = [],
  selectedId,
  onSelect,
}) {
  const groups =
    groupConversations(conversations);

  return (
    <List
      sx={{
        flex: 1,
        overflowY: "auto",
        p: 0,
      }}
    >
      {Object.entries(groups).map(
        ([title, items]) => {
          if (items.length === 0) return null;

          return (
            <Box key={title}>
              <Typography
                sx={{
                  px: 2,
                  py: 1.5,
                  fontSize: 12,
                  fontWeight: 700,
                  color: "text.secondary",
                  textTransform: "uppercase",
                  letterSpacing: 1,
                }}
              >
                {title}
              </Typography>

              {items.map((conversation) => (
                <ConversationItem
                  key={conversation.id}
                  conversation={conversation}
                  selected={
                    selectedId ===
                    conversation.id
                  }
                  onClick={() =>
                    onSelect(conversation)
                  }
                />
              ))}
            </Box>
          );
        }
      )}
    </List>
  );
}

export default ConversationList;