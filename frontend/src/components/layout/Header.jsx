import SmartToyIcon from "@mui/icons-material/SmartToy";
import { AppBar, Toolbar, Typography } from "@mui/material";

function Header() {
  return (
    <AppBar position="static">
      <Toolbar>
        <SmartToyIcon sx={{ mr: 2 }} />

        <Typography variant="h6">
          Enterprise AI Copilot
        </Typography>
      </Toolbar>
    </AppBar>
  );
}

export default Header;