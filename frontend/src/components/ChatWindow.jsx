import { Box, Typography } from "@mui/material";

function ChatWindow() {
  return (
    <Box
      sx={{
        flex: 1,
        padding: 3,
        overflow: "auto",
      }}
    >
      <Typography variant="h5">
        Welcome Ahmed 👋
      </Typography>

      <Typography sx={{ mt: 2 }}>
        Ask me anything about Agile, SAP, AI,
        AEM, Product Management or Software Engineering.
      </Typography>
    </Box>
  );
}

export default ChatWindow;