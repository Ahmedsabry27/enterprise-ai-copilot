import SmartToyIcon from "@mui/icons-material/SmartToy";
import { AppBar, Box, Toolbar, Typography } from "@mui/material";

import UserMenu from "./UserMenu.jsx";

function Header() {
  return (
    <AppBar
      position="static"
      elevation={1}
      sx={{
        bgcolor: "#2563EB",
        height: 64,
      }}
    >
      <Toolbar sx={{ height: "100%" }}>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 2,
            flexGrow: 1,
          }}
        >
          <SmartToyIcon sx={{ fontSize: 28 }} />

          <Typography
            variant="h6"
            fontWeight={600}
          >
            Enterprise AI Copilot
          </Typography>
        </Box>

        <UserMenu />
      </Toolbar>
    </AppBar>
  );
}

export default Header;