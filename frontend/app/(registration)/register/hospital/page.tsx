"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { apiClient } from "../../../../lib/api/client";
import { Loader2, ArrowRight, ArrowLeft, Building2 } from "lucide-react";

const hospitalRegSchema = z.object({
  // Step 1
  name: z.string().min(3, "Hospital name must be at least 3 characters"),
  registration_number: z.string().min(5, "Valid registry number required"),
  address: z.string().min(5, "Full address required"),
  city: z.string().min(2, "City required"),
  state: z.string().min(2, "State required"),
  operating_hours_start: z.string(),
  operating_hours_end: z.string(),
  contact_name: z.string().min(2, "Contact coordinator name required"),
  contact_email: z.string().email("Valid coordinator email required"),
  contact_phone: z.string().regex(/^(\+91)?[6-9]\d{9}$/, "Must be valid 10-digit Indian mobile number"),

  // Step 2
  total_beds: z.number().int().min(1, "Must have at least 1 transfusion bed"),
  total_chairs: z.number().int().min(1, "Must have at least 1 transfusion chair"),
  emergency_capacity: z.number().int().min(1, "Must set emergency buffer capacity"),
});

type HospitalRegValues = z.infer<typeof hospitalRegSchema>;

export default function HospitalRegistration() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    trigger,
    formState: { errors },
  } = useForm<HospitalRegValues>({
    resolver: zodResolver(hospitalRegSchema),
    defaultValues: {
      operating_hours_start: "09:00",
      operating_hours_end: "18:00",
      contact_email: "",
      total_beds: 5,
      total_chairs: 10,
      emergency_capacity: 2,
    },
  });

  const onSubmit = async (data: HospitalRegValues) => {
    setIsLoading(true);
    setError(null);

    // Mock geolocation coordinates for demo
    const mockLat = 13.0827 + (Math.random() - 0.5) * 0.05;
    const mockLng = 80.2707 + (Math.random() - 0.5) * 0.05;

    try {
      // 1. Register hospital profile (automatically creates initial capacity record on backend)
      await apiClient.post("/hospitals/register", {
        name: data.name,
        registration_number: data.registration_number,
        address: data.address,
        city: data.city,
        state: data.state,
        total_transfusion_beds: data.total_beds,
        total_transfusion_chairs: data.total_chairs,
        emergency_capacity: data.emergency_capacity,
        coordinator_name: data.contact_name,
        coordinator_email: data.contact_email,
        coordinator_phone: data.contact_phone,
        operating_hours_start: data.operating_hours_start,
        operating_hours_end: data.operating_hours_end,
        latitude: mockLat,
        longitude: mockLng,
      });

      router.push("/hospital/dashboard");
    } catch (err: any) {
      console.error("Hospital onboarding failure: ", err);
      setError(
        err.response?.data?.detail || "Failed to submit hospital settings. Please check details."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-xl py-12 px-6">
      {/* Step header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-zinc-950 dark:text-white">
            Hospital Portal Setup
          </h2>
          <p className="text-xs text-zinc-500">
            Register hospital facilities and transfusion units.
          </p>
        </div>
        <div className="flex gap-1.5">
          {[1, 2].map((s) => (
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
        {/* STEP 1: Details */}
        {step === 1 && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-zinc-900 dark:text-zinc-100 border-b pb-2">
              Step 1: Hospital Profile Details
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  Hospital Name
                </label>
                <input
                  {...register("name")}
                  type="text"
                  placeholder="City General Hospital"
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                />
                {errors.name && (
                  <p className="text-[10px] text-red-600">{errors.name.message}</p>
                )}
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  Registration Number
                </label>
                <input
                  {...register("registration_number")}
                  type="text"
                  placeholder="REG-9876543-A"
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                />
                {errors.registration_number && (
                  <p className="text-[10px] text-red-600">{errors.registration_number.message}</p>
                )}
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                Street Address
              </label>
              <input
                {...register("address")}
                type="text"
                placeholder="45, G.N. Road, T.Nagar"
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

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  Transfusion Start Time
                </label>
                <input
                  {...register("operating_hours_start")}
                  type="time"
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  Transfusion End Time
                </label>
                <input
                  {...register("operating_hours_end")}
                  type="time"
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                Lead Coordinator Name
              </label>
              <input
                {...register("contact_name")}
                type="text"
                placeholder="Dr. Shreya Roy"
                className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
              />
              {errors.contact_name && (
                <p className="text-[10px] text-red-600">{errors.contact_name.message}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  Coordinator Email
                </label>
                <input
                  {...register("contact_email")}
                  type="email"
                  placeholder="shreya.roy@hospital.com"
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                />
                {errors.contact_email && (
                  <p className="text-[10px] text-red-600">{errors.contact_email.message}</p>
                )}
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  Contact Mobile
                </label>
                <input
                  {...register("contact_phone")}
                  type="tel"
                  placeholder="+919876543210"
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                />
                {errors.contact_phone && (
                  <p className="text-[10px] text-red-600">{errors.contact_phone.message}</p>
                )}
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button
                type="button"
                onClick={async () => {
                  const isValid = await trigger([
                    "name",
                    "registration_number",
                    "address",
                    "city",
                    "state",
                    "operating_hours_start",
                    "operating_hours_end",
                    "contact_name",
                    "contact_email",
                    "contact_phone",
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

        {/* STEP 2: Capacity settings */}
        {step === 2 && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-zinc-900 dark:text-zinc-100 border-b pb-2">
              Step 2: Transfusion Chair & Bed Capacity
            </h3>

            <div className="rounded-lg bg-zinc-50 border p-4 dark:border-zinc-800 dark:bg-zinc-900/30 space-y-4">
              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  Total Transfusion Chairs
                </label>
                <input
                  {...register("total_chairs", { valueAsNumber: true })}
                  type="number"
                  placeholder="10"
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                />
                {errors.total_chairs && (
                  <p className="text-[10px] text-red-600">{errors.total_chairs.message}</p>
                )}
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  Total Transfusion Beds
                </label>
                <input
                  {...register("total_beds", { valueAsNumber: true })}
                  type="number"
                  placeholder="5"
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                />
                {errors.total_beds && (
                  <p className="text-[10px] text-red-600">{errors.total_beds.message}</p>
                )}
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  Reserved Emergency Buffer Slots
                </label>
                <input
                  {...register("emergency_capacity", { valueAsNumber: true })}
                  type="number"
                  placeholder="2"
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                />
                {errors.emergency_capacity && (
                  <p className="text-[10px] text-red-600">{errors.emergency_capacity.message}</p>
                )}
              </div>
            </div>

            <div className="flex justify-between pt-4">
              <button
                type="button"
                onClick={() => setStep(1)}
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
                    Completing facility setup...
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
