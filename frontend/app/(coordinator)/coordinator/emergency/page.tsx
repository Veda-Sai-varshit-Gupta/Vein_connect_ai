"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../../../lib/api/client";
import { AlertTriangle, Loader2, Clock, Zap, Users, Phone } from "lucide-react";
import { format, parseISO, differenceInMinutes } from "date-fns";

interface Emergency {
  id: string;
  patient_id: string;
  hospital_id?: string;
  status: string;
  urgency_level: string;
  is_emergency: boolean;
  emergency_reason?: string;
  predicted_date: string;
  created_at: string;
}

export default function CoordinatorEmergencyPage() {
  const [emergencies, setEmergencies] = useState<Emergency[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [emergencyDonors, setEmergencyDonors] = useState<Record<string, any[]>>({});
  const [loadingDonors, setLoadingDonors] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await apiClient.get("/transfusions/emergency");
        const data = res.data;
        setEmergencies(Array.isArray(data) ? data : []);
      } catch {
        setEmergencies([]);
      } finally {
        setIsLoading(false);
      }
    };
    fetch();
  }, []);

  const findDonors = async (transfusionId: string) => {
    setLoadingDonors((prev) => ({ ...prev, [transfusionId]: true }));
    try {
      const res = await apiClient.get(`/emergency/${transfusionId}/donors`);
      setEmergencyDonors((prev) => ({ ...prev, [transfusionId]: res.data || [] }));
    } catch (err) {
      console.error("Failed to load emergency donors: ", err);
      setEmergencyDonors((prev) => ({
        ...prev,
        [transfusionId]: [],
      }));
    } finally {
      setLoadingDonors((prev) => ({ ...prev, [transfusionId]: false }));
    }
  };

  if (isLoading) return <div className="flex h-[80vh] items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-brand-500" /></div>;

  const elapsed = (created_at: string) => {
    const mins = differenceInMinutes(new Date(), parseISO(created_at));
    if (mins < 60) return `${mins}m ago`;
    return `${Math.floor(mins / 60)}h ${mins % 60}m ago`;
  };

  return (
    <div className="space-y-6">
      {/* Alert Banner */}
      {emergencies.length > 0 && (
        <div className="flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 px-5 py-4 dark:border-red-900/30 dark:bg-red-950/20 animate-pulse">
          <Zap className="h-5 w-5 text-red-500 shrink-0" />
          <div>
            <p className="text-sm font-black text-red-700 dark:text-red-400">
              {emergencies.length} ACTIVE EMERGENCY
              {emergencies.length > 1 ? " CASES" : ""}
            </p>
            <p className="text-xs text-red-500 mt-0.5">Immediate action required. Response window: 30 minutes.</p>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">Emergency Command</h1>
          <p className="text-xs text-zinc-500 mt-0.5">Real-time emergency coordination center.</p>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-bold ${emergencies.length > 0 ? "bg-red-100 text-red-700" : "bg-emerald-100 text-emerald-700"}`}>
          {emergencies.length > 0 ? `${emergencies.length} Active` : "All Clear ✓"}
        </span>
      </div>

      {emergencies.length > 0 ? (
        <div className="space-y-4">
          {emergencies.map((e) => (
            <div key={e.id} className="rounded-xl border-2 border-red-200 bg-white p-5 dark:border-red-900/30 dark:bg-zinc-900">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-100 dark:bg-red-950/30">
                    <AlertTriangle className="h-5 w-5 text-red-500" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-black text-red-600">EMERGENCY</p>
                      <span className="font-mono text-xs font-bold text-zinc-400">#{String(e.id).slice(0, 18)}</span>
                    </div>
                    <p className="text-xs text-zinc-500 mt-0.5">{e.emergency_reason || "Emergency transfusion required"}</p>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-xs font-bold text-red-500 flex items-center gap-1">
                    <Clock className="h-3 w-3" /> {elapsed(e.created_at)}
                  </p>
                  <p className="text-[10px] text-zinc-400 mt-0.5">Target: {format(parseISO(e.predicted_date), "PPp")}</p>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 border-t border-zinc-100 dark:border-zinc-800 pt-4">
                <div className="rounded-lg bg-zinc-50 dark:bg-zinc-800 px-3 py-2 text-xs">
                  <p className="text-zinc-400 text-[10px] font-bold uppercase">Status</p>
                  <p className="font-bold text-zinc-900 dark:text-white capitalize mt-0.5">{e.status.replace(/_/g, " ")}</p>
                </div>
                <div className="rounded-lg bg-zinc-50 dark:bg-zinc-800 px-3 py-2 text-xs">
                  <p className="text-zinc-400 text-[10px] font-bold uppercase">Response SLA</p>
                  <p className="font-bold text-red-500 mt-0.5">30 minutes</p>
                </div>
              </div>

              <div className="mt-4">
                <button
                  onClick={() => findDonors(e.id)}
                  disabled={loadingDonors[e.id]}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-red-500 py-2.5 text-xs font-bold text-white hover:bg-red-600 transition-colors disabled:opacity-50"
                >
                  {loadingDonors[e.id] ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      Querying matching candidates...
                    </>
                  ) : (
                    <>
                      <Users className="h-3.5 w-3.5" /> Find Emergency Donors
                    </>
                  )}
                </button>
              </div>

              {/* Priority Emergency Donors List */}
              {emergencyDonors[e.id] && (
                <div className="mt-4 border-t border-zinc-100 dark:border-zinc-800 pt-4 space-y-2">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">
                    AI Prioritized Emergency Donors
                  </p>
                  <div className="space-y-1.5">
                    {emergencyDonors[e.id].map((donor: any) => (
                      <div
                        key={donor.donor_id || donor.donor_name}
                        className="flex items-center justify-between rounded-lg border border-zinc-100 bg-zinc-50/50 p-2.5 dark:border-zinc-800 dark:bg-zinc-950/20 text-xs"
                      >
                        <div>
                          <div className="flex items-center gap-1.5 font-bold text-zinc-900 dark:text-white">
                            <span>#{donor.rank} {donor.donor_name}</span>
                            <span className="rounded bg-red-100 px-1 py-0.2 text-[8px] font-bold text-red-700 dark:bg-red-950/40 dark:text-red-400">
                              {donor.blood_group}
                            </span>
                          </div>
                          <p className="text-[10px] text-zinc-500 mt-0.5">
                            Proximity: {donor.distance_km} km away • Match score: {donor.emergency_score}%
                          </p>
                        </div>
                        <div className="text-right">
                          <a
                            href={`tel:${donor.phone}`}
                            className="inline-flex items-center gap-1 rounded bg-zinc-100 px-2 py-1 text-[11px] font-black text-brand-500 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-brand-400 dark:hover:bg-zinc-700 transition-colors"
                          >
                            <Phone className="h-3 w-3" /> Call {donor.phone}
                          </a>
                        </div>
                      </div>
                    ))}
                    {emergencyDonors[e.id].length === 0 && (
                      <p className="text-[11px] text-zinc-500">No compatible available donors found in region.</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-zinc-300 p-16 text-center dark:border-zinc-700">
          <AlertTriangle className="h-10 w-10 text-zinc-300 dark:text-zinc-700 mx-auto mb-3" />
          <p className="text-sm font-medium text-emerald-600">No active emergencies</p>
          <p className="text-xs text-zinc-400 mt-1">All patients are currently stable.</p>
        </div>
      )}
    </div>
  );
}
