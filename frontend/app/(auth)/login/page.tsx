"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useAuthStore } from "../../../lib/stores/authStore";
import { apiClient } from "../../../lib/api/client";
import { KeyRound, Mail, Eye, EyeOff, Loader2 } from "lucide-react";

// Form validation schema matching backend
const loginSchema = z.object({
  email: z.string().email("Invalid email address format"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormValues) => {
    setIsLoading(true);
    setError(null);

    try {
      // Connect to FastAPI endpoint
      const response = await apiClient.post("/auth/login", data);
      const { access_token, refresh_token, role } = response.data;

      // Extract user info (simulate User object matching schemas)
      const userResponse = await apiClient.get("/auth/me", {
        headers: {
          Authorization: `Bearer ${access_token}`,
        },
      });

      const user = userResponse.data;

      // Set cookie for Edge middleware guards (expires in 1 hour matching token)
      document.cookie = `veinconnect-token=${access_token}; path=/; max-age=3600; SameSite=Lax`;
      document.cookie = `veinconnect-role=${role}; path=/; max-age=3600; SameSite=Lax`;

      // Set Zustand store credentials
      setAuth(user, access_token, refresh_token);

      // Route based on role and onboarding status
      if (role !== "admin" && !user.is_onboarded) {
        router.push(`/register/${role}`);
      } else {
        router.push(`/${role}/dashboard`);
      }
    } catch (err: any) {
      console.error("Login failure: ", err);
      setError(
        err.response?.data?.detail || "Invalid login credentials. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full space-y-6">
      <div className="space-y-2 text-center md:text-left">
        <h2 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-white">
          Welcome back
        </h2>
        <p className="text-xs text-zinc-500">
          Enter your registered email below to log in.
        </p>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-xs font-semibold text-red-600 dark:bg-red-950/20 dark:text-red-400">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
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

        {/* Password Field */}
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
              className="h-10 w-full rounded-md border border-zinc-200 bg-white pl-10 pr-10 text-xs outline-none focus:border-brand-500 dark:border-zinc-800 dark:bg-zinc-900 dark:focus:border-brand-500"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute top-1/2 right-3 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.password && (
            <p className="text-[10px] font-medium text-red-600 dark:text-red-400">
              {errors.password.message}
            </p>
          )}
        </div>

        {/* Submit button */}
        <button
          type="submit"
          disabled={isLoading}
          className="flex h-10 w-full items-center justify-center gap-2 rounded-md bg-brand-500 font-bold text-white transition-colors hover:bg-brand-600 disabled:opacity-50"
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Verifying credentials...
            </>
          ) : (
            "Log In"
          )}
        </button>
      </form>

      <div className="text-center text-xs text-zinc-600 dark:text-zinc-400">
        New to VeinConnect?{" "}
        <Link
          href="/signup"
          className="font-bold text-brand-500 hover:underline hover:text-brand-600"
        >
          Create account
        </Link>
      </div>
    </div>
  );
}
