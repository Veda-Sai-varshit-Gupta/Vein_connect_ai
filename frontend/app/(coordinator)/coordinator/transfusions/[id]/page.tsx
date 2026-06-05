"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../../../../lib/api/client";
import { 
  Loader2, 
  ArrowLeft, 
  Clock, 
  Calendar, 
  Droplets, 
  MapPin, 
  CheckCircle2, 
  User, 
  Hospital, 
  AlertCircle,
  XCircle,
  Check
} from "lucide-react";
import Link from "next/link";
import { format, parseISO } from "date-fns";
import { useParams } from "next/navigation";

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
  failed: "bg-red-100 text-red-700",
};

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

export default function CoordinatorTransfusionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Action state
  const [confirming, setConfirming] = useState(false);
  const [rejectingDonor, setRejectingDonor] = useState(false);
  const [savingDetails, setSavingDetails] = useState(false);
  const [confirmingCompletion, setConfirmingCompletion] = useState(false);

  // Form expansion states
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  // Form input fields
  const [scheduledDate, setScheduledDate] = useState("");
  const [notes, setNotes] = useState("");
  const [rejectReason, setRejectReason] = useState("");
  const [completionConfirmations, setCompletionConfirmations] = useState<any[]>([]);

  // Feedback Toast
  const [feedback, setFeedback] = useState<{ text: string; type: "success" | "error" } | null>(null);

  const showFeedback = (text: string, type: "success" | "error" = "success") => {
    setFeedback({ text, type });
    setTimeout(() => setFeedback(null), 4000);
  };

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await apiClient.get(`/transfusions/${id}`);
        setData(res.data);
        if (res.data) {
          setScheduledDate(res.data.scheduled_date || "");
          setNotes(res.data.notes || "");
        }

        try {
          const compRes = await apiClient.get(`/confirmations/${id}/completion-status`);
          setCompletionConfirmations(compRes.data);
        } catch {
          setCompletionConfirmations([]);
        }
      } catch {
        setData(null);
        setCompletionConfirmations([]);
      } finally {
        setIsLoading(false);
      }
    };
    if (id) fetch();
  }, [id]);

  const confirm = async () => {
    setConfirming(true);
    try {
      await apiClient.post(`/confirmations/confirm`, {
        transfusion_id: id,
      });
      showFeedback("Coordinator review confirmed successfully!");
      const res = await apiClient.get(`/transfusions/${id}`);
      setData(res.data);
    } catch (err: any) {
      console.error(err);
      showFeedback(err?.response?.data?.detail || "Failed to confirm coordinator review.", "error");
    } finally {
      setConfirming(false);
    }
  };

  const rejectDonor = async () => {
    setRejectingDonor(true);
    try {
      await apiClient.post(`/confirmations/reject`, {
        transfusion_id: id,
        reason: rejectReason,
      });
      showFeedback("Donor rejected. AI matching system is assigning the next compatible donor.");
      setShowRejectForm(false);
      setRejectReason("");
      const res = await apiClient.get(`/transfusions/${id}`);
      setData(res.data);
    } catch (err: any) {
      console.error(err);
      showFeedback(err?.response?.data?.detail || "Failed to reject matched donor.", "error");
    } finally {
      setRejectingDonor(false);
    }
  };

  const handleSaveDetails = async () => {
    setSavingDetails(true);
    try {
      await apiClient.put(`/transfusions/${id}`, {
        scheduled_date: scheduledDate || null,
        notes: notes || null,
      });
      showFeedback("Transfusion details updated successfully.");
      setIsEditing(false);
      const res = await apiClient.get(`/transfusions/${id}`);
      setData(res.data);
    } catch (err: any) {
      console.error(err);
      showFeedback(err?.response?.data?.detail || "Failed to update details.", "error");
    } finally {
      setSavingDetails(false);
    }
  };

  const formatScheduledDate = (dateStr: string | null) => {
    if (!dateStr) return "TBD";
    try {
      return format(parseISO(dateStr), "dd MMM yyyy");
    } catch {
      return dateStr;
    }
  };

  if (isLoading) return <div className="flex h-[80vh] items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-brand-500" /></div>;

  if (!data) {
    return (
      <div className="flex h-[80vh] flex-col items-center justify-center text-center space-y-3">
        <p className="text-sm font-bold text-zinc-500">Transfusion run details not found</p>
        <Link href="/coordinator/transfusions" className="rounded-lg bg-zinc-900 px-4 py-2 text-xs font-bold text-white hover:opacity-90 dark:bg-white dark:text-zinc-900 transition-colors">
          Return to List
        </Link>
      </div>
    );
  }

  const isCancellable = !["completed", "cancelled", "failed"].includes(data.status);

  return (
    <div className="space-y-6 max-w-3xl relative">
      {/* Toast alert banner */}
      {feedback && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-2 rounded-lg px-4 py-3 text-xs font-bold text-white shadow-lg transition-all duration-300 ${
          feedback.type === "success" ? "bg-emerald-600" : "bg-rose-600"
        }`}>
          {feedback.type === "success" ? <Check className="h-4 w-4 shrink-0" /> : <AlertCircle className="h-4 w-4 shrink-0" />}
          <span>{feedback.text}</span>
        </div>
      )}

      {/* Header section */}
      <div className="flex items-center gap-3">
        <Link href="/coordinator/transfusions" className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors">
          <ArrowLeft className="h-4 w-4 text-zinc-600 dark:text-zinc-400" />
        </Link>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-black tracking-tight text-zinc-900 dark:text-white">Run #{String(data.id).slice(0, 8)}</h1>
            <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase ${data.urgency_level === "urgent" || data.urgency_level === "emergency" ? "bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400" : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"}`}>{data.urgency_level}</span>
          </div>
        </div>
      </div>

      {/* Stakeholders grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Patient Info */}
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900 shadow-sm">
          <div className="flex items-center gap-2 mb-3 text-brand-500">
            <User className="h-4 w-4" /> <span className="text-xs font-bold uppercase tracking-wider">Patient</span>
          </div>
          <p className="text-sm font-bold text-zinc-900 dark:text-white">{data.patient?.name || "Patient"}</p>
          <div className="flex items-center gap-2 mt-1">
            <span className="rounded bg-red-50 px-1.5 py-0.5 text-[10px] font-black text-red-600 dark:bg-red-950/20 dark:text-red-400">{data.patient?.blood_group || "—"}</span>
            <span className="text-[10px] text-zinc-400 font-mono">{String(data.patient_id).slice(0, 8)}</span>
          </div>
        </div>

        {/* Donor Info */}
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900 shadow-sm">
          <div className="flex items-center gap-2 mb-3 text-emerald-500">
            <Droplets className="h-4 w-4" /> <span className="text-xs font-bold uppercase tracking-wider">Donor</span>
          </div>
          {data.donor_id ? (
            <>
              <p className="text-sm font-bold text-zinc-900 dark:text-white">{data.donor?.name || "Assigned Donor"}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="rounded bg-emerald-50 px-1.5 py-0.5 text-[10px] font-black text-emerald-600 dark:bg-emerald-950/20 dark:text-emerald-400">{data.donor?.blood_group || "—"}</span>
                <span className="text-[10px] text-zinc-400 font-mono">{String(data.donor_id).slice(0, 8)}</span>
              </div>
              {data.donor?.medical_clearance_url && (
                <div className="mt-2 pt-2 border-t border-zinc-100 dark:border-zinc-800">
                  <a
                    href={data.donor.medical_clearance_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[10px] font-bold text-brand-500 hover:underline flex items-center gap-1"
                  >
                    View Medical Clearance
                  </a>
                </div>
              )}
            </>
          ) : (
            <p className="text-sm font-bold text-zinc-400">Not Assigned</p>
          )}
        </div>

        {/* Hospital Info */}
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900 shadow-sm">
          <div className="flex items-center gap-2 mb-3 text-blue-500">
            <Hospital className="h-4 w-4" /> <span className="text-xs font-bold uppercase tracking-wider">Hospital</span>
          </div>
          {data.hospital_id ? (
            <>
              <p className="text-sm font-bold text-zinc-900 dark:text-white">{data.hospital?.name || "Hospital"}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-[10px] text-zinc-400 font-mono">{String(data.hospital_id).slice(0, 8)}</span>
              </div>
            </>
          ) : (
            <p className="text-sm font-bold text-zinc-400">Not Assigned</p>
          )}
        </div>
      </div>

      {/* Consensus status tracker */}
      <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900 shadow-sm">
        <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-500 mb-4">Consensus Status</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Patient", status: data.patient_confirmation },
            { label: "Donor", status: data.donor_confirmation },
            { label: "Coordinator", status: data.coordinator_confirmation },
            { label: "Hospital", status: data.hospital_confirmation },
          ].map((item) => (
            <div key={item.label} className={`flex flex-col items-center justify-center rounded-lg border p-3 text-center ${item.status === "confirmed" ? "border-emerald-200 bg-emerald-50/50 dark:border-emerald-900/30 dark:bg-emerald-950/20" : item.status === "rejected" ? "border-red-200 bg-red-50/50 dark:border-red-900/30 dark:bg-red-950/20" : "border-zinc-100 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950/50"}`}>
              <div className={`flex h-6 w-6 items-center justify-center rounded-full mb-2 ${item.status === "confirmed" ? "bg-emerald-500 text-white" : item.status === "rejected" ? "bg-red-500 text-white" : "bg-zinc-200 text-zinc-500 dark:bg-zinc-800"}`}>
                {item.status === "confirmed" ? <CheckCircle2 className="h-3.5 w-3.5" /> : item.status === "rejected" ? <XCircle className="h-3.5 w-3.5" /> : <Clock className="h-3.5 w-3.5" />}
              </div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-400">{item.label}</p>
              <p className={`text-[9px] font-bold uppercase mt-1 ${item.status === "confirmed" ? "text-emerald-600 dark:text-emerald-400" : item.status === "rejected" ? "text-red-600 dark:text-red-400" : "text-amber-500"}`}>{item.status || "pending"}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Transfusion Completion Consensus Panel */}
      {completionConfirmations && completionConfirmations.length > 0 && (
        <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-zinc-900 dark:text-white">Transfusion Completion Consensus</h2>
              <p className="text-[11px] text-zinc-400">All 4 stakeholders must confirm that the transfusion procedure has completed successfully.</p>
            </div>
            {data?.status === "completed" ? (
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

          {/* Action button if coordinator has a pending completion confirmation */}
          {(() => {
            const coordConf = completionConfirmations.find((c) => c.role === "coordinator");
            if (coordConf && coordConf.status === "pending" && data?.status === "in_progress") {
              return (
                <div className="mt-4 border-t pt-4 dark:border-zinc-800 flex justify-end">
                  <button
                    onClick={async () => {
                      setConfirmingCompletion(true);
                      try {
                        const res = await apiClient.post(`/confirmations/confirm-completion`, {
                          transfusion_id: id,
                          notes: "Coordinator confirmed transfusion completion"
                        });
                        showFeedback("Completion confirmation submitted!");
                        setCompletionConfirmations(res.data);
                        // Refresh transfusion state
                        const tRes = await apiClient.get(`/transfusions/${id}`);
                        setData(tRes.data);
                      } catch (err: any) {
                        showFeedback(err?.response?.data?.detail || "Failed to confirm completion.", "error");
                      } finally {
                        setConfirmingCompletion(false);
                      }
                    }}
                    disabled={confirmingCompletion}
                    className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-700 transition-colors disabled:opacity-60"
                  >
                    {confirmingCompletion ? <Loader2 className="h-3 w-3 animate-spin" /> : <CheckCircle2 className="h-3 w-3" />}
                    Confirm Transfusion Completed
                  </button>
                </div>
              );
            }
            return null;
          })()}
        </div>
      )}

      {/* Action controls panel */}
      {isCancellable && (
        <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900 shadow-sm space-y-4">
          <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-500 mb-2">Coordinator Actions</h2>
          
          <div className="flex flex-wrap gap-3">
            {/* Confirm Coordinator Review */}
            {data.coordinator_confirmation !== "confirmed" && (
              <button
                onClick={confirm}
                disabled={confirming}
                className="rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 px-4 py-2 text-xs font-bold hover:opacity-90 transition-opacity disabled:opacity-60 flex items-center gap-1.5"
              >
                {confirming && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                Confirm Coordinator Review (Accept)
              </button>
            )}

            {/* Reject Matched Donor */}
            {data.donor_id && (
              <button
                onClick={() => {
                  setShowRejectForm(!showRejectForm);
                }}
                className="rounded-lg border border-red-200 bg-red-50 dark:border-red-900/30 dark:bg-red-950/20 text-red-600 dark:text-red-400 px-4 py-2 text-xs font-bold hover:bg-red-100 dark:hover:bg-red-950/45 transition-colors"
              >
                Reject Matched Donor
              </button>
            )}
          </div>

          {/* Reject Donor expanded block */}
          {showRejectForm && (
            <div className="rounded-lg border border-red-100 bg-red-50/20 dark:border-red-950/35 dark:bg-red-950/10 p-4 space-y-3 mt-3">
              <h3 className="text-xs font-bold text-red-800 dark:text-red-400">Reject Matched Donor</h3>
              <p className="text-[11px] text-zinc-500">This will reject the matched donor reservation, notify all stakeholders, and instruct the AI matcher to automatically select and reserve the next best donor candidate.</p>
              <div>
                <label className="text-[9px] text-zinc-400 font-bold uppercase block mb-1">Reason for Rejection</label>
                <textarea
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="e.g. Donor unavailable on scheduled date, location mismatch, etc..."
                  rows={2}
                  className="w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-xs text-zinc-900 focus:border-red-500 focus:outline-none dark:border-zinc-800 dark:bg-zinc-950 dark:text-white"
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setShowRejectForm(false)}
                  className="rounded px-2.5 py-1 text-xs font-bold text-zinc-500 hover:text-zinc-600"
                >
                  Close
                </button>
                <button
                  onClick={rejectDonor}
                  disabled={rejectingDonor || !rejectReason.trim()}
                  className="rounded bg-red-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-red-700 disabled:opacity-60 flex items-center gap-1"
                >
                  {rejectingDonor && <Loader2 className="h-3 w-3 animate-spin" />}
                  Confirm Rejection & Re-match
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Run details card */}
      <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-500">Run Details</h2>
          {isCancellable && (
            !isEditing ? (
              <button
                onClick={() => {
                  setScheduledDate(data.scheduled_date || "");
                  setNotes(data.notes || "");
                  setIsEditing(true);
                }}
                className="text-xs font-bold text-zinc-900 dark:text-white border border-zinc-200 dark:border-zinc-800 rounded px-2.5 py-1 hover:bg-zinc-50 dark:hover:bg-zinc-850 transition-colors"
              >
                Edit details
              </button>
            ) : (
              <div className="flex gap-2">
                <button
                  onClick={() => setIsEditing(false)}
                  className="text-xs font-bold text-zinc-500 hover:text-zinc-600"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveDetails}
                  disabled={savingDetails}
                  className="text-xs font-bold text-brand-600 hover:text-brand-700 dark:text-brand-400 flex items-center gap-1"
                >
                  {savingDetails && <Loader2 className="h-3 w-3 animate-spin" />}
                  Save
                </button>
              </div>
            )
          )}
        </div>

        {isEditing ? (
          <div className="space-y-4">
            <div>
              <label className="text-[10px] text-zinc-400 font-bold uppercase block mb-1">Scheduled Date</label>
              <input
                type="date"
                value={scheduledDate}
                onChange={(e) => setScheduledDate(e.target.value)}
                className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-brand-500 focus:outline-none dark:border-zinc-800 dark:bg-zinc-950 dark:text-white"
              />
            </div>
            <div>
              <label className="text-[10px] text-zinc-400 font-bold uppercase block mb-1">Notes</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                placeholder="Clinical details, hospital instructions, or travel coordinator comments..."
                className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-brand-500 focus:outline-none dark:border-zinc-800 dark:bg-zinc-950 dark:text-white"
              />
            </div>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-zinc-100 dark:bg-zinc-800"><Calendar className="h-4 w-4 text-zinc-500" /></div>
                <div>
                  <p className="text-[10px] text-zinc-400 font-bold uppercase">Scheduled Date</p>
                  <p className="text-sm font-medium text-zinc-900 dark:text-white">{formatScheduledDate(data.scheduled_date)}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-zinc-100 dark:bg-zinc-800"><MapPin className="h-4 w-4 text-zinc-500" /></div>
                <div>
                  <p className="text-[10px] text-zinc-400 font-bold uppercase">Status</p>
                  <p className="text-sm font-medium text-zinc-900 dark:text-white capitalize">{data.status.replace(/_/g, " ")}</p>
                </div>
              </div>
            </div>
            {data.notes && (
              <div className="mt-4 rounded-lg bg-zinc-50 p-3 dark:bg-zinc-950/50">
                <p className="text-[10px] text-zinc-400 font-bold uppercase mb-1">Notes</p>
                <p className="text-xs text-zinc-700 dark:text-zinc-300 leading-relaxed">{data.notes}</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
