import { Box, Paper, Typography } from "@mui/material";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

import CopyButton from "../common/CopyButton";
import MessageHeader from "./MessageHeader";

function MessageBubble({
  role,
  text,
  timestamp,
}) {
  const isUser = role === "user";

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        mb: 3,
        px: 2,
      }}
    >
      <Paper
        elevation={0}
        className="message-paper"
        sx={{
          width: "fit-content",
          maxWidth: {
            xs: "95%",
            md: "78%",
          },

          p: 3,

          borderRadius: 1,

          bgcolor: isUser ? "primary.main" : "#fff",

          color: isUser ? "#fff" : "#222",

          border: isUser
            ? "none"
            : "1px solid rgba(0,0,0,.08)",

          boxShadow: isUser
            ? "0 10px 25px rgba(25,118,210,.25)"
            : "0 8px 25px rgba(0,0,0,.06)",

          transition: "0.25s",

          "&:hover": {
            transform: "translateY(-2px)",
          },

          "& .copy-btn": {
            opacity: 0,
            transition: ".2s",
          },

          "&:hover .copy-btn": {
            opacity: 1,
          },
        }}
      >
        <MessageHeader
          isUser={isUser}
          timestamp={timestamp}
          text={text}
        />

        <Box
          sx={{
            fontSize: 16,
            lineHeight: 2,

            "& p": {
              my: 1.5,
            },

            "& h1": {
              fontSize: "2rem",
              fontWeight: 700,
              mt: 4,
              mb: 2,
            },

            "& h2": {
              fontSize: "1.7rem",
              fontWeight: 700,
              mt: 4,
              mb: 2,
            },

            "& h3": {
              fontSize: "1.35rem",
              fontWeight: 700,
              mt: 3,
              mb: 2,
            },

            "& ul": {
              pl: 3,
            },

            "& ol": {
              pl: 3,
            },

            "& li": {
              mb: 1,
            },

            "& hr": {
              my: 3,
            },

            "& blockquote": {
              borderLeft: "4px solid #1976d2",
              pl: 2,
              ml: 0,
              my: 2,
              color: "#666",
              fontStyle: "italic",
            },

            "& table": {
              width: "100%",
              borderCollapse: "collapse",
              my: 3,
              overflow: "hidden",
            },

            "& thead": {
              background: "#1976d2",
            },

            "& th": {
              color: "#fff",
              padding: "12px",
              textAlign: "left",
              border: "1px solid #ddd",
            },

            "& td": {
              border: "1px solid #ddd",
              padding: "12px",
            },

            "& img": {
              maxWidth: "100%",
              borderRadius: 2,
            },

            "& pre": {
              margin: 0,
            },

            "& code": {
              backgroundColor: isUser
                ? "rgba(255,255,255,.18)"
                : "#F5F5F5",

              color: isUser ? "#fff" : "#C2185B",

              padding: "3px 7px",

              borderRadius: 1,

              fontFamily:
                "Consolas, Monaco, monospace",

              fontSize: 14,
            },
          }}
        >
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({
                inline,
                className,
                children,
                ...props
              }) {
                const match =
                  /language-(\w+)/.exec(
                    className || ""
                  );

                if (!inline && match) {
                  const code = String(children).replace(
                    /\n$/,
                    ""
                  );

                  return (
                    <Box
                      sx={{
                        my: 3,
                        borderRadius: 2,
                        overflow: "hidden",
                        border:
                          "1px solid rgba(0,0,0,.08)",
                      }}
                    >
                      <Box
                        sx={{
                          bgcolor: "#2D2D2D",
                          color: "#fff",

                          px: 2,

                          py: 1,

                          display: "flex",

                          justifyContent:
                            "space-between",

                          alignItems: "center",
                        }}
                      >
                        <Typography
                          variant="caption"
                          sx={{
                            textTransform: "uppercase",
                            fontWeight: 700,
                            letterSpacing: 1,
                          }}
                        >
                          {match[1]}
                        </Typography>

                        <CopyButton text={code} />
                      </Box>

                      <SyntaxHighlighter
                        language={match[1]}
                        style={oneDark}
                        PreTag="div"
                        customStyle={{
                          margin: 0,
                          borderRadius: 0,
                          padding: 20,
                          fontSize: 14,
                        }}
                        {...props}
                      >
                        {code}
                      </SyntaxHighlighter>
                    </Box>
                  );
                }

                return (
                  <code
                    className={className}
                    {...props}
                  >
                    {children}
                  </code>
                );
              },
            }}
          >
            {text}
          </ReactMarkdown>
        </Box>
      </Paper>
    </Box>
  );
}

export default MessageBubble;