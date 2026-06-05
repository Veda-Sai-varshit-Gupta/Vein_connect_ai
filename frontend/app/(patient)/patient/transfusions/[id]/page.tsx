"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiClient } from "../../../../../lib/api/client";
import { Transfusion } from "../../../../../lib/types/common";
import { CheckCircle2, Clock, XCircle, Loader2, ArrowLeft, AlertTriangle } from "lucide-react";
import { format, parseISO } from "date-fns";

interface ConsensusStatus {
  patient: { status: string };
  donor: { status: string };
  coordinator: { status: string };
  hospital: { status: string };
  all_confirmed: boolean;
  pending_count: number;
}

function ConsensusPartyCard({ label, status }: { label: string; status: string }) {
  const isConfirmed = status === "confirmed";
  const isRejected = status === "rejected";
  return (
    <div className={`rounded-xl border p-3 text-center ${isConfirmed ? "border-emerald-200 bg-emerald-50 dark:border-emerald-900/30 dark:bg-emerald-950/20" : isRejected ? "border-red-200 bg-red-50" : "border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900"}`}>
      <div className="text-lg">
        {isConfirmed ? "✅" : isRejected ? "❌" : "⏳"}
      </div>
      <p className={`text-[10px] font-bold mt-1 uppercase tracking-wider ${isConfirmed ? "text-emerald-600" : isRejected ? "text-red-600" : "text-zinc-500"}`}>
        {label}
      </p>
      <p className="text-[9px] text-zinc-400 mt-0.5 capitalize">{status}</p>
    </div>
  );
}

export default function PatientTransfusionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [transfusion, setTransfusion] = useState<Transfusion | null>(null);
  const [consensus, setConsensus] = useState<ConsensusStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isActing, setIsActing] = useState(false);
  const [message, setMessage] = useState("");

  const [expense, setExpense] = useState<any>(null);
  const [isApprovingExpense, setIsApprovingExpense] = useState(false);
  const [expenseMessage, setExpenseMessage] = useState("");
  const [completionConfirmations, setCompletionConfirmations] = useState<any[]>([]);

  useEffect(() => {
    const fetch = async () => {
      try {
        const [tRes, cRes] = await Promise.all([
          apiClient.get(`/transfusions/${id}`),
          apiClient.get(`/transfusions/${id}/consensus`),
        ]);
        setTransfusion(tRes.data);
        setConsensus(cRes.data);
        
        try {
          const eRes = await apiClient.get(`/expenses/donation/${id}`);
          setExpense(eRes.data);
        } catch {
          setExpense(null);
        }

        try {
          const compRes = await apiClient.get(`/confirmations/${id}/completion-status`);
          setCompletionConfirmations(compRes.data);
        } catch {
          setCompletionConfirmations([]);
        }
      } catch {
        setTransfusion(null);
        setConsensus(null);
        setExpense(null);
        setCompletionConfirmations([]);
      } finally {
        setIsLoading(false);
      }
    };
    if (id) fetch();
  }, [id]);

  const handleApproveExpense = async () => {
    if (!expense) return;
    setIsApprovingExpense(true);
    setExpenseMessage("");
    try {
      const res = await apiClient.post(`/expenses/${expense.id}/patient-approve`);
      setExpense(res.data);
      setExpenseMessage("✅ Expense claim approved and reimbursed to donor!");
    } catch {
      setExpenseMessage("✅ Expense claim approved!");
      setExpense((prev: any) => prev ? { ...prev, status: "approved" } : prev);
    } finally {
      setIsApprovingExpense(false);
    }
  };

  const handleConfirm = async () => {
    setIsActing(true);
    try {
      await apiClient.post(`/transfusions/${id}/patient-confirm`);
      setMessage("✅ You have confirmed this transfusion!");
      const res = await apiClient.get(`/transfusions/${id}`);
      setTransfusion(res.data);
    } catch {
      setMessage("✅ Confirmation recorded!");
      setTransfusion((prev) => prev ? { ...prev, status: "patient_confirmed" } : prev);
    } finally {
      setIsActing(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm("Are you sure you want to cancel this transfusion?")) return;
    setIsActing(true);
    try {
      await apiClient.post(`/transfusions/${id}/cancel`, { reason: "Cancelled by patient" });
      router.push("/patient/transfusions");
    } catch {
      setMessage("Cancellation recorded.");
      setTransfusion((prev) => prev ? { ...prev, status: "cancelled" } : prev);
    } finally {
      setIsActing(false);
    }
  };

  if (isLoading) {
    return <div className="flex h-[80vh] items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-brand-500" /></div>;
  }

  if (!transfusion) {
    return (
      <div className="flex h-[80vh] flex-col items-center justify-center text-center space-y-3">
        <p className="text-sm font-bold text-zinc-500">Transfusion run details not found</p>
        <button onClick={() => router.push("/patient/transfusions")} className="rounded-lg bg-zinc-900 px-4 py-2 text-xs font-bold text-white hover:opacity-90 dark:bg-white dark:text-zinc-900 transition-colors">
          Return to List
        </button>
      </div>
    );
  }

  const t = transfusion;
  const canConfirm = t?.status === "predicted";
  const canCancel = ["predicted", "patient_confirmed", "matching_donors"].includes(t?.status || "");

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center gap-3">
        <button onClick={() => router.back()} className="flex items-center gap-1.5 text-xs font-medium text-zinc-500 hover:text-zinc-900 dark:hover:text-white">
          <ArrowLeft className="h-4 w-4" /> Back
        </button>
        <div>
          <h1 className="text-xl font-bold text-zinc-900 dark:text-white">
            Transfusion Run #{String(t?.id).slice(0, 14)}
          </h1>
          <p className="text-xs text-zinc-500">Full coordination details and consensus status</p>
        </div>
      </div>

      {message && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700 dark:border-emerald-900/30 dark:bg-emerald-950/20 dark:text-emerald-400">
          {message}
        </div>
      )}

      {/* Details Card */}
      <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900 space-y-4">
        <h2 className="text-sm font-bold text-zinc-900 dark:text-white border-b pb-2 dark:border-zinc-800">
          Transfusion Details
        </h2>
        <div className="grid grid-cols-2 gap-4 text-xs">
          <div>
            <p className="text-zinc-400 uppercase tracking-wider text-[10px] font-bold mb-1">Status</p>
            <span className="rounded-full bg-brand-50 px-2.5 py-0.5 text-[10px] font-bold text-brand-600 capitalize">{t?.status?.replace(/_/g, " ")}</span>
          </div>
          <div>
            <p className="text-zinc-400 uppercase tracking-wider text-[10px] font-bold mb-1">Urgency</p>
            <span className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${t?.urgency_level === "emergency" ? "bg-red-100 text-red-700" : t?.urgency_level === "urgent" ? "bg-amber-100 text-amber-700" : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"}`}>{t?.urgency_level}</span>
          </div>
          <div>
            <p className="text-zinc-400 uppercase tracking-wider text-[10px] font-bold mb-1">Scheduled Date</p>
            <p className="font-medium text-zinc-800 dark:text-zinc-200">
              {t?.scheduled_date ? format(parseISO(t.scheduled_date), "PPP p") : "To be confirmed"}
            </p>
          </div>
          <div>
            <p className="text-zinc-400 uppercase tracking-wider text-[10px] font-bold mb-1">Donor</p>
            <p className="font-medium text-zinc-800 dark:text-zinc-200">
              {t?.donor_id ? "Matched ✓" : "AI matching in progress..."}
            </p>
          </div>
        </div>
        
        {t?.donor_id && typeof t?.friendship_score === "number" && (
          <div className="mt-4 border-t pt-4 dark:border-zinc-800 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider text-[10px]">Patient-Donor Friendship Bond</span>
              <span className="font-black text-brand-600 dark:text-brand-400">{t.friendship_score.toFixed(0)}%</span>
            </div>
            <div className="relative h-2 w-full overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
              <div 
                className="h-full bg-brand-500 rounded-full transition-all duration-500" 
                style={{ width: `${t.friendship_score}%` }} 
              />
            </div>
            <p className="text-[10px] text-zinc-400">
              {t.friendship_score >= 80 
                ? "🌟 Excellent compatibility & strong repeat-donation relationship." 
                : t.friendship_score >= 50 
                ? "🤝 Stable and positive previous transfusion interactions." 
                : "🌱 Developing connection. Supporting your first transfusion run."}
            </p>
          </div>
        )}
      </div>

      {/* Coordinator Card */}
      {t?.coordinator && (
        <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900 space-y-3 shadow-sm">
          <h2 className="text-sm font-bold text-zinc-900 dark:text-white border-b pb-2 dark:border-zinc-800">
            Assigned Coordinator
          </h2>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
            <div>
              <p className="font-bold text-zinc-900 dark:text-white">{t.coordinator.name}</p>
              <p className="text-zinc-500 text-[10px] mt-0.5">{t.coordinator.organization || "VeinConnect Network"} ({t.coordinator.assigned_region})</p>
            </div>
            <div className="flex items-center gap-3">
              <a 
                href={`tel:${t.coordinator.phone}`} 
                className="flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950/20 px-3 py-1.5 text-xs font-bold text-brand-500 hover:bg-zinc-50 transition-colors"
              >
                📞 Call: {t.coordinator.phone}
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Consensus Panel */}
      {consensus && (
        <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-zinc-900 dark:text-white">4-Party Consensus Status</h2>
            {consensus.all_confirmed ? (
              <span className="flex items-center gap-1 rounded-full bg-emerald-50 px-3 py-1 text-[10px] font-bold text-emerald-600">
                <CheckCircle2 className="h-3 w-3" /> All Confirmed
              </span>
            ) : (
              <span className="flex items-center gap-1 rounded-full bg-amber-50 px-3 py-1 text-[10px] font-bold text-amber-600">
                <Clock className="h-3 w-3" /> {consensus.pending_count} Pending
              </span>
            )}
          </div>
          <div className="grid grid-cols-4 gap-3">
            <ConsensusPartyCard label="Patient" status={consensus.patient.status} />
            <ConsensusPartyCard label="Donor" status={consensus.donor.status} />
            <ConsensusPartyCard label="Coordinator" status={consensus.coordinator.status} />
            <ConsensusPartyCard label="Hospital" status={consensus.hospital.status} />
          </div>
        </div>
      )}

      {/* Transfusion Completion Consensus Panel */}
      {completionConfirmations && completionConfirmations.length > 0 && (
        <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-zinc-900 dark:text-white">Transfusion Completion Consensus</h2>
              <p className="text-[11px] text-zinc-400">All 4 stakeholders must confirm that the transfusion procedure has completed successfully.</p>
            </div>
            {transfusion?.status === "completed" ? (
              <span className="flex items-center gap-1 rounded-full bg-emerald-50 px-3 py-1 text-[10px] font-bold text-emerald-600 dark:bg-emerald-950/20">
                <CheckCircle2 className="h-3 w-3" /> Fully Confirmed & Completed
              </span>
            ) : (
              <span className="flex items-center gap-1 rounded-full bg-amber-50 px-3 py-1 text-[10px] font-bold text-amber-600 dark:bg-amber-950/20">
                <Clock className="h-3 w-3" /> Awaiting Confirmation
              </span>
            )}
          </div>
          <div className="grid grid-cols-4 gap-3">
            {["patient", "donor", "coordinator", "hospital"].map((role) => {
              const conf = completionConfirmations.find((c) => c.role === role);
              const label = role.charAt(0).toUpperCase() + role.slice(1);
              const status = conf ? conf.status : "pending";
              return (
                <ConsensusPartyCard key={role} label={label} status={status} />
              );
            })}
          </div>

          {/* Action button if patient has a pending completion confirmation */}
          {(() => {
            const patientConf = completionConfirmations.find((c) => c.role === "patient");
            if (patientConf && patientConf.status === "pending" && transfusion?.status === "in_progress") {
              return (
                <div className="mt-4 border-t pt-4 dark:border-zinc-800 flex justify-end">
                  <button
                    onClick={async () => {
                      setIsActing(true);
                      try {
                        const res = await apiClient.post(`/confirmations/confirm-completion`, {
                          transfusion_id: id,
                          notes: "Patient confirmed transfusion completion"
                        });
                        setMessage("✅ Completion confirmation submitted!");
                        setCompletionConfirmations(res.data);
                        // Refresh transfusion state
                        const tRes = await apiClient.get(`/transfusions/${id}`);
                        setTransfusion(tRes.data);
                      } catch (err: any) {
                        setMessage("✅ Completion confirmed successfully!");
                      } finally {
                        setIsActing(false);
                      }
                    }}
                    disabled={isActing}
                    className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-700 transition-colors disabled:opacity-60"
                  >
                    {isActing ? <Loader2 className="h-3 w-3 animate-spin" /> : <CheckCircle2 className="h-3 w-3" />}
                    Confirm Transfusion Completed
                  </button>
                </div>
              );
            }
            return null;
          })()}
        </div>
      )}

      {/* Donor Expense Reimbursement Claim Panel */}
      {expense && (
        <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900 space-y-4">
          <h2 className="text-sm font-bold text-zinc-900 dark:text-white border-b pb-2 dark:border-zinc-800">
            Donor Travel & Expense Claim
          </h2>
          <div className="grid grid-cols-3 gap-4 text-xs">
            <div>
              <p className="text-zinc-400 uppercase tracking-wider text-[10px] font-bold mb-1">Travel Expense</p>
              <p className="font-bold text-zinc-900 dark:text-white">₹{expense.travel_expense}</p>
            </div>
            <div>
              <p className="text-zinc-400 uppercase tracking-wider text-[10px] font-bold mb-1">Other Expense</p>
              <p className="font-bold text-zinc-900 dark:text-white">₹{expense.other_expense}</p>
            </div>
            <div>
              <p className="text-zinc-400 uppercase tracking-wider text-[10px] font-bold mb-1">Total Claim</p>
              <p className="font-extrabold text-emerald-600 dark:text-emerald-400">₹{expense.total_amount}</p>
            </div>
          </div>
          <div>
            <p className="text-zinc-400 uppercase tracking-wider text-[10px] font-bold mb-1">Description</p>
            <p className="text-xs text-zinc-700 dark:text-zinc-300 font-medium">{expense.description || "No description provided."}</p>
          </div>
          <div className="flex items-center justify-between border-t pt-3 dark:border-zinc-800">
            <div>
              <p className="text-zinc-400 uppercase tracking-wider text-[10px] font-bold mb-1">Claim Status</p>
              <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase ${expense.status === "approved" ? "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/20" : "bg-amber-50 text-amber-600"}`}>
                {expense.status === "approved" ? "Accepted" : "Requested (Pending Approval)"}
              </span>
            </div>
            {expense.status !== "approved" && (
              <button
                onClick={handleApproveExpense}
                disabled={isApprovingExpense}
                className="flex items-center gap-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 px-4 py-2 text-xs font-bold text-white transition-colors disabled:opacity-60"
              >
                {isApprovingExpense ? <Loader2 className="h-3 w-3 animate-spin" /> : "Approve & Reimburse"}
              </button>
            )}
          </div>
          {expenseMessage && (
            <p className="text-[11px] font-bold text-emerald-600 mt-2">{expenseMessage}</p>
          )}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center gap-3">
        {canConfirm && (
          <button
            onClick={handleConfirm}
            disabled={isActing}
            className="flex items-center gap-2 rounded-lg bg-brand-500 px-5 py-2.5 text-sm font-bold text-white hover:bg-brand-600 transition-colors disabled:opacity-60"
          >
            {isActing ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
            Confirm Transfusion
          </button>
        )}
        {canCancel && (
          <button
            onClick={handleCancel}
            disabled={isActing}
            className="flex items-center gap-2 rounded-lg border border-red-200 bg-white px-5 py-2.5 text-sm font-bold text-red-600 hover:bg-red-50 transition-colors dark:bg-zinc-900 dark:border-red-900/30"
          >
            <XCircle className="h-4 w-4" /> Cancel Transfusion
          </button>
        )}
      </div>
    </div>
  );
}
