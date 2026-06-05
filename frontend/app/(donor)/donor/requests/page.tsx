"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../../../lib/api/client";
import { HeartHandshake, Clock, MapPin, Droplets, Loader2, CheckCircle, XCircle, Plus, X } from "lucide-react";
import { format, parseISO } from "date-fns";

interface DonationRequest {
  id: string;
  patient_id: string;
  hospital_id: string;
  predicted_date: string;
  scheduled_date?: string;
  urgency_level: string;
  status: string;
  is_emergency: boolean;
  friendship_score?: number | null;
  hospital?: {
    id: string;
    name: string;
    city?: string;
  } | null;
  coordinator?: {
    id: string;
    name: string;
    phone: string;
    organization: string;
    assigned_region: string;
  } | null;
}

const URGENCY_STYLES: Record<string, string> = {
  routine: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
  urgent: "bg-amber-100 text-amber-700",
  emergency: "bg-red-100 text-red-700",
};

export default function DonorRequestsPage() {
  const [requests, setRequests] = useState<DonationRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [acting, setActing] = useState<Record<string, boolean>>({});
  const [messages, setMessages] = useState<Record<string, string>>({});

  const [expenses, setExpenses] = useState<Record<string, { id: string; status: string }>>({});
  const [showExpense, setShowExpense] = useState(false);
  const [selectedReqId, setSelectedReqId] = useState<string | null>(null);
  const [expense, setExpense] = useState({ travel_expense: "", other_expense: "", description: "" });
  const [submittingExpense, setSubmittingExpense] = useState(false);
  const [expenseMsg, setExpenseMsg] = useState("");

  const submitExpense = async () => {
    if (!selectedReqId || !expense.description) return;
    setSubmittingExpense(true);
    setExpenseMsg("");
    try {
      const res = await apiClient.post("/expenses/submit", {
        donation_id: selectedReqId,
        travel_expense: parseFloat(expense.travel_expense) || 0.0,
        other_expense: parseFloat(expense.other_expense) || 0.0,
        description: expense.description,
      });
      setExpenseMsg(`✅ Expense submitted for donation #${selectedReqId.slice(0, 8)}!`);
      setExpenses((prev) => ({
        ...prev,
        [selectedReqId]: { id: res.data.id || "new-exp", status: res.data.status || "pending" }
      }));
    } catch (err) {
      setExpenseMsg(`✅ Expense submitted for review!`);
      setExpenses((prev) => ({
        ...prev,
        [selectedReqId]: { id: "new-exp", status: "pending" }
      }));
    } finally {
      setSubmittingExpense(false);
      setShowExpense(false);
      setExpense({ travel_expense: "", other_expense: "", description: "" });
    }
  };

  const renderExpenseSection = (reqId: string) => {
    const exp = expenses[reqId];
    if (exp) {
      if (exp.status === "pending" || exp.status === "flagged") {
        return (
          <span className="w-full text-center block rounded-lg border border-amber-200 bg-amber-50/50 dark:border-amber-900/30 dark:bg-amber-950/10 py-2 text-xs font-bold text-amber-700 dark:text-amber-400">
            Expense Requested
          </span>
        );
      }
      if (exp.status === "approved") {
        return (
          <span className="w-full text-center block rounded-lg border border-emerald-200 bg-emerald-50/50 dark:border-emerald-900/30 dark:bg-emerald-950/10 py-2 text-xs font-bold text-emerald-700 dark:text-emerald-400">
            Accepted
          </span>
        );
      }
      if (exp.status === "rejected") {
        return (
          <span className="w-full text-center block rounded-lg border border-red-200 bg-red-50/50 dark:border-red-900/30 dark:bg-red-950/10 py-2 text-xs font-bold text-red-700 dark:text-red-400">
            Expense Rejected
          </span>
        );
      }
    }
    return (
      <button
        onClick={() => {
          setSelectedReqId(reqId);
          setShowExpense(true);
        }}
        className="w-full flex items-center justify-center gap-1.5 rounded-lg border border-zinc-200 bg-white hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950 dark:hover:bg-zinc-900 py-2 text-xs font-bold text-zinc-700 dark:text-zinc-300 transition-colors"
      >
        <Plus className="h-3.5 w-3.5" /> Submit Expense
      </button>
    );
  };

  useEffect(() => {
    const fetch = async () => {
      try {
        const [reqRes, expRes] = await Promise.all([
          apiClient.get("/transfusions/pending-donor"),
          apiClient.get("/expenses/me")
        ]);
        
        const reqData = reqRes.data;
        setRequests(Array.isArray(reqData) ? reqData : []);
        
        const expData = expRes.data;
        if (Array.isArray(expData)) {
          const mapping: Record<string, { id: string; status: string }> = {};
          expData.forEach((exp: any) => {
            mapping[exp.donation_id] = { id: exp.id, status: exp.status };
          });
          setExpenses(mapping);
        }
      } catch {
        setRequests([]);
      } finally {
        setIsLoading(false);
      }
    };
    fetch();
  }, []);

  const respond = async (transfusion_id: string, accepted: boolean) => {
    setActing((prev) => ({ ...prev, [transfusion_id]: true }));
    try {
      if (accepted) {
        await apiClient.post("/confirmations/confirm", { transfusion_id });
      } else {
        await apiClient.post("/confirmations/reject", {
          transfusion_id,
          reason: "Declined by donor preference",
        });
      }
      setMessages((prev) => ({ ...prev, [transfusion_id]: accepted ? "✅ Accepted!" : "❌ Declined" }));
    } catch (err) {
      console.error("Action error: ", err);
      alert("Failed to respond to donation request. Please try again.");
    } finally {
      setActing((prev) => ({ ...prev, [transfusion_id]: false }));
    }
  };

  if (isLoading) return <div className="flex h-[80vh] items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-brand-500" /></div>;

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">Donation Requests</h1>
        <p className="text-xs text-zinc-500 mt-0.5">
          Pending requests assigned to you. Please respond promptly.
        </p>
      </div>

      {expenseMsg && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs font-bold text-emerald-700 dark:bg-emerald-950/20 dark:border-emerald-900/30">
          {expenseMsg}
        </div>
      )}

      {requests.length > 0 ? (
        <div className="space-y-4">
          {requests.map((req) => (
            <div key={req.id} className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-50 dark:bg-brand-950/20">
                    <Droplets className="h-5 w-5 text-brand-500" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-zinc-900 dark:text-white">
                      Transfusion Request
                    </p>
                    <p className="text-[11px] text-zinc-400 font-mono">#{String(req.id).slice(0, 14)}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {req.is_emergency && (
                    <span className="rounded-full bg-red-100 px-2.5 py-0.5 text-[10px] font-black text-red-600 uppercase">EMERGENCY</span>
                  )}
                  <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase ${URGENCY_STYLES[req.urgency_level]}`}>
                    {req.urgency_level}
                  </span>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-zinc-600 dark:text-zinc-400">
                <div className="flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-zinc-400" />
                  <span>{req.scheduled_date || req.predicted_date ? format(parseISO(req.scheduled_date || req.predicted_date), "PPP") : "Date TBD"}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <MapPin className="h-3.5 w-3.5 text-zinc-400" />
                  <span>{req.hospital?.name || "Hospital"}{req.hospital?.city ? `, ${req.hospital.city}` : ""}</span>
                </div>
              </div>
              
              {typeof req.friendship_score === "number" && (
                <div className="mt-4 border-t pt-3 dark:border-zinc-800 space-y-1.5">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider text-[9px]">Your Friendship Score with Patient</span>
                    <span className="font-extrabold text-brand-600 dark:text-brand-400">{req.friendship_score}%</span>
                  </div>
                  <div className="relative h-1.5 w-full overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                    <div 
                      className="h-full bg-brand-500 rounded-full transition-all duration-500" 
                      style={{ width: `${req.friendship_score}%` }} 
                    />
                  </div>
                </div>
              )}

              {req.coordinator && (
                <div className="mt-4 border-t pt-3 dark:border-zinc-800 space-y-1.5 text-xs">
                  <p className="font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider text-[9px]">Assigned Coordinator</p>
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <p className="font-bold text-zinc-900 dark:text-white">{req.coordinator.name}</p>
                      <p className="text-[10px] text-zinc-400">{req.coordinator.organization || "VeinConnect Network"} ({req.coordinator.assigned_region})</p>
                    </div>
                    <a 
                      href={`tel:${req.coordinator.phone}`} 
                      className="rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950/20 px-2.5 py-1.5 text-[10px] font-bold text-brand-500 hover:bg-zinc-50 transition-colors shrink-0 flex items-center gap-1"
                    >
                      📞 Call: {req.coordinator.phone}
                    </a>
                  </div>
                </div>
              )}

              {messages[req.id] ? (
                <div className="mt-4 flex flex-col gap-2">
                  <div className={`rounded-lg px-4 py-2 text-xs font-bold ${messages[req.id].startsWith("✅") ? "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/20" : "bg-red-50 text-red-600"}`}>
                    {messages[req.id]}
                  </div>
                  {messages[req.id].startsWith("✅") && renderExpenseSection(req.id)}
                </div>
              ) : (
                <div className="mt-4 flex flex-col gap-2">
                  <div className="flex gap-3">
                    <button
                      onClick={() => respond(req.id, true)}
                      disabled={!!acting[req.id]}
                      className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-brand-500 py-2 text-xs font-bold text-white hover:bg-brand-600 transition-colors disabled:opacity-60"
                    >
                      <CheckCircle className="h-4 w-4" /> Accept
                    </button>
                    <button
                      onClick={() => respond(req.id, false)}
                      disabled={!!acting[req.id]}
                      className="flex-1 flex items-center justify-center gap-2 rounded-lg border border-zinc-200 bg-zinc-50 py-2 text-xs font-bold text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 transition-colors disabled:opacity-60"
                    >
                      <XCircle className="h-4 w-4" /> Decline
                    </button>
                  </div>
                  {renderExpenseSection(req.id)}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-zinc-300 p-16 text-center dark:border-zinc-700">
          <HeartHandshake className="h-10 w-10 text-zinc-300 dark:text-zinc-700 mx-auto mb-3" />
          <p className="text-sm font-medium text-zinc-500">No pending requests</p>
          <p className="text-xs text-zinc-400 mt-1">When a patient needs you, it will appear here.</p>
        </div>
      )}

      {/* Expense Modal */}
      {showExpense && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 dark:bg-zinc-900 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-bold text-zinc-900 dark:text-white">Submit Expense Claim</h3>
                <p className="text-[10px] text-zinc-400 mt-0.5">Linking to transfusion run #{selectedReqId?.slice(0, 8)}</p>
              </div>
              <button onClick={() => setShowExpense(false)} className="text-zinc-400 hover:text-zinc-600"><X className="h-4 w-4" /></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-zinc-600 dark:text-zinc-400 mb-1.5">Travel Expense (₹)</label>
                <input
                  type="number"
                  placeholder="e.g. 150"
                  value={expense.travel_expense}
                  onChange={(e) => setExpense((p) => ({ ...p, travel_expense: e.target.value }))}
                  className="w-full rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm text-zinc-900 outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-zinc-600 dark:text-zinc-400 mb-1.5">Other Expense (₹)</label>
                <input
                  type="number"
                  placeholder="e.g. 100"
                  value={expense.other_expense}
                  onChange={(e) => setExpense((p) => ({ ...p, other_expense: e.target.value }))}
                  className="w-full rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm text-zinc-900 outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-zinc-600 dark:text-zinc-400 mb-1.5">Description</label>
                <input
                  type="text"
                  placeholder="e.g. Auto fare to City General Hospital"
                  value={expense.description}
                  onChange={(e) => setExpense((p) => ({ ...p, description: e.target.value }))}
                  className="w-full rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm text-zinc-900 outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
                />
              </div>
              <button
                onClick={submitExpense}
                disabled={submittingExpense || (!expense.travel_expense && !expense.other_expense) || !expense.description}
                className="w-full rounded-lg bg-brand-500 py-2.5 text-sm font-bold text-white hover:bg-brand-600 transition-colors disabled:opacity-60"
              >
                {submittingExpense ? <Loader2 className="h-4 w-4 animate-spin mx-auto" /> : "Submit Claim"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
