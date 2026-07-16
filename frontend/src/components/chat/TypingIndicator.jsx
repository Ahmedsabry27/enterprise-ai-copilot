import { Box, Typography } from "@mui/material";
import SmartToyIcon from "@mui/icons-material/SmartToy";

function TypingIndicator() {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 2,
        px: 3,
        py: 2,
      }}
    >
      <SmartToyIcon
        color="primary"
        sx={{
          animation: "pulse 1.4s infinite",
          "@keyframes pulse": {
            "0%": { opacity: 0.4 },
            "50%": { opacity: 1 },
            "100%": { opacity: 0.4 },
          },
        }}
      />

      <Typography
        color="text.secondary"
        sx={{
          fontStyle: "italic",
        }}
      >
        Enterprise AI Copilot is thinking...
      </Typography>
    </Box>
  );
}

export default TypingIndicator;