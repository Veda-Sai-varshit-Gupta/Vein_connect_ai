"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "../../../../lib/api/client";
import { Donor, Transfusion, TransfusionStatus } from "../../../../lib/types/common";
import { Award, Heart, CheckCircle2, Clock, MapPin, Smile, Loader2 } from "lucide-react";
import { format, parseISO } from "date-fns";

export default function DonorDashboard() {
  const router = useRouter();
  const [donor, setDonor] = useState<Donor | null>(null);
  const [requests, setRequests] = useState<Transfusion[]>([]);
  const [history, setHistory] = useState<Transfusion[]>([]);
  const [rewardsSummary, setRewardsSummary] = useState<{ total_points: number; tier: string } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAvailable, setIsAvailable] = useState(true);
  const [pendingCompletions, setPendingCompletions] = useState<any[]>([]);

  const fetchDashboardData = async () => {
    try {
      // Fetch donor profile
      const response = await apiClient.get("/donors/me");
      if (!response.data) {
        router.push("/register/donor");
        return;
      }
      setDonor(response.data);
      setIsAvailable(response.data.is_available);

      // Fetch pending requests
      const reqsResponse = await apiClient.get("/transfusions/pending-donor");
      setRequests(reqsResponse.data);

      // Fetch history
      const histResponse = await apiClient.get("/donors/donations");
      setHistory(histResponse.data);

      // Fetch pending completions
      try {
        const compResponse = await apiClient.get("/confirmations/pending-completions");
        setPendingCompletions(compResponse.data);
      } catch (err) {
        console.warn("Failed to fetch pending completions: ", err);
      }

      // Fetch rewards summary
      try {
        const rewardsResponse = await apiClient.get("/rewards/me/summary");
        setRewardsSummary(rewardsResponse.data);
      } catch (err) {
        console.warn("Failed to fetch rewards summary: ", err);
      }
    } catch (err) {
      console.warn("Error loading donor dashboard: ", err);
      setDonor(null);
      setRequests([]);
      setHistory([]);
      setPendingCompletions([]);
      setRewardsSummary(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleToggleAvailability = async () => {
    try {
      const nextState = !isAvailable;
      // Connect to FastAPI availability change endpoint
      await apiClient.post("/donors/availability", { is_available: nextState });
      setIsAvailable(nextState);
    } catch (err) {
      console.error("Availability toggle failure: ", err);
      // Toggle locally for demo UI flow
      setIsAvailable(!isAvailable);
    }
  };

  const handleAction = async (transfusionId: string, isConfirm: boolean) => {
    try {
      if (isConfirm) {
        await apiClient.post("/confirmations/confirm", { transfusion_id: transfusionId });
      } else {
        await apiClient.post("/confirmations/reject", {
          transfusion_id: transfusionId,
          reason: "Declined by donor preference",
        });
      }
      fetchDashboardData();
    } catch (err) {
      console.error("Confirmation error: ", err);
      setRequests((prev) => prev.filter((r) => r.id !== transfusionId));
    }
  };

  return (
    <div className="space-y-6">
      {/* Alert Warning for missing medical clearance document */}
      {!isLoading && donor && !donor.medical_clearance_url && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 dark:border-red-900/30 dark:bg-red-950/20">
          <div className="flex gap-3">
            <div className="mt-0.5 text-red-650 dark:text-red-400">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div>
              <p className="text-xs font-bold text-red-800 dark:text-red-200">
                Please upload you medical clearance document, without that you are not eligible to donate your blood
              </p>
              <div className="mt-2">
                <button
                  onClick={() => router.push("/donor/profile")}
                  className="text-[10px] font-bold underline text-red-800 dark:text-red-200 hover:text-red-950 dark:hover:text-white"
                >
                  Upload Certificate Now &rarr;
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">
            Hello, {donor?.name} 🙌
          </h1>
          <p className="text-xs text-zinc-500">
            Track matching requests and availability settings.
          </p>
        </div>

        {/* Availability Toggle Switch */}
        <div className="flex items-center gap-3 rounded-lg border border-zinc-200 bg-white px-4 py-2 dark:border-zinc-800 dark:bg-zinc-900">
          <span className="text-xs font-bold text-zinc-700 dark:text-zinc-300">
            Available to Donate
          </span>
          <button
            onClick={handleToggleAvailability}
            className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors outline-none ${
              isAvailable ? "bg-emerald-500" : "bg-zinc-200 dark:bg-zinc-800"
            }`}
          >
            <span
              className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                isAvailable ? "translate-x-4.5" : "translate-x-1"
              }`}
            />
          </button>
        </div>
      </div>

      {/* KPI Stats Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {/* Reliability Score Card */}
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">
              Reliability Score
            </span>
            <Smile className="h-4.5 w-4.5 text-emerald-500" />
          </div>
          <div className="mt-2">
            <p className="text-lg font-bold text-zinc-900 dark:text-white">
              {donor?.reliability_score}/100
            </p>
            <div className="mt-1 h-1.5 w-full rounded-full bg-zinc-100 dark:bg-zinc-800 overflow-hidden">
              <div
                style={{ width: `${donor?.reliability_score}%` }}
                className="h-full bg-emerald-500 rounded-full"
              />
            </div>
          </div>
        </div>

        {/* Total Donations */}
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">
              Total Donations
            </span>
            <CheckCircle2 className="h-4.5 w-4.5 text-brand-500" />
          </div>
          <div className="mt-2">
            <p className="text-lg font-bold text-zinc-900 dark:text-white">
              {history.length} Matches
            </p>
            <p className="text-xs text-zinc-500 mt-0.5">Thank you for saving lives!</p>
          </div>
        </div>

        {/* Reward Points */}
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">
              Points balance
            </span>
            <Award className="h-4.5 w-4.5 text-brand-500" />
          </div>
          <div className="mt-2">
            <p className="text-lg font-bold text-zinc-900 dark:text-white">
              {(rewardsSummary?.total_points ?? 0).toLocaleString()} Pts
            </p>
            <p className="text-xs text-emerald-600 font-bold mt-0.5">
              🏆 {rewardsSummary?.tier || "Bronze"} Tier Active
            </p>
          </div>
        </div>
      </div>

      {/* Pending completion confirmations */}
      {pendingCompletions && pendingCompletions.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-sm font-bold text-zinc-900 dark:text-white border-b pb-2 dark:border-zinc-800 flex items-center gap-1.5">
            <CheckCircle2 className="h-4.5 w-4.5 text-emerald-500" />
            <span>Confirm Transfusion Completion</span>
          </h3>
          <div className="space-y-4">
            {pendingCompletions.map((comp) => (
              <div
                key={comp.id}
                className="rounded-xl border border-emerald-200 bg-emerald-50/20 p-4 dark:border-emerald-950/30 dark:bg-emerald-950/10 space-y-4 shadow-sm"
              >
                <div className="flex items-center justify-between border-b pb-2.5 dark:border-zinc-800">
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-emerald-100 px-2.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400">
                      Completed Procedure
                    </span>
                    <span className="text-[10px] font-medium text-zinc-500">
                      Date: {comp.scheduled_date ? format(parseISO(comp.scheduled_date), "PP") : ""}
                    </span>
                  </div>
                  <span className="text-xs font-semibold text-zinc-500">
                    Run #{String(comp.transfusion_id).slice(0, 8)}
                  </span>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5 text-xs text-zinc-600 dark:text-zinc-400">
                    <p>
                      <strong>Patient:</strong> {comp.patient_name || "Patient"}
                    </p>
                    <p>
                      <strong>Hospital:</strong> {comp.hospital_name || "Hospital"}
                    </p>
                  </div>

                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={async () => {
                        try {
                          await apiClient.post("/confirmations/confirm-completion", {
                            transfusion_id: comp.transfusion_id,
                            notes: "Donor confirmed transfusion completion"
                          });
                          fetchDashboardData();
                        } catch (err) {
                          console.error(err);
                        }
                      }}
                      className="rounded-md bg-emerald-600 px-4 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-emerald-700"
                    >
                      Confirm Transfusion Completed
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pending requests queue */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-zinc-900 dark:text-white border-b pb-2 dark:border-zinc-800">
          Donation Request Requests
        </h3>
        {requests.length > 0 ? (
          <div className="space-y-4">
            {requests.map((req) => (
              <div
                key={req.id}
                className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900 space-y-4 shadow-sm"
              >
                <div className="flex items-center justify-between border-b pb-2.5 dark:border-zinc-800">
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-red-100 px-2.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-red-700">
                      {req.urgency_level}
                    </span>
                    <span className="text-[10px] font-medium text-zinc-500">
                      Date: {req.scheduled_date ? format(parseISO(req.scheduled_date), "PPp") : ""}
                    </span>
                  </div>
                  <span className="rounded-full bg-brand-50 px-2 py-0.5 text-[10px] font-bold text-brand-600">
                    Required {req.patient?.blood_group || (req as any).patient_blood_group}
                  </span>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5 text-xs text-zinc-600 dark:text-zinc-400">
                    <p className="flex items-center gap-1.5">
                      <Smile className="h-4 w-4 text-brand-500" />
                      <span>Patient: {req.patient?.name || (req as any).patient_name}</span>
                    </p>
                    <p className="flex items-center gap-1.5">
                      <MapPin className="h-4 w-4 text-zinc-400" />
                      <span>Venue: {req.hospital?.name || "Hospital"}{req.hospital?.city ? ` (${req.hospital.city})` : ""}</span>
                    </p>
                  </div>

                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => handleAction(req.id, false)}
                      className="rounded-md border border-zinc-200 bg-white px-4 py-1.5 text-xs font-semibold text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300"
                    >
                      Decline Match
                    </button>
                    <button
                      onClick={() => handleAction(req.id, true)}
                      className="rounded-md bg-brand-500 px-4 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-brand-600"
                    >
                      Accept Match
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-zinc-200 py-12 text-center text-xs text-zinc-500 dark:border-zinc-800">
            No active donation requests at the moment. Keep availability toggled ON!
          </div>
        )}
      </div>

      {/* Donation logs history */}
      <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900 space-y-4">
        <h3 className="text-sm font-bold text-zinc-900 dark:text-white border-b pb-2 dark:border-zinc-800">
          Recent Donations History
        </h3>
        {history.length > 0 ? (
          <div className="space-y-3">
            {history.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between border-b border-zinc-100 pb-2.5 last:border-0 last:pb-0 dark:border-zinc-800"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-100 text-zinc-500 dark:bg-zinc-850 dark:text-zinc-400">
                    <Clock className="h-4.5 w-4.5" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-zinc-800 dark:text-zinc-200">
                      Donation Run #{item.id}
                    </p>
                    <p className="text-[10px] text-zinc-500">
                      Date: {item.completed_at ? format(parseISO(item.completed_at), "PP") : "Past month"}
                    </p>
                  </div>
                </div>
                <span className="rounded bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-600">
                  Completed
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-zinc-500 text-center py-4">No completed donation logs.</p>
        )}
      </div>
    </div>
  );
}
