"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { apiClient } from "../../../../lib/api/client";
import { useAuthStore } from "../../../../lib/stores/authStore";
import { Loader2, ShieldCheck, Clock, ArrowRight } from "lucide-react";

const coordRegSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  phone: z.string().regex(/^(\+91)?[6-9]\d{9}$/, "Must be valid 10-digit Indian mobile number"),
  organization: z.string().min(3, "Organization name required"),
  assigned_region: z.string().min(2, "Please enter your assigned region/city"),
});

type CoordRegValues = z.infer<typeof coordRegSchema>;

export default function CoordinatorRegistration() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const accessToken = useAuthStore((state) => state.accessToken);
  const refreshToken = useAuthStore((state) => state.refreshToken);
  const setAuth = useAuthStore((state) => state.setAuth);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CoordRegValues>({
    resolver: zodResolver(coordRegSchema),
  });

  const onSubmit = async (data: CoordRegValues) => {
    setIsLoading(true);
    setError(null);

    try {
      await apiClient.post("/coordinators/register", {
        name: data.name,
        phone: data.phone,
        organization: data.organization,
        assigned_region: data.assigned_region,
      });

      // Refetch user profile to update Zustand auth store state
      const userResponse = await apiClient.get("/auth/me");
      if (accessToken && refreshToken) {
        setAuth(userResponse.data, accessToken, refreshToken);
      }

      router.push("/coordinator/dashboard");
    } catch (err: any) {
      console.error("Coordinator onboarding failure: ", err);
      setError(
        err.response?.data?.detail || "Failed to submit coordinator application. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-xl py-12 px-6">
      <div className="mb-8">
        <h2 className="text-xl font-bold tracking-tight text-zinc-950 dark:text-white">
          Coordinator Onboarding
        </h2>
        <p className="text-xs text-zinc-500">
          Apply to manage match logistics and emergency operations.
        </p>
      </div>

      {error && (
        <div className="mb-6 rounded-lg bg-red-50 p-4 text-xs font-semibold text-red-600 dark:bg-red-950/20 dark:text-red-400">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-1">
          <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
            Full Name
          </label>
          <input
            {...register("name")}
            type="text"
            placeholder="Kiran Deshmukh"
            className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
          />
          {errors.name && (
            <p className="text-[10px] text-red-600">{errors.name.message}</p>
          )}
        </div>

        <div className="space-y-1">
          <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
            Mobile Number
          </label>
          <input
            {...register("phone")}
            type="tel"
            placeholder="+919876543210"
            className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
          />
          {errors.phone && (
            <p className="text-[10px] text-red-600">{errors.phone.message}</p>
          )}
        </div>

        <div className="space-y-1">
          <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
            Affiliated Care Organization
          </label>
          <input
            {...register("organization")}
            type="text"
            placeholder="Indian Thalassemia Foundation"
            className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
          />
          {errors.organization && (
            <p className="text-[10px] text-red-600">{errors.organization.message}</p>
          )}
        </div>

        <div className="space-y-1">
          <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
            Assigned Coordination Region
          </label>
          <input
            {...register("assigned_region")}
            type="text"
            placeholder="Chennai Metro Division"
            className="h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900"
          />
          {errors.assigned_region && (
            <p className="text-[10px] text-red-600">{errors.assigned_region.message}</p>
          )}
        </div>

        <div className="pt-4">
          <button
            type="submit"
            disabled={isLoading}
            className="flex h-10 w-full items-center justify-center gap-1.5 rounded-md bg-brand-500 font-bold text-white transition-colors hover:bg-brand-600 disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Submitting credentials...
              </>
            ) : (
              <>
                Submit Application
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
