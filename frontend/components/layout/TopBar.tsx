"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "../../lib/stores/authStore";
import { useNotificationStore } from "../../lib/stores/notificationStore";
import { Bell, Search, Sun, Moon, Laptop, ShieldCheck } from "lucide-react";
import { useTheme } from "next-themes";

export default function TopBar() {
  const { user } = useAuthStore();
  const { unreadCount } = useNotificationStore();
  const { theme, setTheme } = useTheme();
  const router = useRouter();

  const toggleTheme = () => {
    if (theme === "light") setTheme("dark");
    else if (theme === "dark") setTheme("system");
    else setTheme("light");
  };

  return (
    <header className="flex h-16 w-full items-center justify-between border-b border-zinc-200 bg-white px-6 dark:border-zinc-800 dark:bg-zinc-950">
      {/* Search Input (Coordinators and Admin only) */}
      <div className="flex flex-1 items-center">
        {(user?.role === "coordinator" || user?.role === "admin") ? (
          <div className="relative w-80">
            <Search className="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-zinc-400" />
            <input
              type="text"
              placeholder="Search patients, donors or active runs..."
              className="h-9 w-full rounded-md border border-zinc-200 bg-zinc-50 pl-10 pr-4 text-xs outline-none focus:border-brand-500 focus:bg-white dark:border-zinc-800 dark:bg-zinc-900 dark:focus:border-brand-500"
            />
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-xs font-semibold text-zinc-500">
            <ShieldCheck className="h-4 w-4 text-brand-500" />
            Bilingual Care Coordinators Available (EN/HI)
          </div>
        )}
      </div>

      {/* Global Actions */}
      <div className="flex items-center gap-4">
        {/* Toggle Dark Mode */}
        <button
          onClick={toggleTheme}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-zinc-200 text-zinc-600 hover:bg-zinc-50 dark:border-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-900"
          title="Toggle color theme"
        >
          {theme === "light" && <Sun className="h-4 w-4" />}
          {theme === "dark" && <Moon className="h-4 w-4" />}
          {theme === "system" && <Laptop className="h-4 w-4" />}
        </button>

        {/* Notifications Icon */}
        <button
          onClick={() => router.push(`/${user?.role}/notifications`)}
          className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-zinc-200 text-zinc-600 hover:bg-zinc-50 dark:border-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-900"
        >
          <Bell className="h-4 w-4" />
          {unreadCount > 0 && (
            <span className="absolute top-1.5 right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-brand-500 text-[9px] font-bold text-white">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </button>

        {/* User Role Tag */}
        <div className="flex items-center gap-2">
          <div className="rounded-full bg-zinc-100 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
            {user?.role} Portal
          </div>
        </div>
      </div>
    </header>
  );
}
