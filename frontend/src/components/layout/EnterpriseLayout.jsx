import { useState } from "react";
import {
  Outlet,
  useLocation,
} from "react-router-dom";

import {
  Search,
  Bell,
  Settings,
} from "lucide-react";

import Sidebar from "./Sidebar";

export default function EnterpriseLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] =
    useState(false);

  const location = useLocation();

  // Chat needs its own internal scrolling.
  // Other pages can continue using normal page scrolling.
  const isChatPage =
    location.pathname === "/chat" ||
    location.pathname.startsWith("/chat/");

  return (
    <div
      className="
        flex
        h-screen
        min-h-0
        w-full
        overflow-hidden
        bg-[#061426]
        text-slate-100
      "
    >
      {/* ==================================================
          SIDEBAR
      ================================================== */}

      <div
        className="
          hidden
          h-screen
          shrink-0
          overflow-hidden
          lg:flex
        "
      >
        <Sidebar
          collapsed={sidebarCollapsed}
          onCollapsedChange={setSidebarCollapsed}
        />
      </div>

      {/* ==================================================
          APPLICATION
      ================================================== */}

      <div
        className="
          flex
          min-h-0
          min-w-0
          flex-1
          flex-col
          overflow-hidden
          bg-[#0a1b33]
          transition-all
          duration-300
          ease-in-out
        "
      >
        {/* ==================================================
            TOP BAR
        ================================================== */}

        <header
          className="
            flex
            h-20
            shrink-0
            items-center
            justify-between
            border-b
            border-white/10
            bg-[#0d203b]/95
            px-3
            backdrop-blur-xl
            sm:px-6
            lg:px-8
          "
        >
          {/* Search */}

          <div
            className="
              hidden
              items-center
              gap-3
              rounded-xl
              border
              border-white/10
              bg-white/5
              px-4
              py-3
              sm:flex
              sm:w-[min(420px,55vw)]
            "
          >
            <Search
              className="
                h-5
                w-5
                shrink-0
                text-slate-400
              "
            />

            <input
              placeholder="Search workflows, agents, actions..."
              className="
                w-full
                min-w-0
                bg-transparent
                text-sm
                text-slate-200
                outline-none
                placeholder:text-slate-500
              "
            />
          </div>

          {/* Right Side */}

          <div
            className="
              ml-auto
              flex
              items-center
              gap-3
              sm:gap-5
            "
          >
            {/* Runtime */}

            <div
              className="
                hidden
                items-center
                gap-2
                rounded-full
                border
                border-emerald-400/30
                bg-emerald-400/10
                px-5
                py-2
                text-sm
                text-emerald-300
                md:flex
              "
            >
              <span
                className="
                  h-2
                  w-2
                  animate-pulse
                  rounded-full
                  bg-emerald-400
                "
              />

              AI Runtime Online
            </div>

            {/* Notifications */}

            <button
              type="button"
              aria-label="Notifications"
              className="
                flex
                h-10
                w-10
                items-center
                justify-center
                rounded-xl
                text-slate-300
                transition
                hover:bg-white/10
                hover:text-white
              "
            >
              <Bell className="h-5 w-5" />
            </button>

            {/* Settings */}

            <button
              type="button"
              aria-label="Settings"
              className="
                flex
                h-10
                w-10
                items-center
                justify-center
                rounded-xl
                text-slate-300
                transition
                hover:bg-white/10
                hover:text-white
              "
            >
              <Settings className="h-5 w-5" />
            </button>

            {/* Profile */}

            <div className="flex items-center gap-3">
              <div
                className="
                  flex
                  h-11
                  w-11
                  items-center
                  justify-center
                  rounded-full
                  bg-gradient-to-br
                  from-blue-500
                  to-purple-600
                  font-semibold
                  text-white
                  shadow-lg
                "
              >
                AS
              </div>
            </div>
          </div>
        </header>

        {/* ==================================================
            PAGE CONTENT
        ================================================== */}

        <main
          className={`
            min-h-0
            min-w-0
            flex-1
            overflow-x-hidden
            bg-[#081a30]
            p-4
            sm:p-6
            lg:p-8

            ${
              isChatPage
                ? "overflow-hidden"
                : "overflow-y-auto"
            }
          `}
        >
          <div
            className={`
              min-w-0
              overflow-hidden
              rounded-3xl
              border
              border-white/10
              bg-[#07182f]
              shadow-2xl
              shadow-black/20

              ${
                isChatPage
                  ? "h-full min-h-0"
                  : "min-h-full"
              }
            `}
          >
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}