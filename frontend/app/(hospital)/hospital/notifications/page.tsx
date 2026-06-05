"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../../../lib/api/client";
import { Bell, Hospital, Calendar, CheckCircle, Loader2 } from "lucide-react";
import { format, parseISO } from "date-fns";

interface Notification {
  id: string;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
}

export default function HospitalNotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await apiClient.get("/notifications");
        const data = res.data?.items || res.data || [];
        setNotifications(Array.isArray(data) ? data : []);
      } catch {
        setNotifications([]);
      } finally {
        setIsLoading(false);
      }
    };
    fetch();
  }, []);

  const markRead = async (id: string) => {
    try { await apiClient.patch(`/notifications/${id}/read`); } catch {}
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
  };

  const markAllRead = async () => {
    try { await apiClient.patch("/notifications/read-all"); } catch {}
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
  };

  if (isLoading) return <div className="flex h-[80vh] items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-brand-500" /></div>;

  const unread = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="space-y-5 max-w-xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">Notifications</h1>
          <p className="text-xs text-zinc-500 mt-0.5">{unread > 0 ? `${unread} unread` : "All caught up!"}</p>
        </div>
        {unread > 0 && <button onClick={markAllRead} className="text-xs font-semibold text-brand-500 hover:text-brand-600">Mark all read</button>}
      </div>
      <div className="rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900 overflow-hidden">
        {notifications.length > 0 ? (
          <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {notifications.map((n) => (
              <div key={n.id} onClick={() => !n.is_read && markRead(n.id)} className={`flex items-start gap-3 px-4 py-4 cursor-pointer transition-colors hover:bg-zinc-50 dark:hover:bg-zinc-900/50 ${!n.is_read ? "bg-brand-50/30 dark:bg-brand-950/10" : ""}`}>
                <div className="mt-0.5">
                  {n.type === "scheduling" ? <Calendar className="h-4 w-4 text-brand-500" /> : n.type === "capacity" ? <Hospital className="h-4 w-4 text-amber-500" /> : <CheckCircle className="h-4 w-4 text-emerald-500" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className={`text-xs font-bold ${!n.is_read ? "text-zinc-900 dark:text-white" : "text-zinc-600 dark:text-zinc-400"}`}>{n.title}</p>
                    {!n.is_read && <span className="h-2 w-2 rounded-full bg-brand-500 shrink-0" />}
                  </div>
                  <p className="text-[11px] text-zinc-500 mt-0.5 leading-relaxed">{n.message}</p>
                  <p className="text-[10px] text-zinc-400 mt-1">{format(parseISO(n.created_at), "PPp")}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-16 text-center">
            <Bell className="h-10 w-10 text-zinc-300 mx-auto mb-3 dark:text-zinc-700" />
            <p className="text-sm text-zinc-500">No notifications</p>
          </div>
        )}
      </div>
    </div>
  );
}
