"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../../../lib/api/client";
import { AlertTriangle, Loader2, CheckCircle } from "lucide-react";
import { format, parseISO } from "date-fns";

interface Incident {
  id: string;
  type: string;
  severity: string;
  description: string;
  status: string;
  created_at: string;
  resolved_at?: string;
}

const SEVERITY_STYLES: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high: "bg-orange-100 text-orange-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
};

export default function AdminIncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await apiClient.get("/admin/incidents");
        const data = res.data?.items || res.data || [];
        setIncidents(Array.isArray(data) ? data : []);
      } catch {
        setIncidents([]);
      } finally {
        setIsLoading(false);
      }
    };
    fetch();
  }, []);

  if (isLoading) return <div className="flex h-[80vh] items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-brand-500" /></div>;

  const open = incidents.filter((i) => i.status === "open").length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">Incident Center</h1>
          <p className="text-xs text-zinc-500 mt-0.5">{open} open incident{open !== 1 ? "s" : ""} requiring attention.</p>
        </div>
        {open > 0 && (
          <span className="flex items-center gap-1.5 rounded-full bg-red-100 px-3 py-1.5 text-xs font-bold text-red-600">
            <AlertTriangle className="h-3.5 w-3.5" /> {open} Open
          </span>
        )}
      </div>

      <div className="space-y-3">
        {incidents.length > 0 ? (
          incidents.map((inc) => (
            <div key={inc.id} className={`rounded-xl border bg-white p-5 dark:bg-zinc-900 ${inc.status === "open" ? "border-zinc-200 dark:border-zinc-800" : "border-zinc-100 opacity-70 dark:border-zinc-800"}`}>
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${inc.status === "resolved" ? "bg-zinc-100 dark:bg-zinc-800" : "bg-red-50 dark:bg-red-950/20"}`}>
                    {inc.status === "resolved"
                      ? <CheckCircle className="h-4 w-4 text-zinc-400" />
                      : <AlertTriangle className="h-4 w-4 text-red-500" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="text-xs font-bold text-zinc-900 dark:text-white capitalize">{inc.type.replace(/_/g, " ")}</p>
                      <span className={`rounded-full px-2 py-0.5 text-[9px] font-black uppercase ${SEVERITY_STYLES[inc.severity]}`}>{inc.severity}</span>
                      <span className={`rounded-full px-2 py-0.5 text-[9px] font-bold ${inc.status === "open" ? "bg-amber-50 text-amber-600" : "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/20"}`}>
                        {inc.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-zinc-500 mt-1.5 leading-relaxed">{inc.description}</p>
                    <p className="text-[10px] text-zinc-400 mt-1">{format(parseISO(inc.created_at), "dd MMM yyyy, p")}</p>
                    {inc.resolved_at && (
                      <p className="text-[10px] text-emerald-500 mt-0.5">Resolved: {format(parseISO(inc.resolved_at), "dd MMM yyyy, p")}</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="rounded-xl border border-dashed border-zinc-200 bg-white p-10 text-center dark:border-zinc-800 dark:bg-zinc-900">
            <CheckCircle className="h-8 w-8 text-emerald-500 mx-auto mb-2" />
            <p className="text-sm text-zinc-500">No active incidents found.</p>
          </div>
        )}
      </div>
    </div>
  );
}
