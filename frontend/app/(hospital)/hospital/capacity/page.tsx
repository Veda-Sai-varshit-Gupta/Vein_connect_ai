"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../../../lib/api/client";
import { BedDouble, Loader2, Save } from "lucide-react";

interface Capacity {
  available_beds: number;
  occupied_beds: number;
  available_chairs: number;
  occupied_chairs: number;
  emergency_capacity_available: number;
  staff_available: boolean;
  last_updated_at?: string;
}

const DEFAULT_CAPACITY: Capacity = {
  available_beds: 0,
  occupied_beds: 0,
  available_chairs: 0,
  occupied_chairs: 0,
  emergency_capacity_available: 0,
  staff_available: true,
};

function GaugeBar({ used, total, label, color }: { used: number; total: number; label: string; color: string }) {
  const pct = total > 0 ? ((total - used) / total) * 100 : 0;
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs font-bold text-zinc-700 dark:text-zinc-300">{label}</p>
        <p className="text-xs font-black text-zinc-900 dark:text-white">{total - used} / {total} free</p>
      </div>
      <div className="h-3 w-full rounded-full bg-zinc-100 dark:bg-zinc-800 overflow-hidden">
        <div className={`h-full rounded-full ${color} transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <div className="flex justify-between mt-1">
        <p className="text-[10px] text-zinc-400">{used} occupied</p>
        <p className="text-[10px] text-zinc-400">{pct.toFixed(0)}% available</p>
      </div>
    </div>
  );
}

export default function HospitalCapacityPage() {
  const [capacity, setCapacity] = useState<Capacity | null>(null);
  const [form, setForm] = useState<Partial<Capacity>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hospitalId, setHospitalId] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        const meRes = await apiClient.get("/hospitals/me");
        const id = meRes.data?.id;
        setHospitalId(id);
        let cap: Capacity;
        try {
          const capRes = await apiClient.get("/hospitals/me/capacity");
          cap = capRes.data || DEFAULT_CAPACITY;
        } catch {
          cap = DEFAULT_CAPACITY;
        }
        setCapacity(cap);
        setForm({
          available_beds: cap.available_beds,
          occupied_beds: cap.occupied_beds,
          available_chairs: cap.available_chairs,
          occupied_chairs: cap.occupied_chairs,
          emergency_capacity_available: cap.emergency_capacity_available,
          staff_available: cap.staff_available,
        });
      } catch {
        setCapacity(DEFAULT_CAPACITY);
        setForm({
          available_beds: DEFAULT_CAPACITY.available_beds,
          occupied_beds: DEFAULT_CAPACITY.occupied_beds,
          available_chairs: DEFAULT_CAPACITY.available_chairs,
          occupied_chairs: DEFAULT_CAPACITY.occupied_chairs,
          emergency_capacity_available: DEFAULT_CAPACITY.emergency_capacity_available,
          staff_available: DEFAULT_CAPACITY.staff_available,
        });
      } finally {
        setIsLoading(false);
      }
    };
    fetch();
  }, []);

  const save = async () => {
    setError(null);
    const avBeds = form.available_beds ?? 0;
    const occBeds = form.occupied_beds ?? 0;
    const avChairs = form.available_chairs ?? 0;
    const occChairs = form.occupied_chairs ?? 0;

    const totBeds = avBeds + occBeds;
    const totChairs = avChairs + occChairs;

    if (totBeds > 0 && occBeds >= totBeds) {
      setError("Occupied beds must be less than total beds (Available beds must be at least 1).");
      return;
    }
    if (totChairs > 0 && occChairs >= totChairs) {
      setError("Occupied chairs must be less than total chairs (Available chairs must be at least 1).");
      return;
    }

    setSaving(true);
    try {
      if (hospitalId) {
        await apiClient.put(`/hospitals/me/capacity`, form);
      }
      setCapacity((prev) => prev ? { ...prev, ...form } : null);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err: any) {
      console.error("Failed to save capacity:", err);
      setError(err.response?.data?.detail || "Failed to save capacity changes.");
    } finally {
      setSaving(false);
    }
  };

  if (isLoading) return <div className="flex h-[80vh] items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-brand-500" /></div>;

  const c = capacity || DEFAULT_CAPACITY;
  return (
    <div className="space-y-6 max-w-xl">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">Capacity Management</h1>
        <p className="text-xs text-zinc-500 mt-0.5">Real-time beds, chairs and emergency slots.</p>
      </div>

      {/* Current Status */}
      <div className="grid grid-cols-1 gap-3">
        <GaugeBar used={c.occupied_beds} total={c.available_beds + c.occupied_beds} label="Transfusion Beds" color="bg-brand-500" />
        <GaugeBar used={c.occupied_chairs} total={c.available_chairs + c.occupied_chairs} label="Transfusion Chairs" color="bg-emerald-500" />
        <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex items-center justify-between">
            <p className="text-xs font-bold text-zinc-700 dark:text-zinc-300">Emergency Capacity</p>
            <span className={`rounded-full px-3 py-1 text-xs font-black ${c.emergency_capacity_available > 0 ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-600"}`}>
              {c.emergency_capacity_available} slots
            </span>
          </div>
        </div>
      </div>

      {/* Update Form */}
      <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
        <h2 className="text-sm font-bold text-zinc-900 dark:text-white mb-4">Update Capacity</h2>
        <div className="grid grid-cols-2 gap-3">
          {[
            { key: "available_beds", label: "Available Beds" },
            { key: "occupied_beds", label: "Occupied Beds" },
            { key: "available_chairs", label: "Available Chairs" },
            { key: "occupied_chairs", label: "Occupied Chairs" },
            { key: "emergency_capacity_available", label: "Emergency Slots" },
          ].map(({ key, label }) => (
            <div key={key}>
              <label className="block text-[10px] font-bold uppercase tracking-wider text-zinc-500 mb-1.5">{label}</label>
              <input
                type="number"
                min={0}
                value={(form as any)[key] ?? ""}
                onChange={(e) => setForm((prev) => ({ ...prev, [key]: parseInt(e.target.value) || 0 }))}
                className="w-full rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm text-zinc-900 outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
              />
            </div>
          ))}
        </div>
        <button
          onClick={save}
          disabled={saving}
          className="mt-4 flex items-center gap-2 rounded-lg bg-brand-500 px-5 py-2.5 text-xs font-bold text-white hover:bg-brand-600 transition-colors disabled:opacity-60"
        >
          {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
          Save Changes
        </button>
        {error && <p className="mt-2 text-xs font-semibold text-red-650 dark:text-red-400">⚠️ {error}</p>}
        {saved && <p className="mt-2 text-xs font-medium text-emerald-600">✅ Capacity updated successfully</p>}
      </div>
    </div>
  );
}
