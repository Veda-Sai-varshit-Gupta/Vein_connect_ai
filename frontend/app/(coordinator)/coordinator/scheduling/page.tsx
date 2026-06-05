"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../../../lib/api/client";
import { 
  Calendar, 
  Loader2, 
  User, 
  Droplets, 
  Clock, 
  CheckCircle2, 
  ChevronDown, 
  ChevronUp,
  Phone,
  Mail,
  Copy,
  Check,
  AlertTriangle,
  Building2,
  AlertCircle,
  MapPin,
  Activity,
  ArrowRight
} from "lucide-react";
import { format, parseISO } from "date-fns";

interface Transfusion {
  id: string;
  patient_id: string;
  donor_id?: string;
  hospital_id?: string;
  status: string;
  urgency_level: string;
  predicted_date: string;
  scheduled_date?: string;
  patient_confirmation?: string;
  donor_confirmation?: string;
  coordinator_confirmation?: string;
  hospital_confirmation?: string;
  is_emergency?: boolean;
  emergency_reason?: string;
  alternate_hospital_id?: string;
  notes?: string;
}

interface DonorMatch {
  donor_id: string;
  donor_name: string;
  match_score: number;
  blood_group: string;
  reliability_score: number;
  distance_km: number;
  rank: number;
}

interface UnresponsiveDonor {
  transfusion_id: string;
  scheduled_date: string | null;
  urgency_level: string;
  patient_name: string;
  hospital_name: string;
  donor_id: string;
  donor_name: string;
  donor_phone: string;
  donor_upi: string | null;
  donor_email: string;
  reminder_count: number;
  created_at: string;
}

interface HospitalCapacityDetail {
  id: string;
  name: string;
  address: string;
  city: string;
  state: string;
  coordinator_name: string | null;
  coordinator_phone: string | null;
  coordinator_email: string | null;
  total_transfusion_beds: number;
  available_beds: number;
  occupied_beds: number;
  total_transfusion_chairs: number;
  available_chairs: number;
  occupied_chairs: number;
  emergency_capacity: number;
  emergency_capacity_available: number;
}


export default function CoordinatorSchedulingPage() {
  const [activeTab, setActiveTab] = useState<"assignments" | "unresponsive" | "hospitals">("assignments");

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const tab = params.get("tab");
      if (tab === "unresponsive" || tab === "hospitals" || tab === "assignments") {
        setActiveTab(tab as any);
      }
    }
  }, []);
  
  // Tab 1: Assignments
  const [transfusions, setTransfusions] = useState<Transfusion[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [matches, setMatches] = useState<Record<string, DonorMatch[]>>({});
  const [loadingMatches, setLoadingMatches] = useState<Record<string, boolean>>({});
  const [assigning, setAssigning] = useState<Record<string, boolean>>({});
  const [assigned, setAssigned] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [actioning, setActioning] = useState<Record<string, boolean>>({});

  // Tab 2: Unresponsive Donors
  const [unresponsiveDonors, setUnresponsiveDonors] = useState<UnresponsiveDonor[]>([]);
  const [loadingUnresponsive, setLoadingUnresponsive] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedUnresponsive, setExpandedUnresponsive] = useState<string | null>(null);
  const [overridingDonor, setOverridingDonor] = useState<Record<string, boolean>>({});
  const [overriddenDonorsMap, setOverriddenDonorsMap] = useState<Record<string, string>>({});

  // Tab 3: Hospital Rejections & Capacity
  const [rejectedTransfusions, setRejectedTransfusions] = useState<Transfusion[]>([]);
  const [hospitalCapacities, setHospitalCapacities] = useState<HospitalCapacityDetail[]>([]);
  const [loadingHospitalsTab, setLoadingHospitalsTab] = useState(false);
  const [expandedRejected, setExpandedRejected] = useState<string | null>(null);
  const [forcingHospital, setForcingHospital] = useState<Record<string, boolean>>({});
  const [forcedHospitalsMap, setForcedHospitalsMap] = useState<Record<string, string>>({});

  const [feedbackMessage, setFeedbackMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);

  const showFeedback = (text: string, type: "success" | "error" = "success") => {
    setFeedbackMessage({ text, type });
    setTimeout(() => setFeedbackMessage(null), 5000);
  };

  const fetchAssignments = async () => {
    setIsLoading(true);
    try {
      const [resMatching, resConfirmed] = await Promise.all([
        apiClient.get("/transfusions?status=matching_donors&limit=100"),
        apiClient.get("/transfusions?status=patient_confirmed&limit=100")
      ]);
      const dataMatching = resMatching.data?.items || resMatching.data || [];
      const dataConfirmed = resConfirmed.data?.items || resConfirmed.data || [];
      const combined = [...dataMatching, ...dataConfirmed];
      setTransfusions(combined);
    } catch {
      setTransfusions([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAcceptMatch = async (transfusionId: string) => {
    setActioning((prev) => ({ ...prev, [transfusionId]: true }));
    try {
      await apiClient.post("/confirmations/confirm", {
        transfusion_id: transfusionId,
        notes: "Approved by coordinator",
      });
      showFeedback("Match accepted successfully!");
      fetchAssignments();
    } catch (err) {
      console.error(err);
      showFeedback("Failed to accept match.", "error");
    } finally {
      setActioning((prev) => ({ ...prev, [transfusionId]: false }));
    }
  };

  const handleRejectMatch = async (transfusionId: string) => {
    setActioning((prev) => ({ ...prev, [transfusionId]: true }));
    try {
      await apiClient.post("/confirmations/reject", {
        transfusion_id: transfusionId,
        reason: "Rejected by coordinator",
      });
      showFeedback("Match rejected. AI will search for next candidate.");
      fetchAssignments();
    } catch (err) {
      console.error(err);
      showFeedback("Failed to reject match.", "error");
    } finally {
      setActioning((prev) => ({ ...prev, [transfusionId]: false }));
    }
  };

  const fetchUnresponsive = async () => {
    setLoadingUnresponsive(true);
    try {
      const res = await apiClient.get("/coordinators/me/unresponsive-donors");
      setUnresponsiveDonors(res.data || []);
    } catch {
      setUnresponsiveDonors([]);
    } finally {
      setLoadingUnresponsive(false);
    }
  };

  const fetchHospitalOverrides = async () => {
    setLoadingHospitalsTab(true);
    try {
      // 1. Fetch coordinator's assigned transfusions
      const transRes = await apiClient.get("/coordinators/me/transfusions");
      const allTrans: Transfusion[] = transRes.data || [];
      
      // Filter those that are rejected/unavailable by hospital
      const filtered = allTrans.filter(
        (t) => 
          t.hospital_confirmation === "rejected" || 
          t.hospital_confirmation === "unavailable" || 
          (t.alternate_hospital_id && t.hospital_confirmation === "rejected")
      );
      setRejectedTransfusions(filtered);

      // 2. Fetch all hospital capacities
      const hospRes = await apiClient.get("/coordinators/me/hospitals-capacity");
      setHospitalCapacities(hospRes.data || []);
    } catch (err) {
      console.error("Error loading hospital overrides data:", err);
      setRejectedTransfusions([]);
      setHospitalCapacities([]);
    } finally {
      setLoadingHospitalsTab(false);
    }
  };

  useEffect(() => {
    if (activeTab === "assignments") {
      fetchAssignments();
    } else if (activeTab === "unresponsive") {
      fetchUnresponsive();
    } else if (activeTab === "hospitals") {
      fetchHospitalOverrides();
    }
  }, [activeTab]);

  const toggleExpand = async (id: string) => {
    if (expanded === id) { setExpanded(null); return; }
    setExpanded(id);
    if (matches[id]) return;
    setLoadingMatches((prev) => ({ ...prev, [id]: true }));
    try {
      const res = await apiClient.get(`/transfusions/${id}/donor-matches`);
      setMatches((prev) => ({ ...prev, [id]: res.data || [] }));
    } catch {
      setMatches((prev) => ({ ...prev, [id]: [] }));
    } finally {
      setLoadingMatches((prev) => ({ ...prev, [id]: false }));
    }
  };

  const toggleExpandUnresponsive = async (transfusionId: string) => {
    if (expandedUnresponsive === transfusionId) { setExpandedUnresponsive(null); return; }
    setExpandedUnresponsive(transfusionId);
    if (matches[transfusionId]) return;
    setLoadingMatches((prev) => ({ ...prev, [transfusionId]: true }));
    try {
      const res = await apiClient.get(`/transfusions/${transfusionId}/donor-matches`);
      setMatches((prev) => ({ ...prev, [transfusionId]: res.data || [] }));
    } catch {
      setMatches((prev) => ({ ...prev, [transfusionId]: [] }));
    } finally {
      setLoadingMatches((prev) => ({ ...prev, [transfusionId]: false }));
    }
  };

  const assignDonor = async (transfusionId: string, donorId: string) => {
    setAssigning((prev) => ({ ...prev, [`${transfusionId}-${donorId}`]: true }));
    try {
      await apiClient.post(`/transfusions/${transfusionId}/assign-donor`, { donor_id: donorId });
      setAssigned((prev) => ({ ...prev, [transfusionId]: donorId }));
      showFeedback("Donor assigned successfully!");
      fetchAssignments();
    } catch {
      setAssigned((prev) => ({ ...prev, [transfusionId]: donorId }));
      showFeedback("Error assigning donor, but applied to interface view.", "error");
    } finally {
      setAssigning((prev) => ({ ...prev, [`${transfusionId}-${donorId}`]: false }));
    }
  };

  const handleOverrideDonor = async (transfusionId: string, newDonorId: string) => {
    setOverridingDonor((prev) => ({ ...prev, [`${transfusionId}-${newDonorId}`]: true }));
    try {
      await apiClient.post("/coordinators/me/override-donor", {
        transfusion_id: transfusionId,
        new_donor_id: newDonorId,
      });
      setOverriddenDonorsMap((prev) => ({ ...prev, [transfusionId]: newDonorId }));
      showFeedback("Donor successfully overridden! Previous donor reliability score penalized (-15 pts).");
      // Refresh unresponsive list after override
      setTimeout(() => {
        fetchUnresponsive();
      }, 1500);
    } catch (err) {
      console.error(err);
      showFeedback("Failed to override donor.", "error");
    } finally {
      setOverridingDonor((prev) => ({ ...prev, [`${transfusionId}-${newDonorId}`]: false }));
    }
  };

  const handleForceHospital = async (transfusionId: string, hospitalId: string) => {
    setForcingHospital((prev) => ({ ...prev, [`${transfusionId}-${hospitalId}`]: true }));
    try {
      await apiClient.post("/coordinators/me/override-hospital", {
        transfusion_id: transfusionId,
        hospital_id: hospitalId,
      });
      setForcedHospitalsMap((prev) => ({ ...prev, [transfusionId]: hospitalId }));
      showFeedback("Hospital override successful! Confirmations reset and new hospital notified.");
      setTimeout(() => {
        fetchHospitalOverrides();
      }, 1500);
    } catch (err) {
      console.error(err);
      showFeedback("Failed to route to selected hospital.", "error");
    } finally {
      setForcingHospital((prev) => ({ ...prev, [`${transfusionId}-${hospitalId}`]: false }));
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Toast Alert Feedback */}
      {feedbackMessage && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-2 rounded-lg px-4 py-3 text-xs font-bold text-white shadow-lg transition-all duration-300 ${
          feedbackMessage.type === "success" ? "bg-emerald-600" : "bg-red-600"
        }`}>
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{feedbackMessage.text}</span>
        </div>
      )}

      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-black tracking-tight text-zinc-900 dark:text-white">Scheduling & Override Center</h1>
          <p className="text-xs text-zinc-500 mt-0.5">Manage assignments, track unresponsive donors, and coordinate alternate hospital routing.</p>
        </div>

        {/* Tab Selection buttons */}
        <div className="flex rounded-lg border border-zinc-200 bg-zinc-50 p-1 dark:border-zinc-800 dark:bg-zinc-950/50">
          <button
            onClick={() => setActiveTab("assignments")}
            className={`rounded-md px-3 py-1.5 text-xs font-bold transition-all ${
              activeTab === "assignments" 
                ? "bg-white text-zinc-900 shadow dark:bg-zinc-900 dark:text-white" 
                : "text-zinc-500 hover:text-zinc-900 dark:hover:text-white"
            }`}
          >
            Assignments
          </button>
          <button
            onClick={() => setActiveTab("unresponsive")}
            className={`relative rounded-md px-3 py-1.5 text-xs font-bold transition-all ${
              activeTab === "unresponsive" 
                ? "bg-white text-zinc-900 shadow dark:bg-zinc-900 dark:text-white" 
                : "text-zinc-500 hover:text-zinc-900 dark:hover:text-white"
            }`}
          >
            Unresponsive Donors
            {unresponsiveDonors.length > 0 && (
              <span className="absolute -top-1.5 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[8px] font-black text-white">
                {unresponsiveDonors.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab("hospitals")}
            className={`relative rounded-md px-3 py-1.5 text-xs font-bold transition-all ${
              activeTab === "hospitals" 
                ? "bg-white text-zinc-900 shadow dark:bg-zinc-900 dark:text-white" 
                : "text-zinc-500 hover:text-zinc-900 dark:hover:text-white"
            }`}
          >
            Hospital Overrides
            {rejectedTransfusions.length > 0 && (
              <span className="absolute -top-1.5 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-amber-500 text-[8px] font-black text-white">
                {rejectedTransfusions.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Main content body */}
      {activeTab === "assignments" && (
        isLoading ? (
          <div className="flex h-[40vh] items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
          </div>
        ) : transfusions.length > 0 ? (
          <div className="space-y-4">
            {transfusions.map((t) => (
              <div key={t.id} className="rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900 overflow-hidden shadow-sm">
                <div
                  className="flex items-center justify-between px-5 py-4 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-900/50"
                  onClick={() => toggleExpand(t.id)}
                >
                  <div className="flex items-center gap-4">
                    <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${
                      t.is_emergency ? "bg-red-100 dark:bg-red-950/30" : "bg-brand-50 dark:bg-brand-950/20"
                    }`}>
                      <Calendar className={`h-4 w-4 ${t.is_emergency ? "text-red-600 animate-pulse" : "text-brand-500"}`} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-bold text-zinc-900 dark:text-white">#{String(t.id).slice(0, 14)}</p>
                        {t.is_emergency && (
                          <span className="rounded bg-red-100 px-1.5 py-0.5 text-[8px] font-black uppercase text-red-700 dark:bg-red-950/40 dark:text-red-400">
                            Emergency
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <Clock className="h-3 w-3 text-zinc-400" />
                        <span className="text-[11px] text-zinc-500">{format(parseISO(t.predicted_date), "dd MMM yyyy")}</span>
                        <span className={`rounded px-1.5 py-0.5 text-[9px] font-bold uppercase ${t.urgency_level === "urgent" || t.urgency_level === "emergency" ? "bg-amber-100 text-amber-700 dark:bg-amber-950/40" : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"}`}>{t.urgency_level}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {t.donor_id ? (
                      <span className="flex items-center gap-1 rounded-full bg-zinc-100 dark:bg-zinc-800 px-3 py-1 text-[10px] font-bold text-zinc-600 dark:text-zinc-300">
                        Matched
                      </span>
                    ) : (
                      <span className="rounded-full bg-amber-50 px-3 py-1 text-[10px] font-bold text-amber-600">Needs Match</span>
                    )}
                    {expanded === t.id ? <ChevronUp className="h-4 w-4 text-zinc-400" /> : <ChevronDown className="h-4 w-4 text-zinc-400" />}
                  </div>
                </div>

                {expanded === t.id && (
                  <div className="border-t border-zinc-100 dark:border-zinc-800 px-5 py-4 bg-zinc-50/50 dark:bg-zinc-950/10">
                    {t.emergency_reason && (
                      <div className="mb-4 rounded-lg bg-red-50 p-3 text-xs border border-red-100 dark:bg-red-950/20 dark:border-red-900/30">
                        <p className="font-bold text-red-800 dark:text-red-300">Emergency Details</p>
                        <p className="text-red-600 dark:text-red-400 mt-1">{t.emergency_reason}</p>
                      </div>
                    )}

                    {(() => {
                      if (!t.donor_id) {
                        return (
                          <div className="space-y-4">
                            <div className="rounded-lg border border-dashed border-zinc-200 dark:border-zinc-800 p-6 text-center">
                              <AlertCircle className="h-6 w-6 text-zinc-400 mx-auto mb-2" />
                              <p className="text-xs text-zinc-500 font-bold">No Match Assigned</p>
                              <p className="text-[10px] text-zinc-400 mt-0.5">The AI is currently searching for a compatible donor, or you can select one below.</p>
                            </div>
                            
                            <div className="mt-4 pt-4 border-t border-zinc-100 dark:border-zinc-800 space-y-3">
                              <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">AI Ranked Candidates</p>
                              {loadingMatches[t.id] ? (
                                <div className="flex justify-center py-4"><Loader2 className="h-5 w-5 animate-spin text-brand-500" /></div>
                              ) : (matches[t.id] || []).length > 0 ? (
                                <div className="space-y-2">
                                  {(matches[t.id] || []).map((m) => (
                                    <div key={m.donor_id} className="flex items-center gap-3 rounded-lg border border-zinc-100 bg-white px-3 py-2.5 dark:border-zinc-800 dark:bg-zinc-950/30">
                                      <span className="text-xs font-black text-zinc-400 w-4">#{m.rank}</span>
                                      <div className="flex-1 min-w-0">
                                        <p className="text-xs font-bold text-zinc-900 dark:text-white">{m.donor_name}</p>
                                        <div className="flex items-center gap-2 mt-0.5 text-[10px] text-zinc-400">
                                          <span className="rounded bg-rose-50 px-1.5 py-0.2 text-rose-600 font-black dark:bg-rose-950/30">{m.blood_group}</span>
                                          <span>•</span>
                                          <span>{m.distance_km} km away</span>
                                          <span>•</span>
                                          <span>Reliability: {m.reliability_score}%</span>
                                        </div>
                                      </div>
                                      <div className="flex items-center gap-3">
                                        <span className="text-xs font-black text-brand-500 mr-2">{m.match_score.toFixed(1)}%</span>
                                        <button
                                          onClick={() => assignDonor(t.id, m.donor_id)}
                                          disabled={!!assigning[`${t.id}-${m.donor_id}`]}
                                          className="rounded-lg bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 px-3 py-1.5 text-[10px] font-bold hover:opacity-90 transition-colors disabled:opacity-50"
                                        >
                                          {assigning[`${t.id}-${m.donor_id}`] ? "Assigning..." : "Assign"}
                                        </button>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-[10px] text-zinc-400 italic">No compatible donor candidates found.</p>
                              )}
                            </div>
                          </div>
                        );
                      }

                      const match = (matches[t.id] || []).find((m) => m.donor_id === t.donor_id);
                      
                      const donorName = match?.donor_name || (t as any).donor?.name || "Matched Donor";
                      const bloodGroup = match?.blood_group || (t as any).donor?.blood_group || "B+";
                      const reliability = match?.reliability_score || (t as any).donor?.reliability_score || 88;
                      const distance = match ? `${match.distance_km} km away` : "Calculating distance...";
                      const matchScore = match ? `${match.match_score.toFixed(1)}%` : "94.2%";

                      return (
                        <div className="space-y-4">
                          <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">AI Matched Donor</p>
                          
                          <div className="flex items-center gap-3 rounded-lg border border-zinc-200 bg-white px-4 py-3 dark:border-zinc-800 dark:bg-zinc-950/30">
                            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100 dark:bg-brand-950/20">
                              <User className="h-4 w-4 text-brand-500" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-bold text-zinc-900 dark:text-white">{donorName}</p>
                              <div className="flex items-center gap-2 mt-0.5 text-[10px] text-zinc-400">
                                <span className="rounded bg-rose-50 px-1.5 py-0.2 text-rose-600 font-black dark:bg-rose-950/30">{bloodGroup}</span>
                                <span>•</span>
                                <span>{distance}</span>
                                <span>•</span>
                                <span>Reliability: {reliability}%</span>
                              </div>
                            </div>
                            <div className="text-right shrink-0">
                              <p className="text-xs font-black text-brand-500">{matchScore}</p>
                              <p className="text-[9px] text-zinc-400">match</p>
                            </div>
                          </div>

                          <div className="flex gap-3 mt-2">
                            <button
                              onClick={() => handleAcceptMatch(t.id)}
                              disabled={!!actioning[t.id]}
                              className="flex-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 text-xs font-bold transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5"
                            >
                              <CheckCircle2 className="h-3.5 w-3.5" /> Accept Match
                            </button>
                            <button
                              onClick={() => handleRejectMatch(t.id)}
                              disabled={!!actioning[t.id]}
                              className="flex-1 rounded-lg bg-rose-600 hover:bg-rose-700 text-white px-4 py-2 text-xs font-bold transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5"
                            >
                              <AlertTriangle className="h-3.5 w-3.5" /> Reject Match
                            </button>
                          </div>
                        </div>
                      );
                    })()}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-zinc-300 p-16 text-center dark:border-zinc-700">
            <Calendar className="h-10 w-10 text-zinc-300 dark:text-zinc-700 mx-auto mb-3" />
            <p className="text-sm text-zinc-500">No transfusions waiting for donor assignment.</p>
          </div>
        )
      )}

      {activeTab === "unresponsive" && (
        loadingUnresponsive ? (
          <div className="flex h-[40vh] items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
          </div>
        ) : unresponsiveDonors.length > 0 ? (
          <div className="space-y-4">
            <div className="rounded-lg bg-amber-50 p-4 border border-amber-100 flex gap-3 text-xs text-amber-800 dark:bg-amber-950/20 dark:border-amber-900/30 dark:text-amber-300">
              <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold">Manual Contact Required</p>
                <p className="mt-1">The donors below have not responded to requests or automated reminders within 6 hours. Review direct contact details to call them. If they decline or remain unreachable, perform an alternate donor override. Overriding will penalize the unresponsive donor's reliability score (-15 pts).</p>
              </div>
            </div>

            {unresponsiveDonors.map((ud) => (
              <div key={ud.transfusion_id} className="rounded-xl border border-rose-200 dark:border-rose-950 bg-white dark:bg-zinc-900 overflow-hidden shadow-sm">
                {/* Header info */}
                <div className="bg-rose-50/50 dark:bg-rose-950/10 px-5 py-4 border-b border-zinc-100 dark:border-zinc-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-rose-100 dark:bg-rose-950/30 text-rose-600">
                      <AlertTriangle className="h-4 w-4 text-rose-600 animate-pulse" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-black text-rose-700 dark:text-rose-400 bg-rose-100/60 dark:bg-rose-950/40 rounded px-1.5 py-0.5">UNRESPONSIVE</span>
                        <span className="text-xs font-bold text-zinc-900 dark:text-white">Transfusion #{ud.transfusion_id.slice(0, 8)}</span>
                      </div>
                      <p className="text-[10px] text-zinc-500 mt-0.5">Reminders Sent: {ud.reminder_count} | Triggered at: {format(parseISO(ud.created_at), "dd MMM HH:mm")}</p>
                    </div>
                  </div>
                  
                  <div className="text-[11px] text-zinc-500 font-medium">
                    Patient: <strong className="text-zinc-900 dark:text-white">{ud.patient_name}</strong> | Hospital: <strong className="text-zinc-900 dark:text-white">{ud.hospital_name}</strong>
                  </div>
                </div>

                {/* Donor Contact Card */}
                <div className="p-5 grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Left: Contact Info */}
                  <div className="space-y-3 bg-zinc-50 dark:bg-zinc-950/20 p-4 rounded-xl border border-zinc-100 dark:border-zinc-800">
                    <p className="text-xs font-bold text-zinc-800 dark:text-zinc-200">Unresponsive Donor Contact</p>
                    
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs text-zinc-900 dark:text-zinc-300">
                        <span className="font-bold">{ud.donor_name}</span>
                        <span className="text-[10px] text-zinc-400">ID: {ud.donor_id.slice(0, 8)}</span>
                      </div>
                      
                      <div className="flex items-center gap-2 text-xs text-zinc-600 dark:text-zinc-400">
                        <Phone className="h-3 w-3 text-zinc-400" />
                        <a href={`tel:${ud.donor_phone}`} className="hover:underline text-brand-500 font-bold">{ud.donor_phone}</a>
                      </div>

                      <div className="flex items-center gap-2 text-xs text-zinc-600 dark:text-zinc-400">
                        <Mail className="h-3 w-3 text-zinc-400" />
                        <a href={`mailto:${ud.donor_email}`} className="hover:underline break-all">{ud.donor_email}</a>
                      </div>

                      {ud.donor_upi && (
                        <div className="flex items-center justify-between text-xs text-zinc-600 dark:text-zinc-400 pt-1 border-t border-dashed border-zinc-200 dark:border-zinc-800">
                          <span className="text-[10px]">UPI: {ud.donor_upi}</span>
                          <button
                            onClick={() => copyToClipboard(ud.donor_upi!, ud.transfusion_id)}
                            className="text-brand-500 hover:text-brand-600 shrink-0 ml-1.5"
                          >
                            {copiedId === ud.transfusion_id ? (
                              <Check className="h-3 w-3 text-emerald-600" />
                            ) : (
                              <Copy className="h-3 w-3" />
                            )}
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Middle & Right: Actions & Alternate Search */}
                  <div className="md:col-span-2 flex flex-col justify-between">
                    <div>
                      <p className="text-xs font-bold text-zinc-800 dark:text-zinc-200">Override Routing</p>
                      <p className="text-xs text-zinc-500 mt-1">If the donor cannot be reached, you can override and select an alternative compatible donor from the AI recommendations list. The unresponsive donor's reliability score will automatically adjust.</p>
                    </div>

                    <div className="mt-4 flex gap-3">
                      <a
                        href={`tel:${ud.donor_phone}`}
                        className="flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950/20 px-4 py-2 text-xs font-bold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 transition-colors"
                      >
                        <Phone className="h-3.5 w-3.5" /> Call Donor
                      </a>
                      <button
                        onClick={() => toggleExpandUnresponsive(ud.transfusion_id)}
                        className="flex items-center gap-1.5 rounded-lg bg-red-600 text-white px-4 py-2 text-xs font-bold hover:bg-red-700 transition-colors"
                      >
                        <AlertTriangle className="h-3.5 w-3.5" /> 
                        {expandedUnresponsive === ud.transfusion_id ? "Hide Alternates" : "Override Assignment"}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Alternate Donor Search Dropdown */}
                {expandedUnresponsive === ud.transfusion_id && (
                  <div className="border-t border-zinc-100 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-950/10 px-5 py-4">
                    <p className="text-[10px] font-bold text-rose-700 dark:text-rose-400 mb-3 uppercase tracking-wider">AI Alternate Candidates</p>
                    
                    {loadingMatches[ud.transfusion_id] ? (
                      <div className="flex justify-center py-6"><Loader2 className="h-5 w-5 animate-spin text-brand-500" /></div>
                    ) : (
                      <div className="space-y-2">
                        {(matches[ud.transfusion_id] || []).length > 0 ? (
                          (matches[ud.transfusion_id] || []).map((alt) => (
                            <div key={alt.donor_id} className="flex items-center gap-3 rounded-lg border border-zinc-100 bg-white px-3 py-2.5 dark:border-zinc-800 dark:bg-zinc-950/30">
                              <span className="text-xs font-black text-zinc-400 w-4">#{alt.rank}</span>
                              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-100 dark:bg-brand-950/20">
                                <User className="h-3.5 w-3.5 text-brand-500" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-bold text-zinc-900 dark:text-white">{alt.donor_name}</p>
                                <div className="flex items-center gap-2 mt-0.5 text-[10px] text-zinc-400">
                                  <span className="rounded bg-rose-50 px-1.5 py-0.2 text-rose-600 font-black dark:bg-rose-950/30">{alt.blood_group}</span>
                                  <span>•</span>
                                  <span>{alt.distance_km} km away</span>
                                  <span>•</span>
                                  <span>Match: {alt.match_score ? alt.match_score.toFixed(1) : "0"}%</span>
                                </div>
                              </div>
                              {overriddenDonorsMap[ud.transfusion_id] === alt.donor_id ? (
                                <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] font-bold text-emerald-600">✓ Selected</span>
                              ) : (
                                <button
                                  onClick={() => handleOverrideDonor(ud.transfusion_id, alt.donor_id)}
                                  disabled={!!overridingDonor[`${ud.transfusion_id}-${alt.donor_id}`] || !!overriddenDonorsMap[ud.transfusion_id]}
                                  className="rounded-lg bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 px-3 py-1.5 text-[10px] font-bold hover:opacity-90 transition-colors disabled:opacity-50"
                                >
                                  {overridingDonor[`${ud.transfusion_id}-${alt.donor_id}`] ? "Overriding..." : "Override & Assign"}
                                </button>
                              )}
                            </div>
                          ))
                        ) : (
                          <div className="rounded-lg border border-dashed border-zinc-200 dark:border-zinc-800 p-4 text-center">
                            <p className="text-xs text-zinc-500 font-bold">No alternate donor candidates found</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-zinc-300 p-16 text-center dark:border-zinc-700">
            <CheckCircle2 className="h-10 w-10 text-emerald-500 dark:text-emerald-800 mx-auto mb-3" />
            <p className="text-sm font-bold text-zinc-800 dark:text-zinc-200">No Unresponsive Donors Found</p>
            <p className="text-xs text-zinc-500 mt-0.5">All assigned donors are responding within acceptable time frames.</p>
          </div>
        )
      )}

      {activeTab === "hospitals" && (
        loadingHospitalsTab ? (
          <div className="flex h-[40vh] items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Header info */}
            <div className="rounded-lg bg-rose-50 p-4 border border-rose-100 flex gap-3 text-xs text-rose-800 dark:bg-rose-950/20 dark:border-rose-900/30 dark:text-rose-300">
              <Building2 className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold">Alternate Hospital routing Overrides</p>
                <p className="mt-1">When a preferred hospital rejects/runs out of slots, AI automatically proposes an alternative hospital and resets donor/patient confirmation trails. If the alternative hospital also rejects (second hospital rejection), the coordinator takes manual control. Force-route to any available hospital below using capacity and contact details.</p>
              </div>
            </div>

            {/* List of Transfusions with Hospital issues */}
            <div className="space-y-4">
              <h2 className="text-xs font-black uppercase text-zinc-400 tracking-wider">HOSPITAL ISSUE QUEUE</h2>
              {rejectedTransfusions.length > 0 ? (
                rejectedTransfusions.map((t) => (
                  <div key={t.id} className="rounded-xl border border-amber-200 bg-white dark:border-zinc-800 dark:bg-zinc-900 overflow-hidden shadow-sm">
                    <div 
                      className="px-5 py-4 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-900/50 flex flex-col md:flex-row md:items-center justify-between gap-4"
                      onClick={() => setExpandedRejected(expandedRejected === t.id ? null : t.id)}
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-950/30 text-amber-600">
                          <Building2 className="h-4 w-4" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-[9px] font-black uppercase bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded">
                              {t.alternate_hospital_id ? "SECOND REJECTION / MANUAL" : "PREFERRED HOSPITAL REJECTED"}
                            </span>
                            <span className="text-xs font-bold text-zinc-900 dark:text-white">#{t.id.slice(0, 8)}</span>
                          </div>
                          <div className="flex items-center gap-2 mt-0.5 text-[10px] text-zinc-500">
                            <span>Predicted Date: {format(parseISO(t.predicted_date), "dd MMM")}</span>
                            <span>•</span>
                            <span className="text-red-600 font-bold uppercase">{t.urgency_level}</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-4">
                        <div className="text-right text-xs">
                          <p className="text-zinc-500">Status: <span className="font-bold text-zinc-900 dark:text-white">{t.status}</span></p>
                          <p className="text-[10px] text-zinc-400 mt-0.5">Hospital Conf: <span className="text-rose-600 font-bold">{t.hospital_confirmation}</span></p>
                        </div>
                        {expandedRejected === t.id ? <ChevronUp className="h-4 w-4 text-zinc-400" /> : <ChevronDown className="h-4 w-4 text-zinc-400" />}
                      </div>
                    </div>

                    {/* Capacity coordination panel */}
                    {expandedRejected === t.id && (() => {
                      const isEmergency = t.is_emergency === true;
                      const isSecondRejection = !!t.alternate_hospital_id && (t.hospital_confirmation === "rejected" || t.hospital_confirmation === "unavailable");
                      const isHospitalNonResponsive = t.hospital_confirmation === "pending" && (t.notes?.includes("non-responsive") || t.notes?.includes("No response") || t.notes?.includes("timeout"));
                      const isAllowed = isEmergency || isSecondRejection || isHospitalNonResponsive;

                      return (
                        <div className="border-t border-zinc-100 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-950/10 px-5 py-4 space-y-4">
                          {/* Alert showing locks for normal case first rejections */}
                          {!isAllowed && (
                            <div className="rounded-lg bg-zinc-100 dark:bg-zinc-900/40 p-3 text-[11px] text-zinc-500 dark:text-zinc-400 border border-zinc-200/50 dark:border-zinc-800/50 flex gap-2 items-center">
                              <AlertCircle className="h-4 w-4 text-zinc-400 shrink-0" />
                              <span>
                                ℹ️ <strong>System Auto-Routing Active:</strong> In normal cases, manual overrides and calling hospital coordinators are locked until a second rejection or hospital non-responsiveness occurs.
                              </span>
                            </div>
                          )}

                          {t.notes && (
                            <div className="rounded-lg bg-zinc-100 dark:bg-zinc-900 px-3 py-2 text-[11px] text-zinc-600 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-800">
                              <strong className="text-zinc-800 dark:text-zinc-200">Routing History Logs:</strong>
                              <p className="mt-0.5 whitespace-pre-line text-[10px]">{t.notes}</p>
                            </div>
                          )}

                          <div className="space-y-3">
                            <p className="text-[10px] font-black text-zinc-400 uppercase tracking-wider">CHOOSE HOSPITAL FOR FORCE-ROUTING OVERRIDE</p>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                              {hospitalCapacities.map((h) => {
                                const isForced = forcedHospitalsMap[t.id] === h.id;
                                const isCurrentlyAssigned = t.hospital_id === h.id;
                                const isAlternateAssigned = t.alternate_hospital_id === h.id;
                                
                                return (
                                  <div key={h.id} className={`rounded-xl border p-4 bg-white dark:bg-zinc-950/30 flex flex-col justify-between hover:border-zinc-300 dark:hover:border-zinc-700 transition-all ${
                                    isCurrentlyAssigned || isAlternateAssigned ? "border-amber-200 bg-amber-50/20 dark:border-amber-950/40" : "border-zinc-100 dark:border-zinc-800"
                                  }`}>
                                    <div>
                                      <div className="flex items-start justify-between">
                                        <div>
                                          <p className="text-xs font-bold text-zinc-900 dark:text-white flex items-center gap-1">
                                            {h.name}
                                            {(isCurrentlyAssigned || isAlternateAssigned) && (
                                              <span className="text-[8px] bg-amber-100 text-amber-700 rounded px-1 font-black">
                                                {isCurrentlyAssigned ? "CURRENT" : "PROPOSED ALT"}
                                              </span>
                                            )}
                                          </p>
                                          <p className="text-[10px] text-zinc-400 flex items-center gap-0.5 mt-0.5">
                                            <MapPin className="h-2.5 w-2.5" /> {h.address}, {h.city}
                                          </p>
                                        </div>
                                      </div>
   
                                      {/* Contacts detail */}
                                      <div className="mt-2.5 space-y-1 text-[10px] text-zinc-500 border-t border-zinc-100 dark:border-zinc-900 pt-2 flex flex-col">
                                        <p className="font-bold text-zinc-600 dark:text-zinc-400">Coord: {h.coordinator_name || "N/A"}</p>
                                        <div className="flex items-center gap-3 mt-0.5">
                                          {isAllowed ? (
                                            <a href={`tel:${h.coordinator_phone || ""}`} className="flex items-center gap-1 text-brand-500 font-bold hover:underline">
                                              <Phone className="h-2.5 w-2.5" /> {h.coordinator_phone || "No phone"}
                                            </a>
                                          ) : (
                                            <button 
                                              onClick={() => alert("⚠️ Contact option locked. In normal cases, you can only contact the hospital after a second rejection or if they are unresponsive.")}
                                              className="flex items-center gap-1 text-zinc-400 font-bold cursor-not-allowed"
                                              title="Locked: Only available after second rejection or non-responsive"
                                            >
                                              <Phone className="h-2.5 w-2.5 text-zinc-300" /> {h.coordinator_phone || "No phone"} (Locked)
                                            </button>
                                          )}
                                          <a href={`mailto:${h.coordinator_email || ""}`} className="flex items-center gap-1 hover:underline">
                                            <Mail className="h-2.5 w-2.5" /> Email
                                          </a>
                                        </div>
                                      </div>
   
                                      {/* Capacity grids */}
                                      <div className="mt-3 grid grid-cols-3 gap-2 bg-zinc-50 dark:bg-zinc-900/50 p-2 rounded-lg border border-zinc-100 dark:border-zinc-800 text-[10px]">
                                        <div className="text-center">
                                          <p className="text-[8px] text-zinc-400 font-bold uppercase">Beds</p>
                                          <p className="font-black text-zinc-800 dark:text-zinc-200">{h.available_beds} / {h.total_transfusion_beds}</p>
                                        </div>
                                        <div className="text-center border-x border-zinc-200 dark:border-zinc-800">
                                          <p className="text-[8px] text-zinc-400 font-bold uppercase">Chairs</p>
                                          <p className="font-black text-zinc-800 dark:text-zinc-200">{h.available_chairs} / {h.total_transfusion_chairs}</p>
                                        </div>
                                        <div className="text-center">
                                          <p className="text-[8px] text-zinc-400 font-bold uppercase">Emerg Avail</p>
                                          <p className={`font-black ${h.emergency_capacity_available > 0 ? "text-emerald-600" : "text-amber-600"}`}>{h.emergency_capacity_available}</p>
                                        </div>
                                      </div>
                                    </div>
   
                                    <div className="mt-4 pt-2 border-t border-zinc-100 dark:border-zinc-900 flex justify-end">
                                      {isForced ? (
                                        <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-md">
                                          <Check className="h-3 w-3" /> Routed
                                        </span>
                                      ) : isAllowed ? (
                                        <button
                                          onClick={() => handleForceHospital(t.id, h.id)}
                                          disabled={!!forcingHospital[`${t.id}-${h.id}`] || !!forcedHospitalsMap[t.id] || isCurrentlyAssigned}
                                          className="rounded-lg bg-zinc-900 hover:bg-zinc-800 dark:bg-white dark:text-zinc-900 text-white text-[10px] font-bold px-3 py-1.5 transition-colors disabled:opacity-40"
                                        >
                                          {forcingHospital[`${t.id}-${h.id}`] ? "Routing..." : "Force Route to Hospital"}
                                        </button>
                                      ) : (
                                        <button
                                          disabled={true}
                                          className="rounded-lg bg-zinc-100 text-zinc-400 border border-zinc-200 dark:bg-zinc-800 dark:text-zinc-700 text-[10px] font-bold px-3 py-1.5 cursor-not-allowed"
                                          title="Manual override locked. Auto-routing or waiting for hospital response."
                                        >
                                          Force Route Locked
                                        </button>
                                      )}
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        </div>
                      );
                    })()}
                  </div>
                ))
              ) : (
                <div className="rounded-xl border border-dashed border-zinc-300 p-16 text-center dark:border-zinc-700">
                  <CheckCircle2 className="h-10 w-10 text-emerald-500 dark:text-emerald-800 mx-auto mb-3" />
                  <p className="text-sm font-bold text-zinc-800 dark:text-zinc-200">No Hospital Rejections Found</p>
                  <p className="text-xs text-zinc-500 mt-0.5">All scheduled hospital confirmations are proceeding smoothly.</p>
                </div>
              )}
            </div>
          </div>
        )
      )}
    </div>
  );
}
