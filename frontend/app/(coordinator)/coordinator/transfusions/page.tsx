"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiClient } from "../../../../lib/api/client";
import { Loader2, ArrowRight, Clock } from "lucide-react";
import { format, parseISO } from "date-fns";

const STATUS_STYLES: Record<string, string> = {
  predicted: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
  patient_confirmed: "bg-brand-50 text-brand-600",
  matching_donors: "bg-amber-100 text-amber-700",
  donor_confirmed: "bg-blue-50 text-blue-600",
  coordinator_confirmed: "bg-blue-100 text-blue-700",
  hospital_confirmed: "bg-indigo-100 text-indigo-700",
  scheduled: "bg-emerald-50 text-emerald-600",
  in_progress: "bg-amber-100 text-amber-800",
  completed: "bg-emerald-100 text-emerald-700",
  cancelled: "bg-red-50 text-red-600",
};

const MOCK: any[] = [
  { id: "VC-2026-0044", patient_id: "pat-9", status: "patient_confirmed", urgency_level: "urgent", scheduled_date: "2026-06-20T10:00:00", donor_id: null },
  { id: "VC-2026-0043", patient_id: "pat-14", status: "donor_confirmed", urgency_level: "routine", scheduled_date: "2026-06-22T09:00:00", donor_id: "d-2" },
  { id: "VC-2026-0042", patient_id: "pat-1", status: "scheduled", urgency_level: "urgent", scheduled_date: "2026-06-18T10:30:00", donor_id: "d-1" },
  { id: "VC-2026-0038", patient_id: "pat-1", status: "completed", urgency_level: "routine", scheduled_date: "2026-05-28T09:30:00", donor_id: "d-4" },
  { id: "VC-2026-0031", patient_id: "pat-5", status: "cancelled", urgency_level: "routine", scheduled_date: "2026-05-07T09:00:00", donor_id: null },
];

export default function CoordinatorTransfusionsPage() {
  const [transfusions, setTransfusions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await apiClient.get("/transfusions");
        const data = res.data?.items || res.data || [];
        setTransfusions(Array.isArray(data) && data.length > 0 ? data : MOCK);
      } catch {
        setTransfusions(MOCK);
      } finally {
        setIsLoading(false);
      }
    };
    fetch();
  }, []);

  if (isLoading) return <div className="flex h-[80vh] items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-brand-500" /></div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">All Transfusions</h1>
        <p className="text-xs text-zinc-500 mt-0.5">{transfusions.length} total runs across all patients.</p>
      </div>
      <div className="rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-zinc-100 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950/50">
                {["Run ID", "Scheduled", "Urgency", "Status", "Donor", ""].map((h) => (
                  <th key={h} className="py-3 px-4 text-[10px] font-bold uppercase tracking-wider text-zinc-400">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
              {transfusions.map((t) => (
                <tr key={t.id} className="hover:bg-zinc-50/50 dark:hover:bg-zinc-900/30">
                  <td className="py-3 px-4 font-mono text-xs font-bold text-zinc-900 dark:text-white">#{String(t.id).slice(0, 14)}</td>
                  <td className="py-3 px-4 text-xs text-zinc-700 dark:text-zinc-300">
                    <div className="flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5 text-zinc-400" />
                      {t.scheduled_date ? format(parseISO(t.scheduled_date), "dd MMM yyyy") : "—"}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${t.urgency_level === "urgent" ? "bg-amber-100 text-amber-700" : t.urgency_level === "emergency" ? "bg-red-100 text-red-700" : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"}`}>{t.urgency_level}</span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${STATUS_STYLES[t.status] || "bg-zinc-100 text-zinc-600"}`}>
                      {t.status?.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-xs text-zinc-500">{t.donor_id ? "Assigned" : "Pending"}</td>
                  <td className="py-3 px-4">
                    <Link href={`/coordinator/transfusions/${t.id}`} className="flex items-center gap-1 text-[10px] font-bold text-brand-500 hover:text-brand-600">
                      View <ArrowRight className="h-3 w-3" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
