import { Box, CircularProgress, Typography } from "@mui/material";

function TypingIndicator() {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 2,
        p: 2,
      }}
    >
      <CircularProgress size={20} />

      <Typography>
        Enterprise AI Copilot is thinking...
      </Typography>
    </Box>
  );
}

export default TypingIndicator;