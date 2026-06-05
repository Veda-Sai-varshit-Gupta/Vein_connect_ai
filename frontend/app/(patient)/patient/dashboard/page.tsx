"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "../../../../lib/api/client";
import { Patient, Transfusion, TransfusionStatus, BloodGroup } from "../../../../lib/types/common";
import { Calendar, Heart, ShieldAlert, Award, Clock, ArrowRight, User, Loader2 } from "lucide-react";
import { format, formatDistanceToNow, parseISO } from "date-fns";

interface ConsensusStatus {
  patient: { status: string };
  donor: { status: string };
  coordinator: { status: string };
  hospital: { status: string };
  all_confirmed: boolean;
  pending_count: number;
}

export default function PatientDashboard() {
  const router = useRouter();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [activeTransfusion, setActiveTransfusion] = useState<Transfusion | null>(null);
  const [activeConsensus, setActiveConsensus] = useState<ConsensusStatus | null>(null);
  const [history, setHistory] = useState<Transfusion[]>([]);
  const [wallet, setWallet] = useState<{ balance: number } | null>(null);
  const [predictionDate, setPredictionDate] = useState<Date | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Fetch patient profile
        const patientResponse = await apiClient.get("/patients/me");
        if (!patientResponse.data) {
          router.push("/register/patient");
          return;
        }
        setPatient(patientResponse.data);
        const pId = patientResponse.data.id;

        // Fetch AI prediction
        try {
          const predRes = await apiClient.get("/patients/me/prediction");
          if (predRes.data && predRes.data.predicted_date) {
            setPredictionDate(parseISO(predRes.data.predicted_date));
          }
        } catch (e) {
          console.warn("Failed to fetch next transfusion prediction", e);
        }

        // Fetch wallet balance
        try {
          const wRes = await apiClient.get("/wallets/me");
          setWallet(wRes.data);
        } catch (e) {
          console.warn("Failed to fetch wallet for patient dashboard", e);
        }

        // Fetch upcoming/active transfusions
        const upcomingResponse = await apiClient.get("/transfusions/upcoming", {
          params: { limit: 1 },
        });
        if (upcomingResponse.data && upcomingResponse.data.length > 0) {
          const active = upcomingResponse.data[0];
          setActiveTransfusion(active);
          try {
            const cRes = await apiClient.get(`/transfusions/${active.id}/consensus`);
            setActiveConsensus(cRes.data);
          } catch (e) {
            console.warn("Failed to fetch consensus for active transfusion", e);
          }
        } else {
          setActiveTransfusion(null);
          setActiveConsensus(null);
        }

        // Fetch history
        const historyResponse = await apiClient.get("/transfusions/history", {
          params: { limit: 5 },
        });
        setHistory(Array.isArray(historyResponse.data) ? historyResponse.data : []);
      } catch (err) {
        console.error("Error loading patient dashboard:", err);
        setHistory([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const getStatusBadge = (status: TransfusionStatus) => {
    const statusMap: Record<TransfusionStatus, { label: string; style: string }> = {
      predicted: { label: "AI Predicted", style: "bg-slate-100 text-slate-700 dark:bg-slate-900/30 dark:text-slate-400" },
      patient_confirmed: { label: "Patient Confirmed", style: "bg-brand-50 text-brand-600 dark:bg-brand-950/20 dark:text-brand-400" },
      matching_donors: { label: "Matching Donors", style: "bg-amber-50 text-amber-600" },
      donor_confirmed: { label: "Donor Confirmed", style: "bg-blue-50 text-blue-600 dark:bg-blue-950/20 dark:text-blue-400" },
      coordinator_confirmed: { label: "Coordinator Confirmed", style: "bg-blue-100 text-blue-800" },
      hospital_confirmed: { label: "Hospital Confirmed", style: "bg-blue-100 text-blue-800" },
      scheduled: { label: "Scheduled", style: "bg-emerald-50 text-emerald-600" },
      in_progress: { label: "In Progress", style: "bg-amber-100 text-amber-800" },
      completed: { label: "Completed", style: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/20 dark:text-emerald-400" },
      cancelled: { label: "Cancelled", style: "bg-red-50 text-red-600" },
      failed: { label: "Failed", style: "bg-red-100 text-red-800" },
    };
    const mapped = statusMap[status] || { label: status, style: "bg-zinc-100 text-zinc-800" };
    return (
      <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${mapped.style}`}>
        {mapped.label}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
      </div>
    );
  }

  const upcomingDate = activeTransfusion?.scheduled_date
    ? parseISO(activeTransfusion.scheduled_date)
    : predictionDate || null;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">
            Good morning, {patient?.name} 👋
          </h1>
          <p className="text-xs text-zinc-500">
            Monitor your recurring schedule and matching confirmations.
          </p>
        </div>
      </div>

      {/* Profile Metrics Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {/* Next predicted Card */}
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">
              Next Transfusion
            </span>
            <Calendar className="h-4.5 w-4.5 text-brand-500" />
          </div>
          <div className="mt-2">
            <p className="text-lg font-bold text-zinc-900 dark:text-white">
              {upcomingDate ? format(upcomingDate, "MMMM dd, yyyy") : "No Schedule"}
            </p>
            <p className="text-xs text-zinc-500 mt-0.5">
              {upcomingDate 
                ? `${activeTransfusion?.scheduled_date ? "approx. " : "predicted (approx. "}${formatDistanceToNow(upcomingDate)} remaining${activeTransfusion?.scheduled_date ? "" : ")"}`
                : "Request your next run"}
            </p>
          </div>
        </div>

        {/* Blood Group Info */}
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">
              My Blood Group
            </span>
            <Heart className="h-4.5 w-4.5 text-red-500 fill-red-500" />
          </div>
          <div className="mt-2">
            <div className="flex items-center gap-2">
              <span className="rounded bg-blood-bp px-2 py-0.5 text-xs font-bold text-white">
                {patient?.blood_group}
              </span>
              <span className="text-xs font-bold capitalize text-zinc-800 dark:text-zinc-200">
                Thalassemia {patient?.thalassemia_type}
              </span>
            </div>
            <p className="text-xs text-zinc-500 mt-2">
              Avg interval: {patient?.avg_transfusion_interval_days} days
            </p>
          </div>
        </div>

        {/* Wallet Balance Widget */}
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">
              Wallet Balance
            </span>
            <Award className="h-4.5 w-4.5 text-brand-500" />
          </div>
          <div className="mt-2">
            <p className="text-lg font-bold text-zinc-900 dark:text-white">
              ₹ {(wallet?.balance ?? 2340).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </p>
            <p className="text-xs text-zinc-500 mt-0.5">Travel expense claims reimbursement</p>
          </div>
        </div>
      </div>

      {/* Active Transfusion details panel */}
      {activeTransfusion ? (
        <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900 space-y-4">
          <div className="flex items-center justify-between border-b pb-3 dark:border-zinc-800">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">
                Active Transfusion coordination
              </span>
              <h3 className="text-sm font-bold text-zinc-900 dark:text-white">
                Run #{activeTransfusion.id}
              </h3>
            </div>
            {getStatusBadge(activeTransfusion.status)}
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {/* 4-party consensus indicators */}
            <div className="space-y-3">
              <h4 className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">
                Transfusion Consensus status
              </h4>
              <div className="grid grid-cols-4 gap-2 text-center">
                {[
                  { key: "patient", label: "PATIENT", val: activeConsensus?.patient?.status },
                  { key: "donor", label: "DONOR", val: activeConsensus?.donor?.status },
                  { key: "coordinator", label: "COORD", val: activeConsensus?.coordinator?.status },
                  { key: "hospital", label: "HOSPITAL", val: activeConsensus?.hospital?.status },
                ].map(({ key, label, val }) => {
                  const isConfirmed = val === "confirmed";
                  const isRejected = val === "rejected";
                  return (
                    <div key={key} className="rounded-lg bg-zinc-50 p-2 dark:bg-zinc-950 border border-zinc-100 dark:border-zinc-800">
                      <span className={`text-[9px] font-bold ${isConfirmed ? "text-emerald-600" : isRejected ? "text-red-600" : "text-amber-600"}`}>
                        {isConfirmed ? "✅" : isRejected ? "❌" : "⏳"} {label}
                      </span>
                      <p className="text-[9px] font-medium text-zinc-500 mt-1 capitalize">{val || "Pending"}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Matching donor details */}
            <div className="space-y-2">
              <h4 className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">
                Matched Donor
              </h4>
              {activeTransfusion.donor ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between rounded-lg border border-zinc-100 bg-zinc-50/50 p-3 dark:border-zinc-800">
                    <div className="flex items-center gap-2.5">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-50 text-xs font-bold text-brand-600">
                        D
                      </div>
                      <div>
                        <p className="text-xs font-bold text-zinc-900 dark:text-white">
                          {activeTransfusion.donor.name}
                        </p>
                        <p className="text-[10px] text-zinc-500">
                          Reliability Score: {activeTransfusion.donor.reliability_score}% (Gold Tier)
                        </p>
                      </div>
                    </div>
                    <span className="rounded bg-brand-50 px-2 py-0.5 text-[9px] font-bold text-brand-600">
                      {activeTransfusion.donor.blood_group} Group
                    </span>
                  </div>

                  {typeof activeTransfusion.friendship_score === "number" && (
                    <div className="rounded-lg border border-zinc-100 bg-zinc-50/20 p-3 dark:border-zinc-800 space-y-1.5 shadow-sm">
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">Friendship Bond</span>
                        <span className="font-black text-brand-600 dark:text-brand-400">{activeTransfusion.friendship_score.toFixed(0)}%</span>
                      </div>
                      <div className="relative h-1.5 w-full overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                        <div 
                          className="h-full bg-brand-500 rounded-full transition-all duration-500" 
                          style={{ width: `${activeTransfusion.friendship_score}%` }} 
                        />
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-xs text-zinc-500">AI is finding matching donors...</p>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-zinc-300 p-8 text-center dark:border-zinc-700 bg-white dark:bg-zinc-900 shadow-sm">
          <Calendar className="h-8 w-8 text-zinc-300 dark:text-zinc-700 mx-auto mb-2" />
          <p className="text-sm font-bold text-zinc-700 dark:text-zinc-300">No Active Transfusion Coordination Run</p>
          <p className="text-xs text-zinc-500 mt-1 mb-4">Request a new transfusion schedule to match with compatible donors.</p>
          <button 
            onClick={() => router.push("/patient/transfusions")}
            className="rounded-lg bg-brand-500 hover:bg-brand-600 text-white px-4 py-2 text-xs font-bold transition-colors"
          >
            Request Transfusion
          </button>
        </div>
      )}

      {/* History log timeline */}
      <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900 space-y-4">
        <h3 className="text-sm font-bold text-zinc-900 dark:text-white border-b pb-2 dark:border-zinc-800">
          Transfusion History Log
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
                      Transfusion Run #{item.id}
                    </p>
                    <p className="text-[10px] text-zinc-500">
                      Completed: {item.completed_at ? format(parseISO(item.completed_at), "PPP") : "Past month"}
                    </p>
                  </div>
                </div>
                {getStatusBadge(item.status)}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-zinc-500 text-center py-4">No completed runs found.</p>
        )}
      </div>
    </div>
  );
}
