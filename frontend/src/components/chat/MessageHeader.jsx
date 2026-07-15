import {
  Avatar,
  Box,
  Stack,
  Typography,
} from "@mui/material";

import SmartToyIcon from "@mui/icons-material/SmartToy";
import PersonIcon from "@mui/icons-material/Person";

import CopyButton from "../common/CopyButton";

function MessageHeader({
  isUser,
  timestamp,
  text,
}) {
  return (
    <Stack
      direction="row"
      justifyContent="space-between"
      alignItems="center"
      sx={{
        mb: 2,
      }}
    >
      <Stack
        direction="row"
        spacing={1.5}
        alignItems="center"
      >
        <Avatar
          sx={{
            width: 36,
            height: 36,
            bgcolor: isUser ? "primary.main" : "#10A37F",
            boxShadow: "0 2px 8px rgba(0,0,0,.15)",
          }}
        >
          {isUser ? (
            <PersonIcon fontSize="small" />
          ) : (
            <SmartToyIcon fontSize="small" />
          )}
        </Avatar>

        <Box>
          <Stack
            direction="row"
            spacing={1}
            alignItems="center"
          >
            <Typography
              sx={{
                fontWeight: 700,
                fontSize: "0.95rem",
              }}
            >
              {isUser ? "You" : "Enterprise AI Copilot"}
            </Typography>

            {timestamp && (
              <Typography
                variant="caption"
                sx={{
                  color: "text.secondary",
                  fontSize: "0.75rem",
                }}
              >
                {timestamp}
              </Typography>
            )}
          </Stack>
        </Box>
      </Stack>

      {!isUser && (
        <CopyButton text={text} />
      )}
    </Stack>
  );
}

export default MessageHeader;