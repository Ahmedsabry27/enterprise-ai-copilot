import { useState } from "react";

import {
  Avatar,
  Box,
  Button,
  Divider,
  ListItemIcon,
  Menu,
  MenuItem,
  Typography,
} from "@mui/material";

import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import LogoutIcon from "@mui/icons-material/Logout";
import PersonIcon from "@mui/icons-material/Person";
import SettingsIcon from "@mui/icons-material/Settings";

import useAuth from "../../hooks/useAuth";

function UserMenu() {
  const { user, logout } = useAuth();

  const [anchorEl, setAnchorEl] = useState(null);

  const open = Boolean(anchorEl);

  const handleOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    handleClose();
    await logout();
  };

  const initials =
    user?.initials ||
    user?.name
      ?.split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase() ||
    user?.email?.charAt(0).toUpperCase() ||
    "U";

  const displayName =
    user?.givenName ||
    user?.name?.split(" ")[0] ||
    user?.email?.split("@")[0] ||
    user?.username ||
    "User";

  return (
    <>
      <Button
        color="inherit"
        onClick={handleOpen}
        endIcon={<KeyboardArrowDownIcon />}
        sx={{
          textTransform: "none",
          borderRadius: 2,
          px: 1.5,
          py: 0.75,
          minWidth: 0,
          "&:hover": {
            backgroundColor: "rgba(255,255,255,0.12)",
          },
        }}
      >
        <Avatar
          sx={{
            width: 38,
            height: 38,
            bgcolor: "#1E3A8A",
            fontWeight: 600,
            fontSize: 14,
          }}
        >
          {initials}
        </Avatar>

        <Box
          sx={{
            ml: 1.5,
            textAlign: "left",
            display: {
              xs: "none",
              md: "block",
            },
          }}
        >
          <Typography
            sx={{
              color: "white",
              fontWeight: 600,
              fontSize: 14,
              lineHeight: 1.2,
            }}
          >
            {displayName}
          </Typography>

          <Typography
            sx={{
              color: "rgba(255,255,255,0.75)",
              fontSize: 12,
              maxWidth: 160,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {user?.email ?? ""}
          </Typography>
        </Box>
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        PaperProps={{
          elevation: 8,
          sx: {
            mt: 1,
            width: 280,
            borderRadius: 3,
            overflow: "hidden",
          },
        }}
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "right",
        }}
        transformOrigin={{
          vertical: "top",
          horizontal: "right",
        }}
      >
        <Box
          sx={{
            p: 2,
            display: "flex",
            alignItems: "center",
            gap: 2,
          }}
        >
          <Avatar
            sx={{
              width: 52,
              height: 52,
              bgcolor: "#2563EB",
              fontWeight: 600,
            }}
          >
            {initials}
          </Avatar>

          <Box>
            <Typography
              sx={{
                fontWeight: 600,
                fontSize: 15,
              }}
            >
              {user?.name || displayName}
            </Typography>

            <Typography
              variant="body2"
              color="text.secondary"
            >
              {user?.email ?? ""}
            </Typography>
          </Box>
        </Box>

        <Divider />

        <MenuItem onClick={handleClose}>
          <ListItemIcon>
            <PersonIcon fontSize="small" />
          </ListItemIcon>

          Profile
        </MenuItem>

        <MenuItem onClick={handleClose}>
          <ListItemIcon>
            <SettingsIcon fontSize="small" />
          </ListItemIcon>

          Settings
        </MenuItem>

        <Divider />

        <MenuItem
          onClick={handleLogout}
          sx={{
            color: "error.main",
          }}
        >
          <ListItemIcon>
            <LogoutIcon color="error" fontSize="small" />
          </ListItemIcon>

          Logout
        </MenuItem>
      </Menu>
    </>
  );
}

export default UserMenu;