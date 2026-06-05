"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useAuthStore } from "../../../lib/stores/authStore";
import { apiClient } from "../../../lib/api/client";
import { UserRole } from "../../../lib/types/common";
import {
  Mail,
  Phone,
  KeyRound,
  Eye,
  EyeOff,
  Loader2,
  HeartPulse,
  HeartHandshake,
  Workflow,
  Hospital,
} from "lucide-react";

// Form validation matching Pydantic SignupRequest
const signupSchema = z
  .object({
    email: z.string().email("Invalid email address format"),
    phone: z.string().regex(/^(\+91)?[6-9]\d{9}$/, "Must be valid 10-digit Indian phone number"),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/\d/, "Password must contain at least one digit"),
    confirmPassword: z.string(),
    role: z.enum(["patient", "donor", "coordinator", "hospital", "admin"], {
      message: "Please select an account type",
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type SignupFormValues = z.infer<typeof signupSchema>;

export default function SignupPage() {
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      role: "patient",
    },
  });

  const selectedRole = watch("role");

  const onSubmit = async (data: SignupFormValues) => {
    setIsLoading(true);
    setError(null);

    // Prepare payload matching backend Pydantic schema
    const payload = {
      email: data.email,
      phone: data.phone,
      password: data.password,
      role: data.role,
    };

    try {
      const response = await apiClient.post("/auth/signup", payload);
      const { access_token, refresh_token, role } = response.data;

      // Fetch user profile object
      const userResponse = await apiClient.get("/auth/me", {
        headers: {
          Authorization: `Bearer ${access_token}`,
        },
      });
      const user = userResponse.data;

      // Set cookie for Next.js Edge route guard middleware
      document.cookie = `veinconnect-token=${access_token}; path=/; max-age=3600; SameSite=Lax`;
      document.cookie = `veinconnect-role=${role}; path=/; max-age=3600; SameSite=Lax`;

      // Set Zustand credentials
      setAuth(user, access_token, refresh_token);

      // Route based on onboarding destination
      if (role === "admin") {
        router.push("/admin/dashboard");
      } else {
        router.push(`/register/${role}`);
      }
    } catch (err: any) {
      console.error("Signup failure: ", err);
      setError(
        err.response?.data?.detail || "Registration failed. Email or phone might already exist."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const roles = [
    { id: "patient", label: "Patient Care", desc: "Manage transfusion schedules", icon: HeartPulse },
    { id: "donor", label: "Donor Profile", desc: "Donate blood & earn rewards", icon: HeartHandshake },
    { id: "coordinator", label: "Coordinator", desc: "Coordinate matches & emergencies", icon: Workflow },
    { id: "hospital", label: "Hospital", desc: "Set beds & schedule logs", icon: Hospital },
  ] as const;

  return (
    <div className="w-full space-y-6">
      <div className="space-y-2 text-center md:text-left">
        <h2 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-white">
          Create account
        </h2>
        <p className="text-xs text-zinc-500">
          Join VeinConnect AI to start matching care instantly.
        </p>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-xs font-semibold text-red-600 dark:bg-red-950/20 dark:text-red-400">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Role Card Selector */}
        <div className="space-y-2">
          <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
            Account Type
          </label>
          <div className="grid grid-cols-2 gap-3">
            {roles.map((roleObj) => {
              const Icon = roleObj.icon;
              const isSelected = selectedRole === roleObj.id;
              return (
                <button
                  key={roleObj.id}
                  type="button"
                  onClick={() => setValue("role", roleObj.id)}
                  className={`flex flex-col items-start gap-2 rounded-lg border p-3 text-left transition-all outline-none ${
                    isSelected
                      ? "border-brand-500 bg-brand-50/20 dark:bg-brand-950/10"
                      : "border-zinc-200 hover:border-zinc-300 dark:border-zinc-800 dark:hover:border-zinc-700"
                  }`}
                >
                  <div
                    className={`flex h-8 w-8 items-center justify-center rounded-lg ${
                      isSelected
                        ? "bg-brand-500 text-white"
                        : "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400"
                    }`}
                  >
                    <Icon className="h-4.5 w-4.5" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-zinc-900 dark:text-white">
                      {roleObj.label}
                    </p>
                    <p className="text-[9px] text-zinc-500 leading-tight">
                      {roleObj.desc}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
          {errors.role && (
            <p className="text-[10px] font-medium text-red-600 dark:text-red-400">
              {errors.role.message}
            </p>
          )}
        </div>

        {/* Email Field */}
        <div className="space-y-1">
          <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
            Email Address
          </label>
          <div className="relative">
            <Mail className="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-zinc-400" />
            <input
              {...register("email")}
              type="email"
              placeholder="name@hospital.com"
              className="h-10 w-full rounded-md border border-zinc-200 bg-white pl-10 pr-4 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900 dark:focus:border-brand-500"
            />
          </div>
          {errors.email && (
            <p className="text-[10px] font-medium text-red-600 dark:text-red-400">
              {errors.email.message}
            </p>
          )}
        </div>

        {/* Phone Field */}
        <div className="space-y-1">
          <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
            Phone Number (India)
          </label>
          <div className="relative">
            <Phone className="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-zinc-400" />
            <input
              {...register("phone")}
              type="tel"
              placeholder="+919876543210"
              className="h-10 w-full rounded-md border border-zinc-200 bg-white pl-10 pr-4 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900 dark:focus:border-brand-500"
            />
          </div>
          {errors.phone && (
            <p className="text-[10px] font-medium text-red-600 dark:text-red-400">
              {errors.phone.message}
            </p>
          )}
        </div>

        {/* Passwords */}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
              Password
            </label>
            <div className="relative">
              <KeyRound className="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-zinc-400" />
              <input
                {...register("password")}
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                className="h-10 w-full rounded-md border border-zinc-200 bg-white pl-10 pr-4 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900 dark:focus:border-brand-500"
              />
            </div>
            {errors.password && (
              <p className="text-[10px] font-medium text-red-600 leading-tight dark:text-red-400">
                {errors.password.message}
              </p>
            )}
          </div>

          <div className="space-y-1">
            <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
              Confirm
            </label>
            <div className="relative">
              <KeyRound className="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-zinc-400" />
              <input
                {...register("confirmPassword")}
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                className="h-10 w-full rounded-md border border-zinc-200 bg-white pl-10 pr-4 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900 dark:focus:border-brand-500"
              />
            </div>
            {errors.confirmPassword && (
              <p className="text-[10px] font-medium text-red-600 dark:text-red-400">
                {errors.confirmPassword.message}
              </p>
            )}
          </div>
        </div>

        {/* Toggle Show Passwords Option */}
        <div className="flex items-center justify-end">
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="flex items-center gap-1 text-[10px] font-bold text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-300"
          >
            {showPassword ? "Hide Passwords" : "Show Passwords"}
          </button>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={isLoading}
          className="flex h-10 w-full items-center justify-center gap-2 rounded-md bg-brand-500 font-bold text-white transition-colors hover:bg-brand-600 disabled:opacity-50"
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Creating profile account...
            </>
          ) : (
            "Create Account"
          )}
        </button>
      </form>

      <div className="text-center text-xs text-zinc-600 dark:text-zinc-400">
        Already have an account?{" "}
        <Link
          href="/login"
          className="font-bold text-brand-500 hover:underline hover:text-brand-600"
        >
          Log in
        </Link>
      </div>
    </div>
  );
}
