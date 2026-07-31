import {
  createBrowserRouter,
  Navigate,
} from "react-router-dom";


import EnterpriseLayout from "../components/layout/EnterpriseLayout";

import ChatPage from "../pages/ChatPage";

import DashboardPage from "../pages/dashboard/DashboardPage";
import WorkflowsPage from "../pages/workflows/WorkflowsPage";
import WorkflowBuilderPage from "../pages/workflows/WorkflowBuilderPage";
import AgentsPage from "../pages/agents/AgentsPage";
import AgentDetailsPage from "../pages/agents/AgentDetailsPage";
import ActionsPage from "../pages/actions/ActionsPage";
import AuditPage from "../pages/audit/AuditPage";
import SettingsPage from "../pages/settings/SettingsPage";
import KnowledgePage from "../pages/knowledge/KnowledgePage";

import NotFoundPage from "../pages/NotFoundPage";



export const router = createBrowserRouter([

  {
    path: "/",

    element: <EnterpriseLayout />,


    children: [


      // Default landing page
      {
        index: true,

        element: (
          <Navigate
            to="/dashboard"
            replace
          />
        ),

      },



      {
        path: "dashboard",

        element: <DashboardPage />,

        handle: {
          title: "Dashboard",
          icon: "dashboard",
        },

      },



      {
        path: "chat",

        element: <ChatPage />,

        handle: {
          title: "Chat",
          icon: "chat",
        },

      },



      {
        path: "workflows",

        element: <WorkflowsPage />,

        handle: {
          title: "Workflows",
          icon: "workflow",
        },

      },
      { path: "workflows/builder", element: <WorkflowBuilderPage /> },
      { path: "workflows/:workflowId/builder", element: <WorkflowBuilderPage /> },



      {
        path: "agents",

        element: <AgentsPage />,

        handle: {
          title: "Agents",
          icon: "agent",
        },

      },
      { path: "agents/:agentId", element: <AgentDetailsPage /> },



      {
        path: "actions",

        element: <ActionsPage />,

        handle: {
          title: "Actions",
          icon: "action",
        },

      },



      {
        path: "audit",

        element: <AuditPage />,

        handle: {
          title: "Audit",
          icon: "audit",
        },

      },
      { path: "knowledge", element: <KnowledgePage /> },



      {
        path: "settings",

        element: <SettingsPage />,

        handle: {
          title: "Settings",
          icon: "settings",
        },

      },


      // Unknown routes
      {
        path: "*",

        element: <NotFoundPage />,

      },


    ],

  },

]);
