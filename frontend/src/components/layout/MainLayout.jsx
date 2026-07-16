import { Box } from "@mui/material";

import Header from "./Header";
import Sidebar from "../sidebar/Sidebar";

function MainLayout({
  children,
  conversations,
  selectedConversationId,
  onConversationSelect,
  onNewChat,
}) {
  return (
    <Box
      sx={{
        display: "flex",
        width: "100vw",
        height: "100vh",
        overflow: "hidden",
        bgcolor: "#F5F7FA",
      }}
    >
      <Sidebar
        conversations={conversations}
        selectedConversationId={selectedConversationId}
        onConversationSelect={onConversationSelect}
        onNewChat={onNewChat}
      />

      {/* Right Side */}
      <Box
        sx={{
          flex: 1,
          display: "flex",
          flexDirection: "column",

          // IMPORTANT
          minWidth: 0,
          minHeight: 0,

          overflow: "hidden",
        }}
      >
        <Header />

        {/* Chat Area */}
        <Box
          sx={{
            flex: 1,
            display: "flex",
            flexDirection: "column",

            // IMPORTANT
            minWidth: 0,
            minHeight: 0,

            overflow: "hidden",
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
}

export default MainLayout;