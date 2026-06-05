"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../../../lib/api/client";
import { Wallet, ArrowUpRight, ArrowDownLeft, Loader2, IndianRupee } from "lucide-react";
import { format, parseISO } from "date-fns";

interface WalletData { id: string; balance: number; currency: string; }
interface Transaction { id: string; type: "credit" | "debit"; amount: number; description: string; category: string; status: string; created_at: string; }

const CATEGORY_LABELS: Record<string, string> = { reimbursement: "Reimbursement", allowance: "Allowance", withdrawal: "Withdrawal", reward: "Reward", correction: "Correction" };

export default function PatientWalletPage() {
  const [wallet, setWallet] = useState<WalletData | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const [wRes, tRes] = await Promise.all([
          apiClient.get("/wallets/me"),
          apiClient.get("/wallets/me/transactions"),
        ]);
        if (wRes.data) {
          setWallet({
            ...wRes.data,
            balance: parseFloat(wRes.data.balance) || 0,
          });
        } else {
          setWallet(null);
        }
        const txList = Array.isArray(tRes.data) ? tRes.data : tRes.data?.items || [];
        const mappedTx = txList.map((tx: any) => ({
          ...tx,
          amount: parseFloat(tx.amount) || 0,
        }));
        setTransactions(mappedTx);
      } catch {
        setWallet(null);
        setTransactions([]);
      } finally {
        setIsLoading(false);
      }
    };
    fetch();
  }, []);

  if (isLoading) return <div className="flex h-[80vh] items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-brand-500" /></div>;

  return (
    <div className="space-y-6 max-w-xl">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">My Wallet</h1>
        <p className="text-xs text-zinc-500 mt-0.5">Reimbursements, allowances and balance.</p>
      </div>

      {/* Balance Card */}
      <div className="rounded-2xl bg-gradient-to-br from-brand-500 via-brand-600 to-accent-600 p-6 text-white shadow-lg">
        <div className="flex items-center gap-2 mb-1 opacity-80">
          <Wallet className="h-4 w-4" />
          <span className="text-xs font-medium uppercase tracking-wider">Available Balance</span>
        </div>
        <div className="flex items-baseline gap-1 mt-2">
          <IndianRupee className="h-6 w-6" />
          <span className="text-4xl font-black">
            {(wallet?.balance ?? 0).toLocaleString("en-IN")}
          </span>
        </div>
        <p className="text-xs mt-3 opacity-70">Last updated just now</p>
      </div>

      {/* Transactions */}
      <div className="rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900 overflow-hidden">
        <div className="border-b border-zinc-100 dark:border-zinc-800 px-4 py-3">
          <h2 className="text-xs font-bold text-zinc-700 dark:text-zinc-300 uppercase tracking-wider">Transaction History</h2>
        </div>
        {transactions.length > 0 ? (
          <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {transactions.map((tx) => (
              <div key={tx.id} className="flex items-center gap-4 px-4 py-3">
                <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${tx.type === "credit" ? "bg-emerald-50 dark:bg-emerald-950/20" : "bg-red-50 dark:bg-red-950/20"}`}>
                  {tx.type === "credit"
                    ? <ArrowDownLeft className="h-4 w-4 text-emerald-500" />
                    : <ArrowUpRight className="h-4 w-4 text-red-400" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-zinc-900 dark:text-white truncate">{tx.description}</p>
                  <p className="text-[10px] text-zinc-400 mt-0.5">{CATEGORY_LABELS[tx.category] || tx.category} · {format(parseISO(tx.created_at), "dd MMM yyyy")}</p>
                </div>
                <span className={`text-sm font-bold ${tx.type === "credit" ? "text-emerald-600" : "text-red-500"}`}>
                  {tx.type === "credit" ? "+" : "−"}₹{tx.amount.toLocaleString("en-IN")}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Wallet className="h-10 w-10 text-zinc-300 dark:text-zinc-700 mb-3" />
            <p className="text-sm font-medium text-zinc-500">No transactions yet</p>
          </div>
        )}
      </div>
    </div>
  );
}
