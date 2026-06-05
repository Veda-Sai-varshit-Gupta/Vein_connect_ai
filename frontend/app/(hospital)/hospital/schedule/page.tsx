"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../../../lib/api/client";
import { Calendar, Loader2, Clock, Droplets } from "lucide-react";
import { format, parseISO, isToday } from "date-fns";

interface ScheduleItem {
  id: string;
  patient_name?: string;
  patient_blood_group?: string;
  donor_name?: string;
  scheduled_date: string;
  status: string;
  urgency_level: string;
  is_completion_initiated?: boolean;
  coordinator?: {
    id: string;
    name: string;
    phone: string;
    organization: string;
    assigned_region: string;
  } | null;
}

const STATUS_STYLES: Record<string, string> = {
  scheduled: "bg-emerald-100 text-emerald-700",
  in_progress: "bg-amber-100 text-amber-700",
  completed: "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400",
  cancelled: "bg-red-100 text-red-500",
};

export default function HospitalSchedulePage() {
  const [schedule, setSchedule] = useState<ScheduleItem[]>([]);
  const [pendingRuns, setPendingRuns] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hospitalId, setHospitalId] = useState<string | null>(null);

  const fetchScheduleAndPending = async (id: string) => {
    try {
      const [schRes, pendRes] = await Promise.all([
        apiClient.get(`/hospitals/${id}/schedule`),
        apiClient.get(`/hospitals/${id}/pending-slots`),
      ]);
      setSchedule(Array.isArray(schRes.data) ? schRes.data : []);
      setPendingRuns(Array.isArray(pendRes.data) ? pendRes.data : []);
    } catch (err) {
      console.warn("Failed to load schedule data: ", err);
      setSchedule([]);
      setPendingRuns([]);
    }
  };

  useEffect(() => {
    const fetch = async () => {
      try {
        const meRes = await apiClient.get("/hospitals/me");
        const id = meRes.data?.id;
        setHospitalId(id);
        if (id) {
          await fetchScheduleAndPending(id);
        } else {
          setSchedule([]);
          setPendingRuns([]);
        }
      } catch {
        setSchedule([]);
        setPendingRuns([]);
      } finally {
        setIsLoading(false);
      }
    };
    fetch();
  }, []);

  const handleConfirmSlot = async (transfusionId: string, confirm: boolean) => {
    try {
      await apiClient.post("/confirmations/confirm", {
        transfusion_id: transfusionId,
        is_confirmed: confirm,
        rejection_reason: confirm ? null : "Declined due to bed unavailability",
      });
      if (hospitalId) {
        await fetchScheduleAndPending(hospitalId);
      }
    } catch (err) {
      console.error("Action error: ", err);
      setPendingRuns((prev) => prev.filter((r) => r.id !== transfusionId));
    }
  };

  const markComplete = async (id: string) => {
    try {
      await apiClient.post(`/transfusions/${id}/complete`, { actual_date: new Date().toISOString(), notes: "" });
    } catch {}
    setSchedule((prev) => prev.map((s) => (s.id === id ? { ...s, is_completion_initiated: true } : s)));
  };

  if (isLoading) return <div className="flex h-[80vh] items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-brand-500" /></div>;

  const today = format(new Date(), "EEEE, dd MMMM yyyy");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">Daily Schedule</h1>
          <p className="text-xs text-zinc-500 mt-0.5">{today}</p>
        </div>
        <div className="flex items-center gap-2 rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 dark:border-zinc-800 dark:bg-zinc-900">
          <Calendar className="h-4 w-4 text-brand-500" />
          <span className="text-xs font-bold text-zinc-700 dark:text-zinc-300">{schedule.length} Transfusions Today</span>
        </div>
      </div>

      {/* Pending Slot Confirmations */}
      {pendingRuns.length > 0 && (
        <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900 space-y-3 shadow-sm animate-in fade-in duration-200">
          <h3 className="text-xs font-bold text-zinc-900 dark:text-white border-b pb-2 dark:border-zinc-800 flex items-center gap-2">
            <Clock className="h-4 w-4 text-brand-500" />
            Pending Slot Confirmations
          </h3>
          <div className="space-y-2">
            {pendingRuns.map((run) => (
              <div
                key={run.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between rounded-lg border border-zinc-100 bg-zinc-50/50 p-4 dark:border-zinc-800 dark:bg-zinc-950/20 gap-3"
              >
                <div>
                  <p className="text-xs font-bold text-zinc-800 dark:text-zinc-200">
                    Slot Request: Run #{run.id} ({(run.patient_blood_group || run.patient?.blood_group || "—")})
                  </p>
                  <p className="text-[10px] text-zinc-500 mt-0.5">
                    Patient: {run.patient_name || run.patient?.name || "Patient"} • Date: {run.scheduled_date ? format(parseISO(run.scheduled_date), "PPP p") : "—"}
                  </p>
                </div>
                <div className="flex items-center gap-2 self-end sm:self-auto">
                  <button
                    onClick={() => handleConfirmSlot(run.id, false)}
                    className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-bold text-red-600 bg-white hover:bg-red-50 dark:border-red-900/30 dark:bg-zinc-900 dark:hover:bg-red-950/20 transition-colors"
                  >
                    Reject Slot
                  </button>
                  <button
                    onClick={() => handleConfirmSlot(run.id, true)}
                    className="rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-bold text-white hover:bg-emerald-600 dark:bg-emerald-600 dark:hover:bg-emerald-700 transition-colors"
                  >
                    Approve Slot
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {schedule.length > 0 ? (
        <div className="space-y-3">
          {schedule.map((item) => (
            <div key={item.id} className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900 flex items-center gap-4">
              <div className="text-center shrink-0 w-16">
                <p className="text-lg font-black text-zinc-900 dark:text-white">{item.scheduled_date ? format(parseISO(item.scheduled_date), "hh:mm") : "—"}</p>
                <p className="text-[10px] text-zinc-400">{item.scheduled_date ? format(parseISO(item.scheduled_date), "a") : ""}</p>
              </div>
              <div className="h-12 w-px bg-zinc-100 dark:bg-zinc-800 shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-bold text-zinc-900 dark:text-white">{item.patient_name || "Patient"}</p>
                  {item.patient_blood_group && (
                    <span className="rounded bg-red-50 px-1.5 py-0.5 text-[10px] font-black text-red-600">{item.patient_blood_group}</span>
                  )}
                  <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${item.urgency_level === "urgent" ? "bg-amber-100 text-amber-700" : "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400"}`}>{item.urgency_level}</span>
                </div>
                <div className="flex items-center gap-4 mt-1 text-xs text-zinc-500 flex-wrap">
                  <span className="flex items-center gap-1">
                    <Droplets className="h-3 w-3 text-brand-500" /> Donor: {item.donor_name || "TBD"}
                    {(item as any).donor_medical_clearance_url && (
                      <span className="text-[10px] text-zinc-400">
                        (
                        <a
                          href={(item as any).donor_medical_clearance_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[10px] font-bold text-brand-500 hover:underline inline-flex items-center"
                        >
                          View clearance
                        </a>
                        )
                      </span>
                    )}
                  </span>
                  {item.coordinator && (
                    <span className="flex items-center gap-1">
                      👤 Coord: {item.coordinator.name} (<a href={`tel:${item.coordinator.phone}`} className="text-brand-500 font-bold hover:underline">{item.coordinator.phone}</a>)
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className={`rounded-full px-2.5 py-1 text-[10px] font-bold ${STATUS_STYLES[item.status] || "bg-zinc-100 text-zinc-600"}`}>
                  {item.status.replace(/_/g, " ")}
                </span>
                {item.status === "in_progress" && (
                  item.is_completion_initiated ? (
                    <span className="rounded-full bg-amber-50 px-2.5 py-1 text-[10px] font-bold text-amber-600 dark:bg-amber-950/20 dark:text-amber-400">
                      Awaiting Consensus
                    </span>
                  ) : (
                    <button
                      onClick={() => markComplete(item.id)}
                      className="rounded-lg bg-brand-500 px-3 py-1.5 text-[10px] font-bold text-white hover:bg-brand-600 transition-colors"
                    >
                      Mark Complete
                    </button>
                  )
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-zinc-300 p-16 text-center dark:border-zinc-700">
          <Calendar className="h-10 w-10 text-zinc-300 dark:text-zinc-700 mx-auto mb-3" />
          <p className="text-sm text-zinc-500">No transfusions scheduled today</p>
        </div>
      )}
    </div>
  );
}
