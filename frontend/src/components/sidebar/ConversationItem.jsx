import {
  ListItemButton,
  ListItemText,
} from "@mui/material";

function ConversationItem({
  conversation,
  selected,
  onClick,
}) {
  return (
    <ListItemButton
      selected={selected}
      onClick={onClick}
      sx={{
        mx: 1,
        mb: 0.5,
        borderRadius: 2,
      }}
    >
      <ListItemText
        primary={conversation.title}
        primaryTypographyProps={{
          noWrap: true,
          fontSize: 14,
          fontWeight: 500,
        }}
      />
    </ListItemButton>
  );
}

export default ConversationItem;