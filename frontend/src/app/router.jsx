import {
  createBrowserRouter,
  Navigate,
} from "react-router-dom";
import { lazy, Suspense } from "react";


import EnterpriseLayout from "../components/layout/EnterpriseLayout";

// Route pages are intentionally lazy so chat syntax highlighting, charts, and
// administration dependencies do not inflate the application entry chunk.
// eslint-disable-next-line react-refresh/only-export-components
const ChatPage=lazy(()=>import("../pages/ChatPage"));
// eslint-disable-next-line react-refresh/only-export-components
const DashboardPage=lazy(()=>import("../pages/dashboard/DashboardPage"));
// eslint-disable-next-line react-refresh/only-export-components
const WorkflowsPage=lazy(()=>import("../pages/workflows/WorkflowsPage"));
// eslint-disable-next-line react-refresh/only-export-components
const WorkflowBuilderPage=lazy(()=>import("../pages/workflows/WorkflowBuilderPage"));
// Route-level lazy components intentionally live beside the router configuration.
// eslint-disable-next-line react-refresh/only-export-components
const AgentsPage=lazy(()=>import("../pages/agents/AgentsPage"));
// eslint-disable-next-line react-refresh/only-export-components
const AgentDetailsPage=lazy(()=>import("../pages/agents/AgentDetailsPage"));
// eslint-disable-next-line react-refresh/only-export-components
const AgentExecutionDetailsPage=lazy(()=>import("../pages/agents/AgentDetailsPage").then(module=>({default:module.AgentExecutionDetailsPage})));
const deferred=Component=><Suspense fallback={<main className="p-8" aria-live="polite">Loading page…</main>}><Component/></Suspense>;
// eslint-disable-next-line react-refresh/only-export-components
const ActionsPage=lazy(()=>import("../pages/actions/ActionsPage"));
// eslint-disable-next-line react-refresh/only-export-components
const AuditPage=lazy(()=>import("../pages/audit/AuditPage"));
// eslint-disable-next-line react-refresh/only-export-components
const SettingsPage=lazy(()=>import("../pages/settings/SettingsPage"));
// eslint-disable-next-line react-refresh/only-export-components
const KnowledgePage=lazy(()=>import("../pages/knowledge/KnowledgePage"));
// eslint-disable-next-line react-refresh/only-export-components
const ToolCatalogPage=lazy(()=>import("../pages/tools/ToolCatalogPage"));
// eslint-disable-next-line react-refresh/only-export-components
const ToolDetailsPage=lazy(()=>import("../pages/tools/ToolDetailsPage"));
// eslint-disable-next-line react-refresh/only-export-components
const IntegrationsPage=lazy(()=>import("../pages/tools/IntegrationsPage"));
// eslint-disable-next-line react-refresh/only-export-components
const IntegrationDetailPage=lazy(()=>import("../pages/tools/IntegrationDetailPage"));
// eslint-disable-next-line react-refresh/only-export-components
const ToolExecutionsPage=lazy(()=>import("../pages/tools/ToolExecutionsPage"));
import NotFoundPage from "../pages/NotFoundPage";
const adminPage=name=>lazy(()=>import("./AdminPages").then(module=>({default:module[name]})));
const DiscoveryPage=adminPage("DiscoveryPage"),GovernancePage=adminPage("GovernancePage"),MarketplacePage=adminPage("MarketplacePage"),MCPServerDetailsPage=adminPage("MCPServerDetailsPage"),MCPServerFormPage=adminPage("MCPServerFormPage"),MCPServersPage=adminPage("MCPServersPage"),NativeToolsPage=adminPage("NativeToolsPage"),NativeWorkspacePage=adminPage("NativeWorkspacePage"),ToolAnalyticsPage=adminPage("ToolAnalyticsPage");


export const router = createBrowserRouter([

  {
    path: "/",

    element: deferred(EnterpriseLayout),


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

        element: deferred(AgentsPage),

        handle: {
          title: "Agents",
          icon: "agent",
        },

      },
      { path: "agents/:agentId", element: deferred(AgentDetailsPage) },
      { path: "agents/:agentId/executions/:executionId", element: deferred(AgentExecutionDetailsPage) },



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
      { path: "tools", element: <ToolCatalogPage /> },
      { path: "tools/:name", element: <ToolDetailsPage /> },
      { path: "integrations", element: <IntegrationsPage /> },
      { path: "integrations/:connectionId", element: <IntegrationDetailPage /> },
      { path: "tool-executions", element: <ToolExecutionsPage /> },
      { path: "native-tools", element: <NativeToolsPage /> },
      { path: "native-tools/:family", element: <NativeWorkspacePage /> },
      { path: "mcp-servers", element: <MCPServersPage /> },
      { path: "mcp-servers/new", element: <MCPServerFormPage /> },
      { path: "mcp-servers/:serverId", element: <MCPServerDetailsPage /> },
      { path: "discovery", element: <DiscoveryPage /> },
      { path: "tool-marketplace", element: <MarketplacePage /> },
      { path: "tool-governance", element: <GovernancePage /> },
      { path: "tool-analytics", element: <ToolAnalyticsPage /> },



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
