"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../../../lib/api/client";
import { Award, Star, Zap, Loader2, IndianRupee } from "lucide-react";
import { format, parseISO } from "date-fns";

interface RewardSummary {
  total_points: number;
  tier: string;
  tier_level: number;
  points_to_next_tier: number;
  next_tier: string | null;
}

interface RewardEntry {
  id: string;
  type: string;
  points: number;
  description: string;
  created_at: string;
}

const TIER_COLORS: Record<string, string> = {
  Bronze: "text-amber-700 bg-amber-100",
  Silver: "text-zinc-600 bg-zinc-100 dark:text-zinc-400 dark:bg-zinc-800",
  Gold: "text-yellow-700 bg-yellow-100",
  Platinum: "text-blue-700 bg-blue-100",
};

export default function DonorRewardsPage() {
  const [summary, setSummary] = useState<RewardSummary | null>(null);
  const [history, setHistory] = useState<RewardEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [converting, setConverting] = useState(false);
  const [convertMsg, setConvertMsg] = useState("");

  const loadData = async () => {
    try {
      const [sRes, hRes] = await Promise.all([
        apiClient.get("/rewards/me/summary"),
        apiClient.get("/rewards/me/history"),
      ]);
      setSummary(sRes.data);
      setHistory(Array.isArray(hRes.data) ? hRes.data : []);
    } catch {
      setSummary(null);
      setHistory([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const convertPoints = async () => {
    if (!summary || summary.total_points < 100) return;
    setConverting(true);
    setConvertMsg("");
    try {
      await apiClient.post("/rewards/convert", { points: summary.total_points });
      const rupees = (summary.total_points * 0.5).toFixed(0);
      setConvertMsg(`✅ ₹${rupees} credited to your wallet!`);
      await loadData();
    } catch (err: any) {
      console.error("Conversion failed:", err);
      const errMsg = err?.response?.data?.detail || "Point conversion failed. Please try again later.";
      setConvertMsg(`❌ Error: ${errMsg}`);
    } finally {
      setConverting(false);
    }
  };

  if (isLoading) return <div className="flex h-[80vh] items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-brand-500" /></div>;

  const tierProgress = summary ? Math.min(100, ((summary.total_points % 500) / 500) * 100) : 0;

  return (
    <div className="space-y-6 max-w-xl">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">Rewards Center</h1>
        <p className="text-xs text-zinc-500 mt-0.5">Earn points for every donation. Redeem for cash.</p>
      </div>

      {/* Points Card */}
      <div className="rounded-2xl bg-gradient-to-br from-amber-400 via-orange-500 to-brand-500 p-6 text-white shadow-lg">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1 opacity-80">
              <Award className="h-4 w-4" />
              <span className="text-xs font-medium uppercase tracking-wider">Total Points</span>
            </div>
            <div className="flex items-baseline gap-2 mt-2">
              <span className="text-5xl font-black">{(summary?.total_points ?? 0).toLocaleString()}</span>
              <span className="text-sm opacity-80">pts</span>
            </div>
          </div>
          <div className="text-right">
            <span className={`rounded-full px-3 py-1 text-xs font-black ${TIER_COLORS[summary?.tier || "Bronze"]}`}>
              ⭐ {summary?.tier || "Bronze"}
            </span>
            {summary?.next_tier && (
              <p className="text-[10px] opacity-70 mt-2">{summary.points_to_next_tier} pts to {summary.next_tier}</p>
            )}
          </div>
        </div>
        {/* Progress Bar */}
        <div className="mt-4 h-2 w-full rounded-full bg-white/20 overflow-hidden">
          <div className="h-full rounded-full bg-white transition-all" style={{ width: `${tierProgress}%` }} />
        </div>
        <div className="mt-3 flex items-center justify-between text-[10px] opacity-70">
          <span>1 point = ₹0.50</span>
          <span>{summary?.total_points ?? 0} pts = ₹{((summary?.total_points ?? 0) * 0.5).toFixed(0)}</span>
        </div>
      </div>

      {convertMsg ? (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700 dark:bg-emerald-950/20 dark:border-emerald-900/30">{convertMsg}</div>
      ) : (
        <button
          onClick={convertPoints}
          disabled={converting || (summary?.total_points ?? 0) < 100}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-zinc-900 py-3 text-sm font-bold text-white hover:bg-zinc-800 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-100 transition-colors disabled:opacity-40"
        >
          {converting ? <Loader2 className="h-4 w-4 animate-spin" /> : <IndianRupee className="h-4 w-4" />}
          Convert {summary?.total_points ?? 0} Points → ₹{((summary?.total_points ?? 0) * 0.5).toFixed(0)}
        </button>
      )}

      {/* History */}
      <div className="rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900 overflow-hidden">
        <div className="border-b border-zinc-100 dark:border-zinc-800 px-4 py-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-600 dark:text-zinc-400">Points History</h2>
        </div>
        {history.length > 0 ? (
          <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {history.map((r) => (
              <div key={r.id} className="flex items-center gap-3 px-4 py-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-amber-50 dark:bg-amber-950/20">
                  <Zap className="h-4 w-4 text-amber-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-zinc-900 dark:text-white">{r.description}</p>
                  <p className="text-[10px] text-zinc-400 mt-0.5">{format(parseISO(r.created_at), "dd MMM yyyy")}</p>
                </div>
                <span className="text-sm font-bold text-amber-600">+{r.points}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-12 text-center">
            <Award className="h-10 w-10 text-zinc-300 dark:text-zinc-700 mx-auto mb-3" />
            <p className="text-sm text-zinc-500">No rewards yet. Start donating!</p>
          </div>
        )}
      </div>
    </div>
  );
}
