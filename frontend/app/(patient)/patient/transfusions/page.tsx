"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiClient } from "../../../../lib/api/client";
import { Transfusion, TransfusionStatus } from "../../../../lib/types/common";
import { Activity, Clock, ArrowRight, Loader2, Plus, AlertCircle } from "lucide-react";
import { format, parseISO } from "date-fns";

const STATUS_STYLES: Record<string, string> = {
  predicted: "bg-slate-100 text-slate-600 dark:bg-slate-900/30 dark:text-slate-400",
  patient_confirmed: "bg-brand-50 text-brand-600 dark:bg-brand-950/20 dark:text-brand-400",
  matching_donors: "bg-amber-50 text-amber-700",
  donor_confirmed: "bg-blue-50 text-blue-600",
  coordinator_confirmed: "bg-blue-100 text-blue-800",
  hospital_confirmed: "bg-indigo-100 text-indigo-700",
  scheduled: "bg-emerald-50 text-emerald-600",
  in_progress: "bg-amber-100 text-amber-800",
  completed: "bg-emerald-100 text-emerald-700",
  cancelled: "bg-red-50 text-red-600",
  failed: "bg-red-100 text-red-700",
};

const STATUS_LABELS: Record<string, string> = {
  predicted: "AI Predicted",
  patient_confirmed: "Confirmed",
  matching_donors: "Finding Donor",
  donor_confirmed: "Donor Set",
  coordinator_confirmed: "Coord. Confirmed",
  hospital_confirmed: "Hospital Confirmed",
  scheduled: "Scheduled",
  in_progress: "In Progress",
  completed: "Completed",
  cancelled: "Cancelled",
  failed: "Failed",
};

const URGENCY_STYLES: Record<string, string> = {
  routine: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
  urgent: "bg-amber-100 text-amber-700",
  emergency: "bg-red-100 text-red-700",
};

export default function PatientTransfusionsPage() {
  const todayString = new Date().toISOString().split("T")[0];
  const [transfusions, setTransfusions] = useState<Transfusion[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hospitals, setHospitals] = useState<any[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    predicted_date: "",
    urgency_level: "routine",
    hospital_id: "",
    notes: "",
    emergency_reason: ""
  });
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchTransfusions = async () => {
    try {
      const res = await apiClient.get("/transfusions");
      const data = res.data?.items || res.data || [];
      setTransfusions(Array.isArray(data) ? data : []);
    } catch {
      setTransfusions([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTransfusions();

    const fetchHospitals = async () => {
      try {
        const res = await apiClient.get("/patients/me/hospitals");
        const mapped = (res.data || []).map((p: any) => ({
          id: p.hospital_id,
          name: p.hospital_name || "Hospital",
          city: p.city || "",
        }));
        setHospitals(mapped);
      } catch (err) {
        console.warn("Failed to fetch preferred hospitals, using all hospitals list fallback", err);
        try {
          const resAll = await apiClient.get("/hospitals");
          const dataAll = resAll.data?.items || resAll.data || [];
          const mapped = dataAll.map((h: any) => ({
            id: h.id,
            name: h.name,
            city: h.city || "",
          }));
          setHospitals(mapped);
        } catch {
          setHospitals([]);
        }
      }
    };
    fetchHospitals();
  }, []);

  useEffect(() => {
    if (hospitals.length > 0 && !formData.hospital_id) {
      setFormData(prev => ({ ...prev, hospital_id: hospitals[0].id }));
    }
  }, [hospitals]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.predicted_date) {
      setErrorMsg("Please select a predicted date.");
      return;
    }
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const selectedDate = new Date(formData.predicted_date);
    selectedDate.setHours(0, 0, 0, 0);
    if (selectedDate < today) {
      setErrorMsg("Predicted date cannot be in the past.");
      return;
    }
    if (!formData.hospital_id) {
      setErrorMsg("Please select a hospital.");
      return;
    }

    setSubmitting(true);
    setErrorMsg("");

    const isEmergency = formData.urgency_level === "emergency";
    try {
      await apiClient.post("/transfusions", {
        predicted_date: formData.predicted_date,
        urgency_level: formData.urgency_level,
        hospital_id: formData.hospital_id,
        is_emergency: isEmergency,
        emergency_reason: isEmergency ? formData.emergency_reason : null,
        notes: formData.notes
      });
      
      setFormData({
        predicted_date: "",
        urgency_level: "routine",
        hospital_id: hospitals[0]?.hospital?.id || "",
        notes: "",
        emergency_reason: ""
      });
      setShowModal(false);
      fetchTransfusions();
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || "Failed to create transfusion request.");
    } finally {
      setSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">
            My Transfusions
          </h1>
          <p className="text-xs text-zinc-500 mt-0.5">
            Full history and active coordination runs.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 rounded-lg bg-brand-500 px-4 py-2 text-xs font-bold text-white hover:bg-brand-600 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          Request Transfusion
        </button>
      </div>

      <div className="rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900 overflow-hidden">
        {transfusions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-zinc-100 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950/50">
                  <th className="py-3 px-4 text-[10px] font-bold uppercase tracking-wider text-zinc-400">Run ID</th>
                  <th className="py-3 px-4 text-[10px] font-bold uppercase tracking-wider text-zinc-400">Date</th>
                  <th className="py-3 px-4 text-[10px] font-bold uppercase tracking-wider text-zinc-400">Status</th>
                  <th className="py-3 px-4 text-[10px] font-bold uppercase tracking-wider text-zinc-400">Urgency</th>
                  <th className="py-3 px-4 text-[10px] font-bold uppercase tracking-wider text-zinc-400">Donor</th>
                  <th className="py-3 px-4 text-[10px] font-bold uppercase tracking-wider text-zinc-400"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {transfusions.map((t) => (
                  <tr key={t.id} className="hover:bg-zinc-50/50 dark:hover:bg-zinc-900/30 transition-colors">
                    <td className="py-3 px-4 text-xs font-bold text-zinc-900 dark:text-white font-mono">
                      #{String(t.id).slice(0, 14)}
                    </td>
                    <td className="py-3 px-4 text-xs text-zinc-700 dark:text-zinc-300">
                      <div className="flex items-center gap-1.5">
                        <Clock className="h-3.5 w-3.5 text-zinc-400" />
                        {t.scheduled_date
                          ? format(parseISO(t.scheduled_date), "dd MMM yyyy")
                          : "—"}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${STATUS_STYLES[t.status] || "bg-zinc-100 text-zinc-600"}`}>
                        {STATUS_LABELS[t.status] || t.status}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${URGENCY_STYLES[t.urgency_level] || ""}`}>
                        {t.urgency_level}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-xs text-zinc-500">
                      {t.donor_id ? "Matched" : "Pending"}
                    </td>
                    <td className="py-3 px-4">
                      <Link
                        href={`/patient/transfusions/${t.id}`}
                        className="flex items-center gap-1 text-[10px] font-bold text-brand-500 hover:text-brand-600"
                      >
                        View <ArrowRight className="h-3 w-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Activity className="h-10 w-10 text-zinc-300 dark:text-zinc-700 mb-3" />
            <p className="text-sm font-medium text-zinc-500">No transfusions found</p>
            <p className="text-xs text-zinc-400 mt-1">Your transfusion history will appear here.</p>
          </div>
        )}
      </div>

      {/* Request Transfusion Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/60 backdrop-blur-sm">
          <div className="relative w-full max-w-md rounded-xl border border-zinc-200 bg-white p-6 shadow-xl dark:border-zinc-800 dark:bg-zinc-950 animate-in fade-in zoom-in-95 duration-200">
            <h2 className="text-lg font-bold text-zinc-900 dark:text-white">Request Transfusion</h2>
            <p className="text-xs text-zinc-500 mt-1">Submit a new predicted transfusion run. The AI will automatically assign a compatible donor matching your blood type.</p>
            
            <form onSubmit={handleSubmit} className="mt-4 space-y-4">
              {errorMsg && (
                <div className="rounded-lg bg-red-50 p-3 text-xs text-red-600 border border-red-100 dark:bg-red-950/20 dark:border-red-900/30 dark:text-red-400">
                  {errorMsg}
                </div>
              )}

              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-zinc-400">Predicted Date</label>
                <input
                  type="date"
                  min={todayString}
                  value={formData.predicted_date}
                  onChange={(e) => setFormData(prev => ({ ...prev, predicted_date: e.target.value }))}
                  className="mt-1 block w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm bg-white dark:border-zinc-800 dark:bg-zinc-900 text-zinc-900 dark:text-white focus:outline-none focus:border-brand-500"
                  required
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-zinc-400">Urgency Level</label>
                <select
                  value={formData.urgency_level}
                  onChange={(e) => setFormData(prev => ({ ...prev, urgency_level: e.target.value }))}
                  className="mt-1 block w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm bg-white dark:border-zinc-800 dark:bg-zinc-900 text-zinc-900 dark:text-white focus:outline-none focus:border-brand-500"
                >
                  <option value="routine">Routine</option>
                  <option value="urgent">Urgent</option>
                  <option value="emergency">Emergency</option>
                </select>
              </div>

              {formData.urgency_level === "emergency" && (
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-zinc-400">Emergency Reason</label>
                  <textarea
                    value={formData.emergency_reason}
                    onChange={(e) => setFormData(prev => ({ ...prev, emergency_reason: e.target.value }))}
                    placeholder="Specify why this is an emergency..."
                    className="mt-1 block w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm bg-white dark:border-zinc-800 dark:bg-zinc-900 text-zinc-900 dark:text-white focus:outline-none focus:border-brand-500 min-h-[60px]"
                    required
                  />
                </div>
              )}

              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-zinc-400">Preferred Hospital</label>
                <select
                  value={formData.hospital_id}
                  onChange={(e) => setFormData(prev => ({ ...prev, hospital_id: e.target.value }))}
                  className="mt-1 block w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm bg-white dark:border-zinc-800 dark:bg-zinc-900 text-zinc-900 dark:text-white focus:outline-none focus:border-brand-500"
                  required
                >
                  <option value="" disabled>Select a hospital...</option>
                  {hospitals.map((h: any) => (
                    <option key={h.id} value={h.id}>
                      {h.name} {h.city ? `(${h.city})` : ""}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-zinc-400">Additional Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                  placeholder="Any extra instructions or notes..."
                  className="mt-1 block w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm bg-white dark:border-zinc-800 dark:bg-zinc-900 text-zinc-900 dark:text-white focus:outline-none focus:border-brand-500 min-h-[60px]"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  disabled={submitting}
                  className="flex-1 rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900 px-4 py-2 text-xs font-bold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex-1 rounded-lg bg-brand-500 hover:bg-brand-600 text-white px-4 py-2 text-xs font-bold transition-colors disabled:opacity-50"
                >
                  {submitting ? "Submitting..." : "Submit Request"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
