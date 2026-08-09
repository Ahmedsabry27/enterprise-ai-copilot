import { NavLink } from "react-router-dom";

import {
  LayoutDashboard,
  MessageSquare,
  Workflow,
  Bot,
  Zap,
  BookOpen,
  ShieldCheck,
  Settings,
  Wrench,
  PlugZap,
  History,
  ServerCog,
  Compass,
  Store,
  Shield,
  ChartNoAxesCombined,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";

export default function Sidebar({
  collapsed,
  onCollapsedChange,
}) {
  const menu = [
    {
      name: "Dashboard",
      path: "/dashboard",
      icon: LayoutDashboard,
    },
    {
      name: "Chat",
      path: "/chat",
      icon: MessageSquare,
    },
    {
      name: "Workflows",
      path: "/workflows",
      icon: Workflow,
    },
    {
      name: "Agents",
      path: "/agents",
      icon: Bot,
    },
    {
      name: "Actions",
      path: "/actions",
      icon: Zap,
    },
    {
      name: "Tool Catalog",
      path: "/tools",
      icon: Wrench,
    },
    {
      name: "Native Tools",
      path: "/native-tools",
      icon: Wrench,
    },
    {
      name: "MCP Servers",
      path: "/mcp-servers",
      icon: ServerCog,
    },
    {
      name: "Discovery",
      path: "/discovery",
      icon: Compass,
    },
    {
      name: "Tool Marketplace",
      path: "/tool-marketplace",
      icon: Store,
    },
    {
      name: "Governance",
      path: "/tool-governance",
      icon: Shield,
    },
    {
      name: "Tool Analytics",
      path: "/tool-analytics",
      icon: ChartNoAxesCombined,
    },
    {
      name: "Integrations",
      path: "/integrations",
      icon: PlugZap,
    },
    {
      name: "Executions",
      path: "/tool-executions",
      icon: History,
    },
    {
      name: "Knowledge",
      path: "/knowledge",
      icon: BookOpen,
    },
    {
      name: "Audit",
      path: "/audit",
      icon: ShieldCheck,
    },
    {
      name: "Settings",
      path: "/settings",
      icon: Settings,
    },
  ];

  return (
    <aside
      className={`
        h-screen
        flex
        flex-col
        overflow-hidden
        bg-slate-950
        border-r
        border-white/10
        transition-[width]
        duration-300
        ease-in-out
        shrink-0
        ${collapsed ? "w-20" : "w-72"}
      `}
    >
      {/* ==================================================
          Brand + Collapse Button
      ================================================== */}
      <div
        className={`
          flex
          flex-shrink-0
          items-start
          pt-8
          pb-6
          transition-all
          duration-300
          ${
            collapsed
              ? "justify-center px-2"
              : "justify-between px-6"
          }
        `}
      >
        {!collapsed && (
          <div className="min-w-0">
            <h1
              className="
                truncate
                text-2xl
                font-semibold
                tracking-tight
                text-white
              "
            >
              Enterprise AI
            </h1>

            <p
              className="
                mt-1
                truncate
                text-sm
                text-slate-400
              "
            >
              Copilot Platform
            </p>
          </div>
        )}

        <button
          type="button"
          onClick={() =>
            onCollapsedChange(!collapsed)
          }
          aria-label={
            collapsed
              ? "Expand sidebar"
              : "Collapse sidebar"
          }
          aria-expanded={!collapsed}
          title={
            collapsed
              ? "Expand sidebar"
              : "Collapse sidebar"
          }
          className="
            flex
            h-10
            w-10
            flex-shrink-0
            items-center
            justify-center
            rounded-xl
            border
            border-white/10
            bg-white/[0.03]
            text-slate-400
            transition-all
            duration-200
            hover:border-white/20
            hover:bg-white/10
            hover:text-white
            focus:outline-none
            focus:ring-2
            focus:ring-blue-500/50
          "
        >
          {collapsed ? (
            <PanelLeftOpen className="h-5 w-5" />
          ) : (
            <PanelLeftClose className="h-5 w-5" />
          )}
        </button>
      </div>

      {/* ==================================================
          Scrollable Navigation
      ================================================== */}
      <nav
        className={`
          flex-1
          min-h-0
          overflow-y-auto
          overflow-x-hidden
          pb-4
          transition-all
          duration-300
          ${collapsed ? "px-2" : "px-4"}
        `}
      >
        <div className="space-y-1">
          {menu.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.path}
                to={item.path}
                title={
                  collapsed
                    ? item.name
                    : undefined
                }
                className={({ isActive }) => `
                  group
                  flex
                  items-center
                  rounded-xl
                  py-3
                  transition-all
                  duration-200

                  ${
                    collapsed
                      ? "justify-center px-3"
                      : "gap-4 px-4"
                  }

                  ${
                    isActive
                      ? `
                        border
                        border-blue-400/30
                        bg-gradient-to-r
                        from-blue-500/30
                        to-purple-500/20
                        text-white
                        shadow-lg
                        shadow-blue-500/10
                      `
                      : `
                        border
                        border-transparent
                        text-slate-400
                        hover:bg-white/10
                        hover:text-white
                      `
                  }
                `}
              >
                <Icon
                  className="
                    h-5
                    w-5
                    flex-shrink-0
                    transition-transform
                    duration-200
                    group-hover:scale-110
                  "
                />

                {!collapsed && (
                  <span
                    className="
                      whitespace-nowrap
                      text-sm
                      font-medium
                    "
                  >
                    {item.name}
                  </span>
                )}
              </NavLink>
            );
          })}
        </div>
      </nav>

      {/* ==================================================
          User Profile
      ================================================== */}
      <div
        className={`
          flex-shrink-0
          border-t
          border-white/10
          bg-slate-950
          transition-all
          duration-300
          ${collapsed ? "p-3" : "p-4"}
        `}
      >
        <div
          title={
            collapsed
              ? "Ahmed Sabry — Enterprise User"
              : undefined
          }
          className={`
            flex
            items-center
            rounded-2xl
            bg-white/5
            transition-all
            duration-200
            hover:bg-white/10

            ${
              collapsed
                ? "justify-center p-2"
                : "gap-3 px-4 py-3"
            }
          `}
        >
          <div
            className="
              flex
              h-10
              w-10
              flex-shrink-0
              items-center
              justify-center
              rounded-full
              bg-gradient-to-br
              from-blue-500
              to-purple-600
              text-sm
              font-semibold
              text-white
              shadow-lg
              shadow-purple-500/10
            "
          >
            AS
          </div>

          {!collapsed && (
            <div className="min-w-0">
              <div
                className="
                  truncate
                  text-sm
                  font-medium
                  text-white
                "
              >
                Ahmed Sabry
              </div>

              <div
                className="
                  truncate
                  text-xs
                  text-slate-400
                "
              >
                Enterprise User
              </div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}