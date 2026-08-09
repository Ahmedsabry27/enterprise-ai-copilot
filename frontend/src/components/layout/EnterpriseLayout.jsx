import { useState } from "react";
import { Outlet } from "react-router-dom";

import {
  Search,
  Bell,
  Settings,
} from "lucide-react";

import Sidebar from "./Sidebar";

export default function EnterpriseLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] =
    useState(false);

  return (
    <div
      className="
        flex
        h-screen
        w-full
        overflow-hidden
        bg-gradient-to-br
        from-[#071426]
        via-[#10254d]
        to-[#06111f]
        text-white
      "
    >
      {/* ==================================================
          SIDEBAR
      ================================================== */}

      <div
        className="
          hidden
          lg:flex
          h-screen
          shrink-0
          overflow-hidden
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
          flex-1
          min-w-0
          min-h-0
          flex-col
          overflow-hidden
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
            h-20
            shrink-0
            flex
            items-center
            justify-between
            border-b
            border-white/10
            bg-white/5
            px-3
            sm:px-6
            lg:px-8
            backdrop-blur-xl
          "
        >
          {/* Search */}

          <div
            className="
              hidden
              sm:flex
              items-center
              gap-3
              rounded-xl
              border
              border-white/10
              bg-white/5
              px-4
              py-3
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
                md:flex
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
              "
            >
              <span
                className="
                  h-2
                  w-2
                  rounded-full
                  bg-emerald-400
                  animate-pulse
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

            <div
              className="
                flex
                items-center
                gap-3
              "
            >
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
          className="
            min-h-0
            min-w-0
            flex-1
            overflow-y-auto
            overflow-x-hidden
            p-4
            sm:p-6
            lg:p-8
          "
        >
          <div
            className="
              min-h-full
              min-w-0
              overflow-hidden
              rounded-3xl
              border
              border-white/10
              bg-[#07182f]
              shadow-2xl
              shadow-black/20
            "
          >
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}