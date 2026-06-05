"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../../../lib/api/client";
import { Hospital, MapPin, Clock, Star, Loader2, Edit2, Save, X, Trash2 } from "lucide-react";

interface HospitalPref {
  id: string;
  preference_rank: number;
  hospital_id: string;
  hospital_name: string;
  city: string;
  state: string;
  opening_time?: string;
  closing_time?: string;
  contact_phone?: string;
}

interface HospitalItem {
  id: string;
  name: string;
  city: string;
  state: string;
  address?: string;
  operating_hours_start?: string;
  operating_hours_end?: string;
  coordinator_phone?: string;
}

export default function PatientHospitalsPage() {
  const [prefs, setPrefs] = useState<HospitalPref[]>([]);
  const [allHospitals, setAllHospitals] = useState<HospitalItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [selectedHospitals, setSelectedHospitals] = useState<string[]>(["", "", ""]);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPrefsAndHospitals = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const prefsRes = await apiClient.get("/patients/me/hospitals");
      const fetchedPrefs = prefsRes.data;
      setPrefs(Array.isArray(fetchedPrefs) ? fetchedPrefs : []);

      const hospitalsRes = await apiClient.get("/hospitals?page_size=100");
      const fetchedHospitals = Array.isArray(hospitalsRes.data)
        ? hospitalsRes.data
        : (hospitalsRes.data.items || []);
      setAllHospitals(fetchedHospitals);
    } catch (err: any) {
      console.error("Failed to load hospital data:", err);
      setPrefs([]);
      setError("Failed to load live preferences.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPrefsAndHospitals();
  }, []);

  const handleStartEdit = () => {
    const initialSelected = ["", "", ""];
    prefs.forEach((p) => {
      const idx = p.preference_rank - 1;
      if (idx >= 0 && idx < 3) {
        initialSelected[idx] = p.hospital_id;
      }
    });
    setSelectedHospitals(initialSelected);
    setIsEditing(true);
  };

  const handleSelectHospital = (index: number, val: string) => {
    const updated = [...selectedHospitals];
    updated[index] = val;
    setSelectedHospitals(updated);
  };

  const handleClearRank = (index: number) => {
    const updated = [...selectedHospitals];
    updated[index] = "";
    setSelectedHospitals(updated);
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);

    const payload = selectedHospitals
      .map((hospId, index) => ({
        hospital_id: hospId,
        preference_order: index + 1,
      }))
      .filter((item) => item.hospital_id !== "");

    if (payload.length === 0) {
      setError("Please select at least one preferred hospital.");
      setIsSaving(false);
      return;
    }

    try {
      const res = await apiClient.put("/patients/me/hospitals", payload);
      setPrefs(res.data);
      setIsEditing(false);
    } catch (err: any) {
      console.error("Failed to update preferences:", err);
      setError(
        err.response?.data?.detail || "Failed to update preferred hospitals. Please try again."
      );
    } finally {
      setIsSaving(false);
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
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">
            Hospital Preferences
          </h1>
          <p className="text-xs text-zinc-500 mt-0.5">
            Your ranked preferred hospitals for transfusions.
          </p>
        </div>
        {!isEditing && (
          <button
            onClick={handleStartEdit}
            className="flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-4 py-2 text-xs font-bold text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 transition-colors"
          >
            <Edit2 className="h-3.5 w-3.5" /> Edit Preferences
          </button>
        )}
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-xs text-red-800 dark:bg-red-950/20 dark:text-red-400">
          {error}
        </div>
      )}

      {isEditing ? (
        <div className="space-y-4 rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="text-sm font-bold text-zinc-900 dark:text-white mb-2">
            Configure Preferences (Select Up to 3)
          </h2>
          <div className="space-y-4">
            {[0, 1, 2].map((idx) => {
              const currentVal = selectedHospitals[idx];
              // Filter out hospitals selected in other dropdowns
              const disabledIds = selectedHospitals.filter((id, i) => i !== idx && id !== "");

              return (
                <div key={idx} className="flex items-center gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-50 dark:bg-brand-950/20">
                    <span className="text-sm font-black text-brand-500">#{idx + 1}</span>
                  </div>
                  <div className="flex-1">
                    <select
                      value={currentVal}
                      onChange={(e) => handleSelectHospital(idx, e.target.value)}
                      className="w-full rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs text-zinc-900 focus:border-brand-500 focus:bg-white focus:outline-none dark:border-zinc-800 dark:bg-zinc-950 dark:text-white"
                    >
                      <option value="">Select Hospital...</option>
                      {allHospitals.map((hosp) => {
                        const isDisabled = disabledIds.includes(hosp.id);
                        return (
                          <option key={hosp.id} value={hosp.id} disabled={isDisabled}>
                            {hosp.name} {hosp.city ? `(${hosp.city})` : ""}
                          </option>
                        );
                      })}
                    </select>
                  </div>
                  {currentVal && (
                    <button
                      onClick={() => handleClearRank(idx)}
                      className="p-2 text-zinc-400 hover:text-red-500 hover:bg-zinc-50 dark:hover:bg-zinc-800 rounded-md transition-colors"
                      title="Clear Rank"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          <div className="mt-6 flex justify-end gap-3 border-t pt-4 dark:border-zinc-800">
            <button
              onClick={() => setIsEditing(false)}
              className="flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-4 py-2 text-xs font-semibold text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 transition-colors"
            >
              <X className="h-3.5 w-3.5" /> Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="flex items-center gap-2 rounded-lg bg-brand-500 px-5 py-2 text-xs font-bold text-white hover:bg-brand-600 disabled:opacity-50 transition-colors"
            >
              {isSaving ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" /> Saving...
                </>
              ) : (
                <>
                  <Save className="h-3.5 w-3.5" /> Save Choices
                </>
              )}
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {prefs.map((pref) => (
            <div
              key={pref.id}
              className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900 flex items-start gap-4 transition-all hover:shadow-sm"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-50 dark:bg-brand-950/20">
                <span className="text-sm font-black text-brand-500">#{pref.preference_rank}</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <Hospital className="h-4 w-4 text-zinc-400" />
                  <p className="text-sm font-bold text-zinc-900 dark:text-white">
                    {pref.hospital_name || "Preferred Hospital"}
                  </p>
                  {pref.preference_rank === 1 && (
                    <span className="flex items-center gap-0.5 rounded-full bg-amber-100 px-2 py-0.5 text-[9px] font-bold text-amber-700">
                      <Star className="h-2.5 w-2.5" fill="currentColor" /> Primary
                    </span>
                  )}
                </div>
                <div className="mt-2 flex flex-wrap gap-3 text-xs text-zinc-500">
                  {(pref.city || pref.state) && (
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3.5 w-3.5" /> {pref.city || ""}, {pref.state || ""}
                    </span>
                  )}
                  {pref.opening_time && (
                    <span className="flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5" /> {pref.opening_time} – {pref.closing_time}
                    </span>
                  )}
                  {pref.contact_phone && (
                    <span className="text-zinc-400">Tel: {pref.contact_phone}</span>
                  )}
                </div>
              </div>
            </div>
          ))}

          {prefs.length === 0 && (
            <div className="rounded-xl border border-dashed border-zinc-300 p-10 text-center dark:border-zinc-700">
              <Hospital className="h-10 w-10 text-zinc-300 dark:text-zinc-700 mx-auto mb-3" />
              <p className="text-sm font-medium text-zinc-500">No hospital preferences set</p>
              <p className="text-xs text-zinc-400 mt-1">Add preferred hospitals for faster scheduling.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
