"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { apiClient } from "../../../../lib/api/client";
import { BloodGroup } from "../../../../lib/types/common";
import { Loader2, ArrowRight, ArrowLeft, Heart, Check, MapPin } from "lucide-react";

const donorRegSchema = z.object({
  // Step 1
  name: z.string().min(2, "Name must be at least 2 characters"),
  age: z.number().int().min(18, "Must be at least 18 years old to donate"),
  gender: z.enum(["male", "female", "other"]),
  blood_group: z.enum(["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]),
  upi_id: z.string().min(3, "UPI ID is required for travel reimbursements"),

  // Step 2
  max_travel_distance_km: z.number().int().min(2).max(100),
  language_preference: z.enum(["en", "hi"]),

  // Step 3
  address: z.string().min(5, "Please enter your address"),
});

type DonorRegValues = z.infer<typeof donorRegSchema>;

export default function DonorRegistration() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Selected availability days/times tracking state
  const [selectedDays, setSelectedDays] = useState<string[]>(["Sun", "Sat"]);
  const [selectedTimes, setSelectedTimes] = useState<string[]>(["Morning"]);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    trigger,
    formState: { errors },
  } = useForm<DonorRegValues>({
    resolver: zodResolver(donorRegSchema),
    defaultValues: {
      max_travel_distance_km: 15,
      language_preference: "en",
    },
  });

  const travelDist = watch("max_travel_distance_km");

  const daysList = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const timesList = ["Morning", "Afternoon", "Evening"];

  const handleDayToggle = (day: string) => {
    setSelectedDays((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day]
    );
  };

  const handleTimeToggle = (time: string) => {
    setSelectedTimes((prev) =>
      prev.includes(time) ? prev.filter((t) => t !== time) : [...prev, time]
    );
  };

  const onSubmit = async (data: DonorRegValues) => {
    setIsLoading(true);
    setError(null);

    // Mock geolocation lookup for simplicity during demo registration
    // In production, maps library returns these coordinates
    const mockLat = 13.0827 + (Math.random() - 0.5) * 0.1;
    const mockLng = 80.2707 + (Math.random() - 0.5) * 0.1;

    try {
      await apiClient.post("/donors/register", {
        name: data.name,
        age: data.age,
        gender: data.gender,
        blood_group: data.blood_group,
        upi_id: data.upi_id,
        max_travel_distance_km: data.max_travel_distance_km,
        preferred_days: selectedDays,
        preferred_times: selectedTimes,
        language_preference: data.language_preference,
        latitude: mockLat,
        longitude: mockLng,
      });

      router.push("/donor/dashboard");
    } catch (err: any) {
      console.error("Donor onboarding failure: ", err);
      setError(
        err.response?.data?.detail || "Failed to submit donor registration. Please retry."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-xl py-12 px-6">
      {/* Step indicators */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-zinc-950 dark:text-white">
            Donor Account Onboarding
          </h2>
          <p className="text-xs text-zinc-500">
            Set your donation settings to start saving lives.
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
              Step 1: Contact Details & UPI
            </h3>

            <div className="space-y-1">
              <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                Full Name
              </label>
              <input
                {...register("name")}
                type="text"
                placeholder="Arjun Kapoor"
                className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
              />
              {errors.name && (
                <p className="text-[10px] text-red-600">{errors.name.message}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  Age (18+)
                </label>
                <input
                  {...register("age", { valueAsNumber: true })}
                  type="number"
                  placeholder="24"
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                />
                {errors.age && (
                  <p className="text-[10px] text-red-600">{errors.age.message}</p>
                )}
              </div>

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
            </div>

            <div className="grid grid-cols-2 gap-4">
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

              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  UPI ID (For Expense Claims)
                </label>
                <input
                  {...register("upi_id")}
                  type="text"
                  placeholder="arjun@okaxis"
                  className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
                />
                {errors.upi_id && (
                  <p className="text-[10px] text-red-600">{errors.upi_id.message}</p>
                )}
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button
                type="button"
                onClick={async () => {
                  const isValid = await trigger(["name", "age", "gender", "blood_group", "upi_id"]);
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

        {/* STEP 2: Donation Preferences */}
        {step === 2 && (
          <div className="space-y-6">
            <h3 className="text-sm font-bold text-zinc-900 dark:text-zinc-100 border-b pb-2">
              Step 2: Availability Preferences
            </h3>

            {/* Travel Radius */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                  Maximum Travel Radius
                </label>
                <span className="text-xs font-bold text-brand-600">
                  {travelDist} km
                </span>
              </div>
              <input
                type="range"
                min="2"
                max="100"
                {...register("max_travel_distance_km", { valueAsNumber: true })}
                className="h-1.5 w-full cursor-pointer appearance-none rounded-lg bg-zinc-200 dark:bg-zinc-800 accent-brand-500"
              />
            </div>

            {/* Preferred Days */}
            <div className="space-y-2">
              <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                Preferred Donation Days
              </label>
              <div className="flex flex-wrap gap-2">
                {daysList.map((day) => {
                  const isSelected = selectedDays.includes(day);
                  return (
                    <button
                      key={day}
                      type="button"
                      onClick={() => handleDayToggle(day)}
                      className={`flex items-center gap-1 rounded-full px-4 py-1.5 text-xs font-semibold border transition-all ${
                        isSelected
                          ? "bg-brand-500 border-brand-500 text-white"
                          : "bg-white border-zinc-200 text-zinc-700 hover:border-zinc-300 dark:bg-zinc-900 dark:border-zinc-800 dark:text-zinc-300"
                      }`}
                    >
                      {day}
                      {isSelected && <Check className="h-3 w-3" />}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Preferred Times */}
            <div className="space-y-2">
              <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                Preferred Times of Day
              </label>
              <div className="flex gap-2.5">
                {timesList.map((time) => {
                  const isSelected = selectedTimes.includes(time);
                  return (
                    <button
                      key={time}
                      type="button"
                      onClick={() => handleTimeToggle(time)}
                      className={`flex items-center gap-1 rounded-full px-4 py-1.5 text-xs font-semibold border transition-all ${
                        isSelected
                          ? "bg-brand-500 border-brand-500 text-white"
                          : "bg-white border-zinc-200 text-zinc-700 hover:border-zinc-300 dark:bg-zinc-900 dark:border-zinc-800 dark:text-zinc-300"
                      }`}
                    >
                      {time}
                      {isSelected && <Check className="h-3 w-3" />}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                Bilingual Language Preference
              </label>
              <select
                {...register("language_preference")}
                className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
              >
                <option value="en">English</option>
                <option value="hi">हिंदी (Hindi)</option>
              </select>
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
                type="button"
                onClick={async () => {
                  const isValid = await trigger(["max_travel_distance_km", "language_preference"]);
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

        {/* STEP 3: Location setting */}
        {step === 3 && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-zinc-900 dark:text-zinc-100 border-b pb-2">
              Step 3: Location Verification
            </h3>

            <div className="space-y-1">
              <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                Residential Address / City
              </label>
              <textarea
                {...register("address")}
                rows={3}
                placeholder="12, Cathedral Road, Gopalapuram, Chennai, Tamil Nadu - 600086"
                className="w-full rounded-md border border-zinc-200 bg-white p-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
              />
              {errors.address && (
                <p className="text-[10px] text-red-600">{errors.address.message}</p>
              )}
            </div>

            {/* Geolocation Mock Visual Panel */}
            <div className="rounded-lg border border-zinc-200 p-4 dark:border-zinc-800 bg-zinc-50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-100 text-brand-600 dark:bg-brand-950/20">
                  <MapPin className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-zinc-900 dark:text-white">
                    GPS Coordinates Autocorrect
                  </h4>
                  <p className="text-[9px] text-zinc-500">
                    Location is pinned to coordinates for mapping distances to hospitals.
                  </p>
                </div>
              </div>
              <span className="rounded bg-brand-50 px-2 py-1 text-[9px] font-bold text-brand-600">
                Auto Geocoded
              </span>
            </div>

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
                    Registering donor...
                  </>
                ) : (
                  "Complete Registration"
                )}
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  );
}
