"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "../../lib/stores/authStore";
import { cn } from "../../lib/utils/cn";
import {
  LayoutDashboard,
  Calendar,
  Activity,
  HeartHandshake,
  Award,
  Wallet,
  Bell,
  Settings,
  LogOut,
  Users,
  ShieldAlert,
  Hospital,
  AlertTriangle,
  Flame,
  CheckCircle,
} from "lucide-react";

interface SidebarProps {
  className?: string;
}

export default function Sidebar({ className }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, clearAuth } = useAuthStore();
  const role = user?.role;

  const handleLogout = () => {
    clearAuth();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  };

  // Nav link mappings based on user role
  const getNavLinks = () => {
    switch (role) {
      case "patient":
        return [
          { name: "Dashboard", href: "/patient/dashboard", icon: LayoutDashboard },
          { name: "My Transfusions", href: "/patient/transfusions", icon: Activity },
          { name: "Hospitals", href: "/patient/hospitals", icon: Hospital },
          { name: "Expense Approvals", href: "/patient/expenses", icon: Wallet },
          { name: "My Wallet", href: "/patient/wallet", icon: Wallet },
          { name: "Notifications", href: "/patient/notifications", icon: Bell },
        ];
      case "donor":
        return [
          { name: "Dashboard", href: "/donor/dashboard", icon: LayoutDashboard },
          { name: "Donation Requests", href: "/donor/requests", icon: HeartHandshake },
          { name: "Donation History", href: "/donor/donations", icon: CheckCircle },
          { name: "Rewards Center", href: "/donor/rewards", icon: Award },
          { name: "My Wallet", href: "/donor/wallet", icon: Wallet },
          { name: "Notifications", href: "/donor/notifications", icon: Bell },
          { name: "Profile Settings", href: "/donor/profile", icon: Settings },
        ];
      case "coordinator":
        return [
          { name: "Dashboard", href: "/coordinator/dashboard", icon: LayoutDashboard },
          { name: "Scheduling Center", href: "/coordinator/scheduling", icon: Calendar },
          { name: "Emergency Command", href: "/coordinator/emergency", icon: Flame },
          { name: "Notifications", href: "/coordinator/notifications", icon: Bell },
        ];
      case "hospital":
        return [
          { name: "Dashboard", href: "/hospital/dashboard", icon: LayoutDashboard },
          { name: "Daily Schedule", href: "/hospital/schedule", icon: Calendar },
          { name: "Capacity Controls", href: "/hospital/capacity", icon: Hospital },
          { name: "Notifications", href: "/hospital/notifications", icon: Bell },
        ];
      case "admin":
        return [
          { name: "Overview Dashboard", href: "/admin/dashboard", icon: LayoutDashboard },
          { name: "User Accounts", href: "/admin/users", icon: Users },
          { name: "Coordinator Approvals", href: "/admin/coordinators", icon: ShieldAlert },
          { name: "Incident Center", href: "/admin/incidents", icon: AlertTriangle },
        ];
      default:
        return [];
    }
  };

  const navLinks = getNavLinks();

  return (
    <aside
      className={cn(
        "flex h-screen w-64 flex-col border-r border-zinc-200 bg-white px-4 py-6 dark:border-zinc-800 dark:bg-zinc-950",
        className
      )}
    >
      {/* Brand Header */}
      <div className="mb-8 flex items-center gap-2 px-2">
        <div className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-accent-500 p-[1.5px] shadow-sm">
          <div className="flex h-full w-full items-center justify-center rounded-full bg-zinc-900 text-xs font-black tracking-tighter text-white dark:bg-black">
            <span className="text-brand-400">V</span>
            <span className="text-accent-500">C</span>
          </div>
        </div>
        <div>
          <h1 className="text-sm font-bold tracking-tight text-zinc-900 dark:text-white">
            VeinConnect
          </h1>
          <p className="text-[10px] font-semibold text-brand-500 dark:text-brand-400">Care Coordination</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 space-y-1">
        {navLinks.map((link) => {
          const Icon = link.icon;
          const isActive = pathname.startsWith(link.href);
          return (
            <Link
              key={link.name}
              href={link.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-brand-50 text-brand-600 dark:bg-brand-950/30 dark:text-brand-500"
                  : "text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-900/50 dark:hover:text-white"
              )}
            >
              <Icon className="h-4 w-4" />
              {link.name}
            </Link>
          );
        })}
      </nav>

      {/* User Card & Logout */}
      <div className="border-t border-zinc-200 pt-4 dark:border-zinc-800">
        {user && (
          <div className="mb-4 flex items-center gap-3 px-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-zinc-100 font-semibold text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
              {user.email[0].toUpperCase()}
            </div>
            <div className="overflow-hidden">
              <p className="truncate text-xs font-semibold text-zinc-950 dark:text-white">
                {user.email}
              </p>
              <p className="text-[10px] font-medium capitalize text-zinc-500">
                {user.role}
              </p>
            </div>
          </div>
        )}
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-900/50 dark:hover:text-white"
        >
          <LogOut className="h-4 w-4 text-zinc-500" />
          Log Out
        </button>
      </div>
    </aside>
  );
}
