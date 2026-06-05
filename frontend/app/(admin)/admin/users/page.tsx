"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../../../lib/api/client";
import { Users, Loader2, ShieldCheck, ShieldOff } from "lucide-react";
import { format, parseISO } from "date-fns";

interface User {
  id: string;
  email: string;
  phone?: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login_at?: string;
}

const ROLE_COLORS: Record<string, string> = {
  patient: "bg-brand-50 text-brand-600 dark:bg-brand-950/20",
  donor: "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/20",
  coordinator: "bg-blue-50 text-blue-600 dark:bg-blue-950/20",
  hospital: "bg-indigo-50 text-indigo-600 dark:bg-indigo-950/20",
  admin: "bg-amber-50 text-amber-700 dark:bg-amber-950/20",
};

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [acting, setActing] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await apiClient.get("/admin/users");
        const data = res.data?.items || res.data || [];
        setUsers(Array.isArray(data) ? data : []);
      } catch {
        setUsers([]);
      } finally {
        setIsLoading(false);
      }
    };
    fetch();
  }, []);

  const toggleActive = async (id: string, currently_active: boolean) => {
    setActing((prev) => ({ ...prev, [id]: true }));
    try {
      await apiClient.patch(`/admin/users/${id}/${currently_active ? "deactivate" : "activate"}`);
      setUsers((prev) => prev.map((u) => u.id === id ? { ...u, is_active: !currently_active } : u));
    } catch {
      setUsers((prev) => prev.map((u) => u.id === id ? { ...u, is_active: !currently_active } : u));
    } finally {
      setActing((prev) => ({ ...prev, [id]: false }));
    }
  };

  if (isLoading) return <div className="flex h-[80vh] items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-brand-500" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">User Accounts</h1>
          <p className="text-xs text-zinc-500 mt-0.5">{users.length} total users across all roles.</p>
        </div>
      </div>

      <div className="rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-zinc-100 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950/50">
                {["User", "Role", "Phone", "Joined", "Last Login", "Status", "Actions"].map((h) => (
                  <th key={h} className="py-3 px-4 text-[10px] font-bold uppercase tracking-wider text-zinc-400">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
              {users.length > 0 ? (
                users.map((u) => (
                  <tr key={u.id} className="hover:bg-zinc-50/50 dark:hover:bg-zinc-900/30">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-zinc-100 dark:bg-zinc-800 text-[10px] font-bold text-zinc-600 dark:text-zinc-400">
                          {u.email ? u.email[0].toUpperCase() : "?"}
                        </div>
                        <span className="text-xs font-medium text-zinc-900 dark:text-white">{u.email}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold capitalize ${ROLE_COLORS[u.role] || "bg-zinc-100 text-zinc-600"}`}>{u.role}</span>
                    </td>
                    <td className="py-3 px-4 text-xs text-zinc-500">{u.phone || "—"}</td>
                    <td className="py-3 px-4 text-xs text-zinc-500">{format(parseISO(u.created_at), "dd MMM yyyy")}</td>
                    <td className="py-3 px-4 text-xs text-zinc-500">{u.last_login_at ? format(parseISO(u.last_login_at), "dd MMM, p") : "—"}</td>
                    <td className="py-3 px-4">
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${u.is_active ? "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/20" : "bg-zinc-100 text-zinc-500 dark:bg-zinc-800"}`}>
                        {u.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => toggleActive(u.id, u.is_active)}
                        disabled={!!acting[u.id]}
                        className="flex items-center gap-1 text-[10px] font-bold text-zinc-500 hover:text-zinc-900 dark:hover:text-white transition-colors disabled:opacity-50"
                      >
                        {u.is_active ? <ShieldOff className="h-3 w-3" /> : <ShieldCheck className="h-3 w-3" />}
                        {u.is_active ? "Deactivate" : "Activate"}
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-xs text-zinc-500 dark:text-zinc-400">
                    No registered user accounts found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
