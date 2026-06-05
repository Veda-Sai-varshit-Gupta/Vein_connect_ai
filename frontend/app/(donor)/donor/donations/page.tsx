"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../../../lib/api/client";
import { CheckCircle2, Clock, Loader2 } from "lucide-react";
import { format, parseISO } from "date-fns";

interface Donation {
  id: string;
  transfusion_id: string;
  status: string;
  donated_at?: string;
  created_at: string;
  hospital_name?: string;
  patient_blood_group?: string;
  units?: number;
}

const STATUS_STYLES: Record<string, string> = {
  completed: "bg-emerald-100 text-emerald-700",
  cancelled: "bg-red-100 text-red-500",
  no_show: "bg-amber-100 text-amber-700",
  pending: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
};

export default function DonorDonationsPage() {
  const [donations, setDonations] = useState<Donation[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await apiClient.get("/donors/donations");
        const data = res.data;
        setDonations(Array.isArray(data) ? data : []);
      } catch {
        setDonations([]);
      } finally {
        setIsLoading(false);
      }
    };
    fetch();
  }, []);

  if (isLoading) return <div className="flex h-[80vh] items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-brand-500" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">Donation History</h1>
          <p className="text-xs text-zinc-500 mt-0.5">{donations.length} lifetime donation{donations.length !== 1 ? "s" : ""}. Thank you! 🩸</p>
        </div>
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-2 dark:border-emerald-900/30 dark:bg-emerald-950/20">
          <p className="text-xs font-bold text-emerald-600">Total Donated</p>
          <p className="text-xl font-black text-emerald-700">{donations.filter((d) => d.status === "completed").length} <span className="text-xs font-normal">units</span></p>
        </div>
      </div>

      <div className="rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900 overflow-hidden">
        {donations.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-zinc-100 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950/50">
                  <th className="py-3 px-4 text-[10px] font-bold uppercase tracking-wider text-zinc-400">Run ID</th>
                  <th className="py-3 px-4 text-[10px] font-bold uppercase tracking-wider text-zinc-400">Date</th>
                  <th className="py-3 px-4 text-[10px] font-bold uppercase tracking-wider text-zinc-400">Hospital</th>
                  <th className="py-3 px-4 text-[10px] font-bold uppercase tracking-wider text-zinc-400">Blood Group</th>
                  <th className="py-3 px-4 text-[10px] font-bold uppercase tracking-wider text-zinc-400">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {donations.map((d) => (
                  <tr key={d.id} className="hover:bg-zinc-50/50 dark:hover:bg-zinc-900/30">
                    <td className="py-3 px-4 text-xs font-bold text-zinc-900 dark:text-white font-mono">#{String(d.transfusion_id).slice(0, 14)}</td>
                    <td className="py-3 px-4 text-xs text-zinc-700 dark:text-zinc-300">
                      <div className="flex items-center gap-1.5">
                        <Clock className="h-3.5 w-3.5 text-zinc-400" />
                        {d.donated_at ? format(parseISO(d.donated_at), "dd MMM yyyy") : "—"}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-xs text-zinc-600 dark:text-zinc-400">{d.hospital_name || "—"}</td>
                    <td className="py-3 px-4">
                      {d.patient_blood_group && (
                        <span className="rounded bg-red-50 px-2 py-0.5 text-[10px] font-black text-red-600">{d.patient_blood_group}</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`flex items-center gap-1 w-fit rounded-full px-2.5 py-0.5 text-[10px] font-bold ${STATUS_STYLES[d.status] || ""}`}>
                        {d.status === "completed" && <CheckCircle2 className="h-3 w-3" />}
                        {d.status.replace(/_/g, " ")}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <CheckCircle2 className="h-10 w-10 text-zinc-300 dark:text-zinc-700 mb-3" />
            <p className="text-sm font-medium text-zinc-500">No donations yet</p>
          </div>
        )}
      </div>
    </div>
  );
}
