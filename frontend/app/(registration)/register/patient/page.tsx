"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { apiClient } from "../../../../lib/api/client";
import { BloodGroup, ThalassemiaType } from "../../../../lib/types/common";
import { Loader2, Heart, ShieldAlert, ArrowRight, ArrowLeft } from "lucide-react";

const patientRegSchema = z.object({
  // Step 1
  name: z.string().min(2, "Name must be at least 2 characters"),
  age: z.number().int().positive("Age must be positive number"),
  gender: z.enum(["male", "female", "other"]),
  address: z.string().min(5, "Please enter your address"),
  city: z.string().min(2, "City required"),
  state: z.string().min(2, "State required"),
  blood_group: z.enum(["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"], {
    message: "Select valid blood group",
  }),
  thalassemia_type: z.enum(["major", "intermedia", "minor", "hb_e", "hb_s"], {
    message: "Select thalassemia type",
  }),
  
  // Step 2
  avg_transfusion_interval_days: z.number().int().min(7).max(90, "Interval must be between 7 and 90 days"),
  last_transfusion_date: z.string().optional(),
  emergency_contact_name: z.string().min(2, "Emergency contact name required"),
  emergency_contact_phone: z.string().regex(/^(\+91)?[6-9]\d{9}$/, "Must be valid 10-digit Indian mobile number"),
  consents_data_sharing: z.boolean().refine((val) => val === true, {
    message: "Consent to data sharing is required",
  }),
  consents_emergency_escalation: z.boolean(),
  
  // Step 3
  preferred_hospitals: z.array(z.string()).min(1, "Select at least one preferred hospital"),
});

type PatientRegValues = z.infer<typeof patientRegSchema>;

export default function PatientRegistration() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [hospitalsList, setHospitalsList] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    trigger,
    formState: { errors },
  } = useForm<PatientRegValues>({
    resolver: zodResolver(patientRegSchema),
    defaultValues: {
      address: "",
      city: "Chennai",
      state: "Tamil Nadu",
      avg_transfusion_interval_days: 21,
      consents_data_sharing: true,
      consents_emergency_escalation: true,
      preferred_hospitals: [],
    },
  });

  const selectedHospitals = watch("preferred_hospitals") || [];

  // Fetch hospitals list from FastAPI for Preferences selection
  useEffect(() => {
    const fetchHospitals = async () => {
      try {
        const response = await apiClient.get("/hospitals?page_size=100");
        const items = Array.isArray(response.data) ? response.data : (response.data.items || []);
        setHospitalsList(items);
      } catch (err) {
        console.error("Failed to load hospitals list: ", err);
        // Fallback mockup list for UI robustness
        setHospitalsList([
          { id: "d9b0f69a-2f47-495b-b9ab-1d9bf1eb62ea", name: "Apollo Hospital, Chennai" },
          { id: "f130b91d-cf5f-4d94-a461-750d4fbb1bde", name: "City Care General, Delhi" },
          { id: "e584f938-1f48-4395-8e7c-eb80c85c2c56", name: "Red Cross Blood Care, Mumbai" },
        ]);
      }
    };
    fetchHospitals();
  }, []);

  const handleHospitalToggle = (hospId: string) => {
    if (selectedHospitals.includes(hospId)) {
      setValue(
        "preferred_hospitals",
        selectedHospitals.filter((id) => id !== hospId)
      );
    } else {
      if (selectedHospitals.length >= 3) return;
      setValue("preferred_hospitals", [...selectedHospitals, hospId]);
    }
  };

  const onSubmit = async (data: PatientRegValues) => {
    setIsLoading(true);
    setError(null);

    const prefList = data.preferred_hospitals.map((hospId, index) => ({
      hospital_id: hospId,
      preference_order: index + 1,
    }));

    try {
      // Connect to FastAPI Patient Creation endpoint
      await apiClient.post("/patients/register", {
        name: data.name,
        age: data.age,
        gender: data.gender,
        address: data.address,
        city: data.city,
        state: data.state,
        blood_group: data.blood_group,
        thalassemia_type: data.thalassemia_type,
        avg_transfusion_interval_days: data.avg_transfusion_interval_days,
        last_transfusion_date: data.last_transfusion_date ? data.last_transfusion_date : null,
        emergency_contact_name: data.emergency_contact_name,
        emergency_contact_phone: data.emergency_contact_phone,
        data_sharing_consent: data.consents_data_sharing,
        emergency_consent: data.consents_emergency_escalation,
        hospital_preferences: prefList,
      });

      router.push("/patient/dashboard");
    } catch (err: any) {
      console.error("Patient onboarding failure: ", err);
      setError(
        err.response?.data?.detail || "Failed to submit patient details. Please retry."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-xl py-12 px-6">
      {/* Wizard steps indicator header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-zinc-950 dark:text-white">
            Patient Care Setup
          </h2>
          <p className="text-xs text-zinc-500">
            Configure your regular transfusion settings.
          </p>
        </div>
        <div className="flex gap-1.5">
          {[1, 2, 3].map((s) => (
            <div
              key={s}
              className={`h-2 w-8 rounded-full transition-colors ${
                s <= step ? "bg-brand-500" : "bg-zinc-200 dark:bg-zinc-800"
              }`}
            />
          ))}
        </div>
      </div>

      {error && (
        <div className="mb-6 rounded-lg bg-red-50 p-4 text-xs font-semibold text-red-600 dark:bg-red-950/20 dark:text-red-400">
          {error}
        </div>
      )}

      {Object.keys(errors).length > 0 && (
        <div className="mb-6 rounded-lg bg-amber-50 p-4 text-xs font-semibold text-amber-800 dark:bg-amber-950/20 dark:text-amber-400">
          <p className="font-bold mb-1">Please check the form. The following fields have errors:</p>
          <ul className="list-disc pl-4 space-y-0.5">
            {Object.entries(errors).map(([field, err]: any) => (
              <li key={field}>{err.message}</li>
            ))}
          </ul>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* STEP 1: Personal Info */}
        {step === 1 && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-zinc-900 dark:text-zinc-100 border-b pb-2">
              Step 1: Patient Information
            </h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  Full Name
                </label>
                <input
                  {...register("name")}
                  type="text"
                  placeholder="Rahul Sharma"
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                />
                {errors.name && (
                  <p className="text-[10px] text-red-600">{errors.name.message}</p>
                )}
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  Age (Years)
                </label>
                <input
                  {...register("age", { valueAsNumber: true })}
                  type="number"
                  placeholder="18"
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                />
                {errors.age && (
                  <p className="text-[10px] text-red-600">{errors.age.message}</p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  Gender
                </label>
                <select
                  {...register("gender")}
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                >
                  <option value="">Select Gender</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
                {errors.gender && (
                  <p className="text-[10px] text-red-600">{errors.gender.message}</p>
                )}
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  Blood Group
                </label>
                <select
                  {...register("blood_group")}
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                >
                  <option value="">Select Blood Group</option>
                  <option value="A+">A+</option>
                  <option value="A-">A-</option>
                  <option value="B+">B+</option>
                  <option value="B-">B-</option>
                  <option value="AB+">AB+</option>
                  <option value="AB-">AB-</option>
                  <option value="O+">O+</option>
                  <option value="O-">O-</option>
                </select>
                {errors.blood_group && (
                  <p className="text-[10px] text-red-600">{errors.blood_group.message}</p>
                )}
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                Thalassemia Type
              </label>
              <select
                {...register("thalassemia_type")}
                className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
              >
                <option value="">Select Type</option>
                <option value="major">Thalassemia Major (Requires frequent transfusions)</option>
                <option value="intermedia">Thalassemia Intermedia (Occasional transfusions)</option>
                <option value="minor">Thalassemia Minor (Mild trait)</option>
                <option value="hb_e">Hemoglobin E trait</option>
                <option value="hb_s">Sickle Beta Thalassemia</option>
              </select>
              {errors.thalassemia_type && (
                <p className="text-[10px] text-red-600">{errors.thalassemia_type.message}</p>
              )}
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                Residential Street Address
              </label>
              <input
                {...register("address")}
                type="text"
                placeholder="12, Cathedral Road, Gopalapuram"
                className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
              />
              {errors.address && (
                <p className="text-[10px] text-red-600">{errors.address.message}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  City
                </label>
                <input
                  {...register("city")}
                  type="text"
                  placeholder="Chennai"
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                />
                {errors.city && (
                  <p className="text-[10px] text-red-600">{errors.city.message}</p>
                )}
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  State
                </label>
                <input
                  {...register("state")}
                  type="text"
                  placeholder="Tamil Nadu"
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                />
                {errors.state && (
                  <p className="text-[10px] text-red-600">{errors.state.message}</p>
                )}
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button
                type="button"
                onClick={async () => {
                  const isValid = await trigger([
                    "name",
                    "age",
                    "gender",
                    "address",
                    "city",
                    "state",
                    "blood_group",
                    "thalassemia_type",
                  ]);
                  if (isValid) setStep(2);
                }}
                className="flex h-10 items-center justify-center gap-1.5 rounded-md bg-brand-500 px-6 font-bold text-white transition-colors hover:bg-brand-600"
              >
                Next Step
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: Medical Settings & Consents */}
        {step === 2 && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-zinc-900 dark:text-zinc-100 border-b pb-2">
              Step 2: Medical & Safety Profiles
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  Last Transfusion Date
                </label>
                <input
                  {...register("last_transfusion_date")}
                  type="date"
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  Transfusion Interval (Days)
                </label>
                <input
                  {...register("avg_transfusion_interval_days", { valueAsNumber: true })}
                  type="number"
                  placeholder="21"
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                />
                {errors.avg_transfusion_interval_days && (
                  <p className="text-[10px] text-red-600">
                    {errors.avg_transfusion_interval_days.message}
                  </p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  Emergency Contact Name
                </label>
                <input
                  {...register("emergency_contact_name")}
                  type="text"
                  placeholder="Suresh Sharma"
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                />
                {errors.emergency_contact_name && (
                  <p className="text-[10px] text-red-600">
                    {errors.emergency_contact_name.message}
                  </p>
                )}
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  Emergency Contact Phone
                </label>
                <input
                  {...register("emergency_contact_phone")}
                  type="tel"
                  placeholder="+919876543210"
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                />
                {errors.emergency_contact_phone && (
                  <p className="text-[10px] text-red-600">
                    {errors.emergency_contact_phone.message}
                  </p>
                )}
              </div>
            </div>

            {/* Consents toggles */}
            <div className="space-y-3 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800 bg-zinc-50/50">
              <div className="flex items-start gap-3">
                <input
                  {...register("consents_data_sharing")}
                  type="checkbox"
                  id="consent_share"
                  className="mt-1 h-4 w-4 rounded border-zinc-300 text-brand-500 outline-none"
                />
                <div className="leading-tight">
                  <label htmlFor="consent_share" className="text-xs font-bold text-zinc-900 dark:text-white cursor-pointer">
                    I consent to sharing my medical data
                  </label>
                  <p className="text-[10px] text-zinc-500">
                    Allows hospitals and coordinates to find matches securely.
                  </p>
                  {errors.consents_data_sharing && (
                    <p className="text-[10px] text-red-600 mt-1">
                      {errors.consents_data_sharing.message}
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-start gap-3 border-t border-zinc-200 pt-3 dark:border-zinc-800">
                <input
                  {...register("consents_emergency_escalation")}
                  type="checkbox"
                  id="consent_escalate"
                  className="mt-1 h-4 w-4 rounded border-zinc-300 text-brand-500 outline-none"
                />
                <div className="leading-tight">
                  <label htmlFor="consent_escalate" className="text-xs font-bold text-zinc-900 dark:text-white cursor-pointer">
                    Enable auto emergency routing
                  </label>
                  <p className="text-[10px] text-zinc-500">
                    System can automatically find alternative hospitals and alert nearby donors when scheduled slots fail.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex justify-between pt-4">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="flex h-10 items-center justify-center gap-1.5 rounded-md border border-zinc-200 bg-white px-4 text-xs font-semibold text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </button>
              <button
                type="button"
                onClick={async () => {
                  const isValid = await trigger([
                    "avg_transfusion_interval_days",
                    "last_transfusion_date",
                    "emergency_contact_name",
                    "emergency_contact_phone",
                    "consents_data_sharing",
                    "consents_emergency_escalation",
                  ]);
                  if (isValid) setStep(3);
                }}
                className="flex h-10 items-center justify-center gap-1.5 rounded-md bg-brand-500 px-6 font-bold text-white transition-colors hover:bg-brand-600"
              >
                Next Step
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: Hospital Preferences */}
        {step === 3 && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-zinc-900 dark:text-zinc-100 border-b pb-2">
              Step 3: Preferred Hospitals Selection
            </h3>
            
            <p className="text-[10px] text-zinc-500 leading-normal">
              Select one or more hospitals below, ranked in order of preference. The AI scheduler prioritizes your top picks when booking transfusion chairs.
            </p>

            <div className="space-y-2 max-h-60 overflow-y-auto border rounded-md p-3 dark:border-zinc-800">
              {hospitalsList.length > 0 ? (
                hospitalsList.map((hosp) => {
                  const isChecked = selectedHospitals.includes(hosp.id);
                  const isMaxReached = selectedHospitals.length >= 3 && !isChecked;
                  return (
                    <div
                      key={hosp.id}
                      onClick={() => {
                        if (isMaxReached) return;
                        handleHospitalToggle(hosp.id);
                      }}
                      className={`flex items-center justify-between rounded-lg border p-3 transition-colors ${
                        isChecked
                          ? "border-brand-500 bg-brand-50/10 cursor-pointer"
                          : isMaxReached
                          ? "opacity-50 cursor-not-allowed border-zinc-200 dark:border-zinc-800"
                          : "border-zinc-200 hover:border-zinc-300 dark:border-zinc-800 cursor-pointer"
                      }`}
                    >
                      <div>
                        <p className="text-xs font-bold text-zinc-900 dark:text-white">
                          {hosp.name}
                        </p>
                        <p className="text-[10px] text-zinc-500">
                          {hosp.address || "Medical Complex"}
                        </p>
                      </div>
                      <input
                        type="checkbox"
                        checked={isChecked}
                        disabled={isMaxReached}
                        readOnly
                        className="h-4 w-4 text-brand-500 rounded"
                      />
                    </div>
                  );
                })
              ) : (
                <div className="text-center py-6 text-xs text-zinc-500">
                  No registered hospitals found.
                </div>
              )}
            </div>
            {errors.preferred_hospitals && (
              <p className="text-[10px] text-red-600">
                {errors.preferred_hospitals.message}
              </p>
            )}

            {/* Display Ranking Sequence */}
            {selectedHospitals.length > 0 && (
              <div className="space-y-2 rounded-lg bg-zinc-50 p-4 dark:bg-zinc-900/40">
                <h4 className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  Ranking Preference:
                </h4>
                <div className="space-y-1.5">
                  {selectedHospitals.map((hospId, index) => {
                    const hospName = hospitalsList.find((h) => h.id === hospId)?.name || "Hospital";
                    return (
                      <div
                        key={hospId}
                        className="flex items-center gap-3 rounded bg-white p-2.5 text-xs border dark:bg-zinc-950 dark:border-zinc-800"
                      >
                        <span className="flex h-5 w-5 items-center justify-center rounded bg-brand-50 text-[10px] font-bold text-brand-600">
                          {index + 1}
                        </span>
                        <span className="font-medium text-zinc-800 dark:text-zinc-200">
                          {hospName}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="flex justify-between pt-4">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="flex h-10 items-center justify-center gap-1.5 rounded-md border border-zinc-200 bg-white px-4 text-xs font-semibold text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </button>
              
              <button
                type="submit"
                disabled={isLoading}
                className="flex h-10 items-center justify-center gap-1.5 rounded-md bg-brand-500 px-6 font-bold text-white transition-colors hover:bg-brand-600 disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Saving settings...
                  </>
                ) : (
                  "Complete Setup"
                )}
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  );
}
