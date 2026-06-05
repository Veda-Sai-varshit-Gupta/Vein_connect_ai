"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../../../lib/api/client";
import { ShieldAlert, Loader2, CheckCircle, XCircle, User, MapPin, Building } from "lucide-react";
import { format, parseISO } from "date-fns";

interface Coordinator {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  organization?: string;
  assigned_region?: string;
  approval_status: string;
  created_at: string;
}

export default function AdminCoordinatorsPage() {
  const [pending, setPending] = useState<Coordinator[]>([]);
  const [approved, setApproved] = useState<Coordinator[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [acting, setActing] = useState<Record<string, boolean>>({});
  const [done, setDone] = useState<Record<string, string>>({});

  useEffect(() => {
    const fetch = async () => {
      try {
        const [pRes, aRes] = await Promise.all([
          apiClient.get("/coordinators/pending"),
          apiClient.get("/coordinators"),
        ]);
        const pData = pRes.data || [];
        const aData = aRes.data?.items || aRes.data || [];
        setPending(Array.isArray(pData) ? pData : []);
        setApproved(Array.isArray(aData) ? aData.filter((c: any) => c.approval_status === "approved") : []);
      } catch {
        setPending([]);
        setApproved([]);
      } finally {
        setIsLoading(false);
      }
    };
    fetch();
  }, []);

  const act = async (id: string, action: "approve" | "reject") => {
    setActing((prev) => ({ ...prev, [id]: true }));
    try {
      if (action === "approve") {
        await apiClient.post(`/coordinators/${id}/approve`);
      } else {
        await apiClient.post(`/coordinators/${id}/reject`, { reason: "Application rejected by admin" });
      }
      setDone((prev) => ({ ...prev, [id]: action }));
    } catch {
      setDone((prev) => ({ ...prev, [id]: action }));
    } finally {
      setActing((prev) => ({ ...prev, [id]: false }));
    }
  };

  if (isLoading) return <div className="flex h-[80vh] items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-brand-500" /></div>;

  const activePending = pending.filter((p) => !done[p.id]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">Coordinator Management</h1>
        <p className="text-xs text-zinc-500 mt-0.5">{activePending.length} pending approval{activePending.length !== 1 ? "s" : ""}.</p>
      </div>

      {/* Pending Approvals */}
      <div>
        <h2 className="text-sm font-bold text-zinc-700 dark:text-zinc-300 mb-3 flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-amber-500" /> Pending Applications
        </h2>
        {activePending.length > 0 ? (
          <div className="space-y-3">
            {pending.map((c) => {
              if (done[c.id]) return (
                <div key={c.id} className={`rounded-xl border p-4 text-xs font-bold ${done[c.id] === "approve" ? "border-emerald-200 bg-emerald-50 text-emerald-600 dark:border-emerald-900/30 dark:bg-emerald-950/20" : "border-red-200 bg-red-50 text-red-600"}`}>
                  {done[c.id] === "approve" ? "✅ Approved — " : "❌ Rejected — "}{c.name}
                </div>
              );
              return (
                <div key={c.id} className="rounded-xl border border-amber-200 bg-white p-5 dark:border-amber-900/30 dark:bg-zinc-900">
                  <div className="flex items-start gap-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-amber-50 dark:bg-amber-950/20">
                      <User className="h-5 w-5 text-amber-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-bold text-zinc-900 dark:text-white">{c.name}</p>
                      <div className="flex flex-wrap gap-3 mt-1 text-xs text-zinc-500">
                        {c.email && <span>{c.email}</span>}
                        {c.organization && <span className="flex items-center gap-1"><Building className="h-3 w-3" /> {c.organization}</span>}
                        {c.assigned_region && <span className="flex items-center gap-1"><MapPin className="h-3 w-3" /> {c.assigned_region}</span>}
                      </div>
                      <p className="text-[10px] text-zinc-400 mt-1">Applied {format(parseISO(c.created_at), "dd MMM yyyy, p")}</p>
                    </div>
                  </div>
                  <div className="flex gap-2 mt-4">
                    <button onClick={() => act(c.id, "approve")} disabled={!!acting[c.id]} className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-brand-500 py-2 text-xs font-bold text-white hover:bg-brand-600 transition-colors disabled:opacity-60">
                      <CheckCircle className="h-3.5 w-3.5" /> Approve
                    </button>
                    <button onClick={() => act(c.id, "reject")} disabled={!!acting[c.id]} className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-zinc-200 bg-zinc-50 py-2 text-xs font-bold text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 transition-colors disabled:opacity-60">
                      <XCircle className="h-3.5 w-3.5" /> Reject
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-zinc-300 p-10 text-center dark:border-zinc-700">
            <CheckCircle className="h-8 w-8 text-emerald-400 mx-auto mb-2" />
            <p className="text-sm text-zinc-500">No pending applications</p>
          </div>
        )}
      </div>

      {/* Approved Coordinators */}
      <div>
        <h2 className="text-sm font-bold text-zinc-700 dark:text-zinc-300 mb-3">Active Coordinators</h2>
        <div className="rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900 divide-y divide-zinc-100 dark:divide-zinc-800">
          {approved.length > 0 ? (
            approved.map((c) => (
              <div key={c.id} className="flex items-center gap-4 px-4 py-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-50 dark:bg-brand-950/20 text-[10px] font-black text-brand-500">
                  {c.name ? c.name[0] : "?"}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-bold text-zinc-900 dark:text-white">{c.name}</p>
                  <p className="text-[10px] text-zinc-400">{c.organization} · {c.assigned_region}</p>
                </div>
                <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-[10px] font-bold text-emerald-600 dark:bg-emerald-950/20">Active</span>
              </div>
            ))
          ) : (
            <div className="p-6 text-center text-xs text-zinc-500">
              No active coordinators found.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
