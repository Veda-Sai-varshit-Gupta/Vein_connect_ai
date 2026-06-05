"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "../../../../lib/api/client";
import { Transfusion, TransfusionStatus } from "../../../../lib/types/common";
import { Activity, Flame, ShieldAlert, Award, ArrowRight, UserCheck, AlertTriangle, Loader2 } from "lucide-react";
import { format, parseISO } from "date-fns";

export default function CoordinatorDashboard() {
  const router = useRouter();
  const [activeCount, setActiveCount] = useState(0);
  const [pendingCount, setPendingCount] = useState(0);
  const [doneToday, setDoneToday] = useState(0);
  const [emergencyCount, setEmergencyCount] = useState(0);
  const [transfusions, setTransfusions] = useState<Transfusion[]>([]);
  const [unresponsiveDonors, setUnresponsiveDonors] = useState<any[]>([]);
  const [capacities, setCapacities] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, transfusionsRes, unresponsiveRes, capacityRes] = await Promise.all([
        apiClient.get("/coordinators/me/stats").catch(() => ({ data: { active_count: 0, pending_count: 0, done_today: 0, emergency_count: 0 } })),
        apiClient.get("/transfusions", { params: { status: "active" } }),
        apiClient.get("/coordinators/me/unresponsive-donors").catch(() => ({ data: [] })),
        apiClient.get("/coordinators/me/hospitals-capacity").catch(() => ({ data: [] })),
      ]);

      const stats = statsRes.data;
      setActiveCount(stats.active_count ?? 0);
      setPendingCount(stats.pending_count ?? 0);
      setDoneToday(stats.done_today ?? 0);
      setEmergencyCount(stats.emergency_count ?? 0);

      const transfusionList = Array.isArray(transfusionsRes.data)
        ? transfusionsRes.data
        : transfusionsRes.data?.items || [];
      setTransfusions(transfusionList);

      setUnresponsiveDonors(unresponsiveRes.data || []);
      setCapacities(capacityRes.data || []);
    } catch (err) {
      console.error("Failed to load coordinator dashboard data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const getUrgencyBadge = (urgency: string) => {
    switch (urgency) {
      case "emergency":
        return <span className="rounded bg-red-100 px-2 py-0.5 text-[9px] font-bold uppercase text-red-700">Emergency</span>;
      case "urgent":
        return <span className="rounded bg-amber-100 px-2 py-0.5 text-[9px] font-bold uppercase text-amber-700">Urgent</span>;
      default:
        return <span className="rounded bg-zinc-100 px-2 py-0.5 text-[9px] font-bold uppercase text-zinc-600">Routine</span>;
    }
  };

  const getStatusBadge = (status: TransfusionStatus) => {
    switch (status) {
      case "completed":
        return <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[9px] font-bold text-emerald-600">Completed</span>;
      case "donor_confirmed":
        return <span className="rounded-full bg-blue-50 px-2 py-0.5 text-[9px] font-bold text-blue-600">Donor Confirmed</span>;
      case "matching_donors":
        return <span className="rounded-full bg-amber-50 px-2 py-0.5 text-[9px] font-bold text-amber-600">AI Matching</span>;
      default:
        return <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-[9px] font-bold text-zinc-600">{status}</span>;
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
      </div>
    );
  }

  const hasAlerts = unresponsiveDonors.length > 0 || capacities.some(h => h.available_beds === 0);

  return (
    <div className="space-y-6">
      {/* Top title */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">
          Command Center — Regional Coordinator
        </h1>
        <p className="text-xs text-zinc-500">
          Coordinate match confirmations, hospital scheduling queues, and escalations.
        </p>
      </div>

      {/* KPI Stats Strip */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">Active Runs</span>
          <p className="text-xl font-bold text-zinc-900 dark:text-white">{activeCount}</p>
        </div>

        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">Pending Confirms</span>
          <p className="text-xl font-bold text-zinc-900 dark:text-white">{pendingCount}</p>
        </div>

        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">Done Today</span>
          <p className="text-xl font-bold text-zinc-900 dark:text-white">{doneToday}</p>
        </div>

        <div className="rounded-xl border border-red-200 bg-red-50 p-4 dark:border-red-950 dark:bg-red-950/20">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-red-600 dark:text-red-400">Emergencies</span>
            <Flame className="h-4 w-4 animate-bounce text-red-500" />
          </div>
          <p className="text-xl font-bold text-red-700 dark:text-red-400">{emergencyCount} Active</p>
        </div>
      </div>

      {/* Alert Feeds Panel */}
      {hasAlerts && (
        <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900 space-y-3">
          <h3 className="text-sm font-bold text-zinc-900 dark:text-white flex items-center gap-2">
            <AlertTriangle className="h-4.5 w-4.5 text-amber-500" />
            Workflow alerts requiring coordinator action
          </h3>
          
          <div className="space-y-2">
            {/* Unresponsive Donors Alerts */}
            {unresponsiveDonors.map((ud) => (
              <div key={ud.transfusion_id} className="flex items-center justify-between rounded-lg border border-amber-200 bg-amber-50/20 p-3.5 dark:border-amber-900/30">
                <div>
                  <p className="text-xs font-bold text-zinc-900 dark:text-white">
                    ⚠️ Run #{String(ud.transfusion_id).substring(0, 8)}: Donor unresponsive
                  </p>
                  <p className="text-[10px] text-zinc-500">
                    Patient: {ud.patient_name} • Scheduled: {ud.scheduled_date ? format(parseISO(ud.scheduled_date), "MMMM d") : "N/A"} • Donor: {ud.donor_name} hasn't confirmed in 6 hrs
                  </p>
                </div>
                <button 
                  onClick={() => router.push("/coordinator/scheduling?tab=unresponsive")}
                  className="rounded bg-amber-500 px-3 py-1.5 text-[10px] font-bold text-white transition-colors hover:bg-amber-600"
                >
                  Select Alternate Donor
                </button>
              </div>
            ))}

            {/* Capacity Overflow Alerts */}
            {capacities.filter(h => h.available_beds === 0).map((h) => (
              <div key={h.id} className="flex items-center justify-between rounded-lg border border-red-200 bg-red-50/10 p-3.5 dark:border-red-900/20">
                <div>
                  <p className="text-xs font-bold text-zinc-900 dark:text-white">
                    ⚠️ Capacity Overflow Alert at {h.name}
                  </p>
                  <p className="text-[10px] text-zinc-500">
                    Hospital reports 100% bed occupancy ({h.occupied_beds}/{h.total_transfusion_beds} beds occupied)
                  </p>
                </div>
                <button 
                  onClick={() => router.push("/coordinator/scheduling?tab=hospitals")}
                  className="rounded bg-brand-500 px-3 py-1.5 text-[10px] font-bold text-white transition-colors hover:bg-brand-600"
                >
                  Route Alternate Hospital
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active Transfusion Coordination Table */}
      <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900 space-y-4">
        <h3 className="text-sm font-bold text-zinc-900 dark:text-white border-b pb-2 dark:border-zinc-800">
          All Active Transfusion Runs
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-zinc-100 text-[10px] font-bold uppercase tracking-wider text-zinc-400 dark:border-zinc-800">
                <th className="py-3 px-2">Run ID</th>
                <th className="py-3 px-2">Patient</th>
                <th className="py-3 px-2">Matched Donor</th>
                <th className="py-3 px-2">Status</th>
                <th className="py-3 px-2">Urgency</th>
                <th className="py-3 px-2">Next Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100 text-xs dark:divide-zinc-800">
              {transfusions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-zinc-500 dark:text-zinc-400">
                    No active transfusion runs found.
                  </td>
                </tr>
              ) : (
                transfusions.map((run) => (
                  <tr key={run.id} className="hover:bg-zinc-50/50 dark:hover:bg-zinc-900/30">
                    <td className="py-3 px-2 font-bold text-zinc-900 dark:text-white">{String(run.id).substring(0, 12)}</td>
                    <td className="py-3 px-2 font-medium text-zinc-800 dark:text-zinc-300">
                      {run.patient?.name} <span className="rounded bg-zinc-100 px-1.5 py-0.5 text-[9px] dark:bg-zinc-800">{run.patient?.blood_group}</span>
                    </td>
                    <td className="py-3 px-2 text-zinc-500">
                      {run.donor ? run.donor.name : "Unmatched"}
                    </td>
                    <td className="py-3 px-2">{getStatusBadge(run.status)}</td>
                    <td className="py-3 px-2">{getUrgencyBadge(run.urgency_level)}</td>
                    <td className="py-3 px-2">
                      <button 
                        onClick={() => router.push(`/coordinator/transfusions/${run.id}`)}
                        className="flex items-center gap-1 text-[10px] font-bold text-brand-500 hover:text-brand-600"
                      >
                        Manage Run
                        <ArrowRight className="h-3 w-3" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
