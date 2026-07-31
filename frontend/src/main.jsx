import React from "react";
import ReactDOM from "react-dom/client";

import "./config/amplify";
import "./index.css";

import { ThemeProvider, CssBaseline } from "@mui/material";
import { TooltipProvider } from "@/components/ui/tooltip";

import "@fontsource/inter";

import App from "./App";
import theme from "./theme";

import QueryProvider from "./providers/QueryProvider";


ReactDOM.createRoot(
  document.getElementById("root")
).render(

  <ThemeProvider theme={theme}>

    <CssBaseline />


    <QueryProvider>

      <TooltipProvider>

        <App />

      </TooltipProvider>

    </QueryProvider>


  </ThemeProvider>

);