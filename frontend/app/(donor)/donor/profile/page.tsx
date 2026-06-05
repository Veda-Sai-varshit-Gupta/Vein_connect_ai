"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../../../lib/api/client";
import { Loader2, User, FileText, Upload, Save, CheckCircle, AlertTriangle, IndianRupee, MapPin } from "lucide-react";
import { differenceInDays, addDays, parseISO, format } from "date-fns";

export default function DonorProfilePage() {
  const [donor, setDonor] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [name, setName] = useState("");
  const [upiId, setUpiId] = useState("");
  const [demandedReimbursement, setDemandedReimbursement] = useState(0);
  const [maxTravelDistance, setMaxTravelDistance] = useState(25);
  const [selectedDays, setSelectedDays] = useState<string[]>([]);
  const [selectedTimes, setSelectedTimes] = useState<string[]>([]);
  const [file, setFile] = useState<File | null>(null);

  const daysList = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const timesList = ["Morning", "Afternoon", "Evening"];

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setIsLoading(true);
      const res = await apiClient.get("/donors/me");
      const data = res.data;
      setDonor(data);
      setName(data.name || "");
      setUpiId(data.upi_id || "");
      setDemandedReimbursement(Number(data.demanded_reimbursement) || 0);
      setMaxTravelDistance(data.max_travel_distance_km || 25);
      setSelectedDays(data.preferred_days || []);
      setSelectedTimes(data.preferred_times || []);
    } catch (err: any) {
      console.error("Failed to fetch profile:", err);
      setError("Failed to load profile details. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!donor) return;
    setIsSaving(true);
    setError(null);
    setSaveSuccess(false);

    try {
      const res = await apiClient.put(`/donors/${donor.id}`, {
        name,
        upi_id: upiId,
        demanded_reimbursement: demandedReimbursement,
        max_travel_distance_km: maxTravelDistance,
        preferred_days: selectedDays,
        preferred_times: selectedTimes,
      });
      setDonor(res.data);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to update profile settings.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleUploadCertificate = async () => {
    if (!file) return;
    setIsUploading(true);
    setError(null);
    setUploadSuccess(false);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await apiClient.post("/donors/upload-clearance", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      setUploadSuccess(true);
      setFile(null);
      // Refresh profile data
      await fetchProfile();
      setTimeout(() => setUploadSuccess(false), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to upload medical certificate.");
    } finally {
      setIsUploading(false);
    }
  };

  const toggleDay = (day: string) => {
    setSelectedDays((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day]
    );
  };

  const toggleTime = (time: string) => {
    setSelectedTimes((prev) =>
      prev.includes(time) ? prev.filter((t) => t !== time) : [...prev, time]
    );
  };

  // Calculations for Medical Clearance Certificate
  const getCertificateStatus = () => {
    if (!donor || !donor.medical_clearance_at) {
      return {
        status: "Missing",
        color: "text-red-500 bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900/30",
        message: "No medical clearance certificate uploaded yet. You cannot be matched with patients.",
        icon: <AlertTriangle className="h-5 w-5 text-red-500" />,
        daysLeft: 0,
      };
    }

    const clearanceDate = parseISO(donor.medical_clearance_at);
    const expiryDate = addDays(clearanceDate, 180);
    const daysLeft = differenceInDays(expiryDate, new Date());

    if (daysLeft <= 0) {
      return {
        status: "Expired",
        color: "text-red-500 bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900/30",
        message: "Your medical certificate has expired. Please upload an updated certificate to remain eligible.",
        icon: <AlertTriangle className="h-5 w-5 text-red-500" />,
        daysLeft: 0,
      };
    }

    if (daysLeft < 30) {
      return {
        status: "Expiring Soon",
        color: "text-amber-500 bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-900/30",
        message: `Your certificate will expire in ${daysLeft} days. Please upload a new one soon.`,
        icon: <AlertTriangle className="h-5 w-5 text-amber-500" />,
        daysLeft,
      };
    }

    return {
      status: "Active",
      color: "text-emerald-500 bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-900/30",
      message: `Verified and active. Expires in ${daysLeft} days (on ${format(expiryDate, "dd MMM yyyy")}).`,
      icon: <CheckCircle className="h-5 w-5 text-emerald-500" />,
      daysLeft,
    };
  };

  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
      </div>
    );
  }

  const certStatus = getCertificateStatus();

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">Profile & Preferences</h1>
        <p className="text-xs text-zinc-500 mt-0.5">Manage your personal settings, standard reimbursement demand, and upload verification clearance.</p>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3.5 text-xs text-red-600 dark:border-red-900/30 dark:bg-red-950/20 dark:text-red-400">
          {error}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-3">
        {/* Left Column: Personal and Matching Settings */}
        <div className="md:col-span-2 space-y-6">
          <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900 shadow-sm">
            <h2 className="text-sm font-bold text-zinc-900 dark:text-white flex items-center gap-2 mb-4">
              <User className="h-4 w-4 text-brand-500" /> General Profile
            </h2>
            <form onSubmit={handleSaveProfile} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="text-[11px] font-bold text-zinc-500 uppercase tracking-wider block mb-1">Full Name</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full text-xs px-3 py-2 rounded-lg border border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950 text-zinc-900 dark:text-white focus:outline-none focus:border-brand-500 transition-colors"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-bold text-zinc-500 uppercase tracking-wider block mb-1">UPI ID for Reimbursement</label>
                  <input
                    type="text"
                    required
                    placeholder="name@upi"
                    value={upiId}
                    onChange={(e) => setUpiId(e.target.value)}
                    className="w-full text-xs px-3 py-2 rounded-lg border border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950 text-zinc-900 dark:text-white focus:outline-none focus:border-brand-500 transition-colors"
                  />
                </div>
              </div>

              {/* Slider for Demanded Reimbursement */}
              <div className="pt-2">
                <div className="flex justify-between items-center mb-1">
                  <label className="text-[11px] font-bold text-zinc-500 uppercase tracking-wider flex items-center gap-1">
                    <IndianRupee className="h-3 w-3" /> Demanded Reimbursement
                  </label>
                  <span className="text-xs font-black text-brand-500">₹{demandedReimbursement}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1500"
                  step="50"
                  value={demandedReimbursement}
                  onChange={(e) => setDemandedReimbursement(Number(e.target.value))}
                  className="w-full h-1.5 bg-zinc-200 dark:bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-brand-500"
                />
                <p className="text-[10px] text-zinc-400 mt-1">
                  * Keeping your demanded reimbursement fair (e.g. ₹500 or less to cover actual travel cost) increases your matching compatibility score.
                </p>
              </div>

              {/* Slider for Max Travel Distance */}
              <div className="pt-2">
                <div className="flex justify-between items-center mb-1">
                  <label className="text-[11px] font-bold text-zinc-500 uppercase tracking-wider flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5" /> Max Travel Distance
                  </label>
                  <span className="text-xs font-black text-brand-500">{maxTravelDistance} km</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="100"
                  step="5"
                  value={maxTravelDistance}
                  onChange={(e) => setMaxTravelDistance(Number(e.target.value))}
                  className="w-full h-1.5 bg-zinc-200 dark:bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-brand-500"
                />
              </div>

              {/* Preferred availability days */}
              <div>
                <label className="text-[11px] font-bold text-zinc-500 uppercase tracking-wider block mb-1.5">Preferred Availability Days</label>
                <div className="flex flex-wrap gap-2">
                  {daysList.map((day) => {
                    const isSelected = selectedDays.includes(day);
                    return (
                      <button
                        type="button"
                        key={day}
                        onClick={() => toggleDay(day)}
                        className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition-colors ${
                          isSelected
                            ? "bg-brand-500 text-white border-brand-500 hover:bg-brand-600"
                            : "bg-zinc-50 text-zinc-600 border-zinc-200 dark:bg-zinc-950 dark:text-zinc-400 dark:border-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-900"
                        }`}
                      >
                        {day}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Preferred availability times */}
              <div>
                <label className="text-[11px] font-bold text-zinc-500 uppercase tracking-wider block mb-1.5">Preferred Availability Times</label>
                <div className="flex gap-2">
                  {timesList.map((time) => {
                    const isSelected = selectedTimes.includes(time);
                    return (
                      <button
                        type="button"
                        key={time}
                        onClick={() => toggleTime(time)}
                        className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition-colors ${
                          isSelected
                            ? "bg-brand-500 text-white border-brand-500 hover:bg-brand-600"
                            : "bg-zinc-50 text-zinc-600 border-zinc-200 dark:bg-zinc-950 dark:text-zinc-400 dark:border-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-900"
                        }`}
                      >
                        {time}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-zinc-100 dark:border-zinc-800">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="availability"
                    checked={donor?.is_available || false}
                    onChange={async (e) => {
                      const active = e.target.checked;
                      try {
                        const res = await apiClient.patch(`/donors/${donor.id}/availability`, { is_available: active });
                        setDonor(res.data);
                      } catch {
                        // ignore/fallback
                      }
                    }}
                    className="rounded text-brand-500 focus:ring-brand-500"
                  />
                  <label htmlFor="availability" className="text-xs text-zinc-600 dark:text-zinc-400 cursor-pointer">
                    I am actively available for emergency matching
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={isSaving}
                  className="flex items-center gap-1.5 rounded-lg bg-brand-500 px-4 py-2 text-xs font-bold text-white hover:bg-brand-600 transition-colors disabled:opacity-50"
                >
                  {isSaving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                  {saveSuccess ? "Saved!" : "Save Profile"}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Right Column: Medical Clearance Certificate upload */}
        <div className="space-y-6">
          <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900 shadow-sm">
            <h2 className="text-sm font-bold text-zinc-900 dark:text-white flex items-center gap-2 mb-4">
              <FileText className="h-4 w-4 text-brand-500" /> Medical Clearance
            </h2>

            {/* Verification Status Card */}
            <div className={`rounded-xl border p-4 text-xs space-y-2 mb-5 ${certStatus.color}`}>
              <div className="flex items-center gap-2">
                {certStatus.icon}
                <span className="font-extrabold uppercase tracking-wide">Status: {certStatus.status}</span>
              </div>
              <p className="text-zinc-600 dark:text-zinc-400 text-[11px] leading-relaxed">{certStatus.message}</p>
              {donor?.medical_clearance_url && (
                <div className="pt-1.5">
                  <a
                    href={donor.medical_clearance_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[10px] font-bold underline hover:text-zinc-900"
                  >
                    View Current Certificate
                  </a>
                </div>
              )}
            </div>

            {/* File Upload Component */}
            <div className="space-y-4">
              <label className="text-[11px] font-bold text-zinc-500 uppercase tracking-wider block">
                Upload Proof Certificate
              </label>
              <div className="rounded-lg border border-dashed border-zinc-300 p-4 text-center dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-950/20 transition-colors relative cursor-pointer">
                <input
                  type="file"
                  accept="image/*,application/pdf"
                  onChange={handleFileChange}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <Upload className="h-6 w-6 text-zinc-400 mx-auto mb-2" />
                <p className="text-[11px] font-bold text-zinc-600 dark:text-zinc-400">
                  {file ? file.name : "Select Clearance Document"}
                </p>
                <p className="text-[9px] text-zinc-400 mt-1">PDF or image files up to 5MB</p>
              </div>

              <button
                type="button"
                onClick={handleUploadCertificate}
                disabled={isUploading || !file}
                className="w-full flex items-center justify-center gap-1.5 rounded-lg bg-brand-500 px-4 py-2 text-xs font-bold text-white hover:bg-brand-600 transition-colors disabled:opacity-50"
              >
                {isUploading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Upload className="h-3.5 w-3.5" />}
                {uploadSuccess ? "Uploaded!" : "Upload Certificate"}
              </button>

              <div className="rounded-lg bg-zinc-50 dark:bg-zinc-950 p-3 border border-zinc-100 dark:border-zinc-800 text-[10px] text-zinc-400 leading-normal">
                ⚠️ **Clearance Requirement**: To ensure patient safety, donors must submit a valid medical clearance certificate showing they are fit to donate. This certificate is automatically marked invalid after **6 months** and must be re-submitted. Ineligible donors are excluded from transfusion matching recommendations.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
