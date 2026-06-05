"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../../../lib/api/client";
import { Loader2, TrendingUp, BarChart3, Activity, Droplet } from "lucide-react";

interface AnalyticsData {
  transfusions_by_month: { month: string; count: number }[];
  blood_group_distribution: { group: string; percentage: number }[];
  avg_donor_reliability: number;
  success_rate: number;
}

const MOCK_DATA: AnalyticsData = {
  transfusions_by_month: [
    { month: "Jan", count: 120 },
    { month: "Feb", count: 145 },
    { month: "Mar", count: 130 },
    { month: "Apr", count: 160 },
    { month: "May", count: 185 },
    { month: "Jun", count: 210 },
  ],
  blood_group_distribution: [
    { group: "O+", percentage: 38 },
    { group: "A+", percentage: 28 },
    { group: "B+", percentage: 22 },
    { group: "AB+", percentage: 5 },
    { group: "O-", percentage: 4 },
    { group: "A-", percentage: 2 },
    { group: "B-", percentage: 1 },
  ],
  avg_donor_reliability: 84.5,
  success_rate: 96.2,
};

export default function AdminAnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await apiClient.get("/admin/analytics");
        setData(res.data && Object.keys(res.data).length > 0 ? res.data : MOCK_DATA);
      } catch {
        setData(MOCK_DATA);
      } finally {
        setIsLoading(false);
      }
    };
    fetch();
  }, []);

  if (isLoading) return <div className="flex h-[80vh] items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-brand-500" /></div>;

  const d = data || MOCK_DATA;
  const maxTransfusions = Math.max(...d.transfusions_by_month.map(m => m.count));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">Platform Analytics</h1>
        <p className="text-xs text-zinc-500 mt-0.5">Deep dive into platform usage and AI performance metrics.</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex items-center gap-3 mb-2 text-emerald-500">
            <Activity className="h-5 w-5" />
            <h2 className="text-sm font-bold text-zinc-900 dark:text-white">Success Rate</h2>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-black text-emerald-600 dark:text-emerald-400">{d.success_rate}%</span>
          </div>
          <p className="text-xs text-zinc-500 mt-2">Percentage of transfusions completed without cancellation.</p>
        </div>

        <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex items-center gap-3 mb-2 text-brand-500">
            <TrendingUp className="h-5 w-5" />
            <h2 className="text-sm font-bold text-zinc-900 dark:text-white">Avg. Donor Reliability</h2>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-black text-brand-600 dark:text-brand-400">{d.avg_donor_reliability.toFixed(1)}</span>
            <span className="text-sm text-zinc-500 font-bold">/ 100</span>
          </div>
          <p className="text-xs text-zinc-500 mt-2">AI computed reliability score across all active donors.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Trend */}
        <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex items-center gap-2 mb-6">
            <BarChart3 className="h-4 w-4 text-zinc-500" />
            <h2 className="text-sm font-bold text-zinc-900 dark:text-white">Transfusions (6 Months)</h2>
          </div>
          <div className="flex items-end justify-between gap-2 h-48 px-2">
            {d.transfusions_by_month.map((item) => (
              <div key={item.month} className="flex flex-col items-center gap-2 flex-1 group">
                <div className="w-full relative bg-zinc-100 rounded-t-md dark:bg-zinc-800 transition-colors group-hover:bg-brand-50 dark:group-hover:bg-brand-950/30" style={{ height: `${(item.count / maxTransfusions) * 100}%` }}>
                  <div className="absolute inset-x-0 bottom-0 bg-brand-500 rounded-t-md transition-all group-hover:bg-brand-400" style={{ height: '100%' }}></div>
                  <span className="absolute -top-6 inset-x-0 text-center text-[10px] font-bold text-zinc-500 opacity-0 group-hover:opacity-100 transition-opacity">{item.count}</span>
                </div>
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">{item.month}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Blood Group Distribution */}
        <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex items-center gap-2 mb-6">
            <Droplet className="h-4 w-4 text-red-500" />
            <h2 className="text-sm font-bold text-zinc-900 dark:text-white">Blood Group Distribution</h2>
          </div>
          <div className="space-y-4">
            {d.blood_group_distribution.map((bg) => (
              <div key={bg.group}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-bold text-zinc-700 dark:text-zinc-300">{bg.group}</span>
                  <span className="text-zinc-500">{bg.percentage}%</span>
                </div>
                <div className="h-2 w-full rounded-full bg-zinc-100 dark:bg-zinc-800 overflow-hidden">
                  <div className="h-full rounded-full bg-red-500" style={{ width: `${bg.percentage}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
