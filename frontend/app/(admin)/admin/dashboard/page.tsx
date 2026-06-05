"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../../../lib/api/client";
import { Users, Activity, Hospital, HeartHandshake, AlertTriangle, TrendingUp, Loader2, CheckCircle2 } from "lucide-react";

interface Stats {
  total_patients: number;
  total_donors: number;
  total_users: number;
  active_transfusions: number;
  total_hospitals?: number;
  completed_this_month?: number;
  emergencies_today?: number;
}



interface KPICardProps {
  label: string;
  value: number | string;
  icon: React.ElementType;
  color: string;
  bg: string;
  trend?: string;
}

function KPICard({ label, value, icon: Icon, color, bg, trend }: KPICardProps) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">{label}</p>
          <p className={`text-3xl font-black mt-2 ${color}`}>{typeof value === "number" ? value.toLocaleString() : value}</p>
          {trend && <p className="text-[10px] text-emerald-500 mt-1 font-medium">{trend}</p>}
        </div>
        <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${bg}`}>
          <Icon className={`h-5 w-5 ${color}`} />
        </div>
      </div>
    </div>
  );
}

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await apiClient.get("/admin/stats");
        setStats(res.data);
      } catch (err) {
        console.error("Failed to fetch admin stats:", err);
        setStats(null);
      } finally {
        setIsLoading(false);
      }
    };
    fetch();
  }, []);

  if (isLoading) return <div className="flex h-[80vh] items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-brand-500" /></div>;

  const s = stats;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">Admin Overview</h1>
        <p className="text-xs text-zinc-500 mt-0.5">Platform-wide health and KPIs.</p>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KPICard label="Total Patients" value={s?.total_patients ?? 0} icon={Users} color="text-brand-500" bg="bg-brand-50 dark:bg-brand-950/20" trend="↑ Live data" />
        <KPICard label="Total Donors" value={s?.total_donors ?? 0} icon={HeartHandshake} color="text-emerald-500" bg="bg-emerald-50 dark:bg-emerald-950/20" trend="↑ Live data" />
        <KPICard label="Active Runs" value={s?.active_transfusions ?? 0} icon={Activity} color="text-amber-500" bg="bg-amber-50 dark:bg-amber-950/20" />
        <KPICard label="Hospitals" value={s?.total_hospitals ?? 0} icon={Hospital} color="text-blue-500" bg="bg-blue-50 dark:bg-blue-950/20" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <KPICard label="Completed This Month" value={s?.completed_this_month ?? 0} icon={CheckCircle2} color="text-emerald-600" bg="bg-emerald-50 dark:bg-emerald-950/20" trend="↑ Live data" />
        <KPICard label="Emergencies Today" value={s?.emergencies_today ?? 0} icon={AlertTriangle} color="text-red-500" bg="bg-red-50 dark:bg-red-950/20" />
      </div>

      {/* Health Indicators */}
      <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
        <h2 className="text-sm font-bold text-zinc-900 dark:text-white mb-4">Platform Health</h2>
        <div className="space-y-3">
          {[
            { label: "Backend API", status: "Operational", color: "text-emerald-600 bg-emerald-50" },
            { label: "Database", status: "Connected", color: "text-emerald-600 bg-emerald-50" },
            { label: "AI Matching Engine", status: "Active", color: "text-emerald-600 bg-emerald-50" },
            { label: "Notification Service", status: "Running", color: "text-emerald-600 bg-emerald-50" },
          ].map((item) => (
            <div key={item.label} className="flex items-center justify-between">
              <p className="text-xs font-medium text-zinc-700 dark:text-zinc-300">{item.label}</p>
              <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${item.color} dark:bg-emerald-950/20 dark:text-emerald-400`}>
                ● {item.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
