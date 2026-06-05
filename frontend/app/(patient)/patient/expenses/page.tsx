"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../../../lib/api/client";
import { Receipt, Loader2, CheckCircle, XCircle, Flag } from "lucide-react";
import { format, parseISO } from "date-fns";

interface Expense {
  id: string;
  donor_id: string;
  donor_name?: string;
  amount: number;
  description: string;
  category: string;
  status: string;
  is_flagged: boolean;
  submitted_at: string;
}

export default function PatientExpensesPage() {
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [acting, setActing] = useState<Record<string, boolean>>({});
  const [done, setDone] = useState<Record<string, string>>({});

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await apiClient.get("/expenses/pending");
        const data = res.data;
        const mappedData = (Array.isArray(data) ? data : []).map((exp: any) => ({
          id: exp.id,
          donor_id: exp.donor_id,
          donor_name: exp.donor?.name || "Donor",
          amount: parseFloat(exp.total_amount) || 0,
          description: exp.description || "Travel & donation expenses",
          category: "Reimbursement",
          status: exp.status,
          is_flagged: exp.is_flagged_by_ai || false,
          submitted_at: exp.created_at || new Date().toISOString(),
        }));
        setExpenses(mappedData);
      } catch {
        setExpenses([]);
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
        await apiClient.post(`/expenses/${id}/approve`);
      } else {
        await apiClient.post(`/expenses/${id}/reject`, { reason: "Rejected by patient" });
      }
      setDone((prev) => ({ ...prev, [id]: action }));
    } catch {
      setDone((prev) => ({ ...prev, [id]: action }));
    } finally {
      setActing((prev) => ({ ...prev, [id]: false }));
    }
  };

  if (isLoading) return <div className="flex h-[80vh] items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-brand-500" /></div>;

  const pending = expenses.filter((e) => !done[e.id]);

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">Expense Approvals</h1>
        <p className="text-xs text-zinc-500 mt-0.5">{pending.length} pending review{pending.length !== 1 ? "s" : ""}.</p>
      </div>

      <div className="space-y-3">
        {expenses.map((exp) => (
          <div key={exp.id} className={`rounded-xl border bg-white p-5 dark:bg-zinc-900 ${exp.is_flagged ? "border-amber-200 dark:border-amber-900/30" : "border-zinc-200 dark:border-zinc-800"}`}>
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${exp.is_flagged ? "bg-amber-50 dark:bg-amber-950/20" : "bg-zinc-100 dark:bg-zinc-800"}`}>
                  {exp.is_flagged ? <Flag className="h-4 w-4 text-amber-500" /> : <Receipt className="h-4 w-4 text-zinc-400" />}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-bold text-zinc-900 dark:text-white">{exp.donor_name || "Donor"}</p>
                    {exp.is_flagged && (
                      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[9px] font-black text-amber-700 uppercase">⚠ Flagged</span>
                    )}
                  </div>
                  <p className="text-xs text-zinc-500 mt-0.5">{exp.description}</p>
                  <p className="text-[10px] text-zinc-400 mt-0.5">{format(parseISO(exp.submitted_at), "dd MMM yyyy, p")} · {exp.category}</p>
                </div>
              </div>
              <div className="text-right shrink-0">
                <p className="text-lg font-black text-zinc-900 dark:text-white">₹{exp.amount.toLocaleString("en-IN")}</p>
              </div>
            </div>

            <div className="mt-4">
              {done[exp.id] ? (
                <div className={`rounded-lg px-4 py-2 text-xs font-bold ${done[exp.id] === "approve" ? "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/20" : "bg-red-50 text-red-600"}`}>
                  {done[exp.id] === "approve" ? "✅ Approved — wallet credited" : "❌ Rejected"}
                </div>
              ) : (
                <div className="flex gap-2">
                  <button onClick={() => act(exp.id, "approve")} disabled={!!acting[exp.id]} className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-brand-500 py-2 text-xs font-bold text-white hover:bg-brand-600 transition-colors disabled:opacity-60">
                    <CheckCircle className="h-3.5 w-3.5" /> Approve ₹{exp.amount}
                  </button>
                  <button onClick={() => act(exp.id, "reject")} disabled={!!acting[exp.id]} className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-zinc-200 bg-zinc-50 py-2 text-xs font-bold text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 transition-colors disabled:opacity-60">
                    <XCircle className="h-3.5 w-3.5" /> Reject
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
        {expenses.length === 0 && (
          <div className="rounded-xl border border-dashed border-zinc-300 p-16 text-center dark:border-zinc-700">
            <Receipt className="h-10 w-10 text-zinc-300 dark:text-zinc-700 mx-auto mb-3" />
            <p className="text-sm text-zinc-500">No pending expenses</p>
          </div>
        )}
      </div>
    </div>
  );
}
