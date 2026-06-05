import React from "react";
import Link from "next/link";
import { 
  ArrowRight, 
  Activity, 
  Calendar, 
  HeartHandshake, 
  Users, 
  ShieldAlert, 
  Sparkles,
  Zap,
  Clock,
  TrendingUp
} from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-zinc-50 font-sans text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100 selection:bg-brand-500/20 relative">
      {/* Background Video for the top fold (Header + Hero) */}
      <div className="absolute top-0 inset-x-0 h-[580px] sm:h-[600px] md:h-[680px] z-0 overflow-hidden">
        <video 
          autoPlay 
          loop 
          muted 
          playsInline 
          className="h-full w-full object-cover"
        >
          <source src="/bg-video.mp4" type="video/mp4" />
        </video>
        {/* Overlay to ensure text readability */}
        <div className="absolute inset-0 bg-white/40 dark:bg-zinc-950/70 backdrop-blur-[1px]" />
      </div>

      {/* ── Navigation Header ── */}
      <header className="sticky top-0 z-50 w-full border-b border-zinc-200/80 bg-white/80 backdrop-blur-md dark:border-zinc-800/80 dark:bg-zinc-950/80">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2.5 text-lg font-bold tracking-tight">
            <div className="relative flex h-8.5 w-8.5 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-accent-500 p-[1.5px] shadow-sm">
              <div className="flex h-full w-full items-center justify-center rounded-full bg-zinc-900 text-[10px] font-black tracking-tighter text-white">
                <span className="text-brand-400">V</span>
                <span className="text-accent-500">C</span>
              </div>
            </div>
            <span className="font-display font-extrabold text-zinc-900 dark:text-white">
              VeinConnect <span className="text-brand-500 dark:text-brand-400">AI</span>
            </span>
          </Link>

          <div className="flex items-center gap-4">
            <Link 
              href="/login" 
              className="text-xs font-bold text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-200 transition-colors"
            >
              Sign In
            </Link>
            <Link 
              href="/signup" 
              className="inline-flex h-9 items-center justify-center rounded-full bg-brand-500 px-4 text-xs font-bold text-white shadow-sm shadow-brand-500/25 hover:bg-brand-600 transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* ── Hero Section ── */}
      <section className="relative z-10 overflow-hidden pt-20 pb-16 md:pt-28 md:pb-24">
        {/* Decorative subtle background gradients */}
        <div className="absolute top-0 right-1/4 -z-10 h-72 w-72 rounded-full bg-brand-500/5 blur-3xl" />
        <div className="absolute top-1/3 left-1/4 -z-10 h-96 w-96 rounded-full bg-accent-500/5 blur-3xl" />

        <div className="mx-auto max-w-7xl px-6 text-center">
          <div className="mx-auto inline-flex items-center gap-1.5 rounded-full border border-zinc-200 bg-white py-1 px-3 text-[10px] font-semibold text-zinc-600 shadow-sm dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400">
            <Sparkles className="h-3 w-3 text-accent-500" />
            <span>AI-Driven Thalassemia Care Coordination</span>
          </div>

          <h1 className="mx-auto mt-6 max-w-4xl font-display text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl text-zinc-900 dark:text-white leading-[1.1]">
            AI-Powered Recurring Transfusion <br />
            <span className="bg-gradient-to-r from-brand-500 to-accent-500 bg-clip-text text-transparent">
              Coordination Platform
            </span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-sm md:text-base text-zinc-600 dark:text-zinc-400 leading-relaxed">
            Every drop saves a life. VeinConnect AI automates matching, scheduling, and consensus mapping across Patients, Donors, Coordinators, and Hospitals to make regular Thalassemia care stress-free.
          </p>

          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link 
              href="/signup" 
              className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-full bg-brand-500 px-6 text-xs font-bold text-white shadow-md shadow-brand-500/20 hover:bg-brand-600 sm:w-auto transition-all"
            >
              Register a New Account
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link 
              href="/login" 
              className="inline-flex h-11 w-full items-center justify-center rounded-full border border-zinc-200 bg-white px-6 text-xs font-bold text-zinc-700 shadow-sm hover:bg-zinc-50 sm:w-auto dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800/80 transition-colors"
            >
              Sign In to Your Dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* ── Statistics strip ── */}
      <section className="border-y border-zinc-200 bg-white py-8 dark:border-zinc-800 dark:bg-zinc-900/50">
        <div className="mx-auto grid max-w-7xl grid-cols-2 gap-6 px-6 md:grid-cols-4">
          <div className="text-center md:border-r md:border-zinc-200 dark:md:border-zinc-800">
            <p className="font-display text-3xl font-extrabold text-brand-500">2,000+</p>
            <p className="mt-1 text-[10px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              Registered Donors
            </p>
          </div>
          <div className="text-center md:border-r md:border-zinc-200 dark:md:border-zinc-800">
            <p className="font-display text-3xl font-extrabold text-zinc-900 dark:text-white">500+</p>
            <p className="mt-1 text-[10px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              Active Patients
            </p>
          </div>
          <div className="text-center md:border-r md:border-zinc-200 dark:md:border-zinc-800">
            <p className="font-display text-3xl font-extrabold text-accent-500">98.4%</p>
            <p className="mt-1 text-[10px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              On-Time Transfusions
            </p>
          </div>
          <div className="text-center">
            <p className="font-display text-3xl font-extrabold text-zinc-900 dark:text-white">5+</p>
            <p className="mt-1 text-[10px] font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              Major Cities Active
            </p>
          </div>
        </div>
      </section>

      {/* ── Key Features Grid ── */}
      <section className="py-16 md:py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center">
            <h2 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">
              Advanced Healthcare Coordination Engine
            </h2>
            <p className="mt-3 text-xs text-zinc-500 dark:text-zinc-400 max-w-md mx-auto">
              VeinConnect replaces ad-hoc emergency calls with predictive matching and structured schedules.
            </p>
          </div>

          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {/* Feature 1 */}
            <div className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900/40">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-950/20 dark:text-brand-400">
                <Users className="h-5 w-5" />
              </div>
              <h3 className="mt-4 font-display text-base font-bold">🤖 Predictive Matching</h3>
              <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
                Matches patients with compatible, reliable donors near them, sorting by real travel distance, schedules, and reliability history scores.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900/40">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-950/20 dark:text-brand-400">
                <Calendar className="h-5 w-5" />
              </div>
              <h3 className="mt-4 font-display text-base font-bold">✅ Consensus Coordination</h3>
              <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
                4-party consensus engine. Transfusions require confirmations from patient, donor, hospital, and coordinator to avoid no-shows.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900/40 sm:col-span-2 lg:col-span-1">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-950/20 dark:text-brand-400">
                <ShieldAlert className="h-5 w-5" />
              </div>
              <h3 className="mt-4 font-display text-base font-bold">🚨 Emergency Command</h3>
              <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
                Instantly trigger crisis modes. The system alerts standby donors via automated text channels, prioritizing them by likelihood of positive response.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Role Portal Selection ── */}
      <section className="bg-zinc-100/50 py-16 dark:bg-zinc-900/10 border-t border-zinc-200 dark:border-zinc-800">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center">
            <h2 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">
              Log In to Your Role-Specific Portal
            </h2>
            <p className="mt-3 text-xs text-zinc-500 dark:text-zinc-400">
              Each stakeholder has custom views, workflows, and automated tasks.
            </p>
          </div>

          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {/* Patient Portal */}
            <Link 
              href="/login" 
              className="group block rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm hover:border-brand-500 transition-all dark:border-zinc-800 dark:bg-zinc-900/30"
            >
              <Activity className="h-6 w-6 text-brand-500 transition-transform group-hover:scale-110" />
              <h3 className="mt-4 font-display text-sm font-bold text-zinc-900 dark:text-white">
                Patient Portal
              </h3>
              <p className="mt-1.5 text-[11px] text-zinc-500 dark:text-zinc-400 leading-relaxed">
                Track predicted cycles, rank hospital preferences, and manage consensus schedules.
              </p>
            </Link>

            {/* Donor Portal */}
            <Link 
              href="/login" 
              className="group block rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm hover:border-brand-500 transition-all dark:border-zinc-800 dark:bg-zinc-900/30"
            >
              <HeartHandshake className="h-6 w-6 text-brand-500 transition-transform group-hover:scale-110" />
              <h3 className="mt-4 font-display text-sm font-bold text-zinc-900 dark:text-white">
                Donor Hub
              </h3>
              <p className="mt-1.5 text-[11px] text-zinc-500 dark:text-zinc-400 leading-relaxed">
                Manage availability calendars, confirm scheduling requests, and track travel credits/rewards.
              </p>
            </Link>

            {/* Coordinator Portal */}
            <Link 
              href="/login" 
              className="group block rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm hover:border-brand-500 transition-all dark:border-zinc-800 dark:bg-zinc-900/30"
            >
              <Users className="h-6 w-6 text-brand-500 transition-transform group-hover:scale-110" />
              <h3 className="mt-4 font-display text-sm font-bold text-zinc-900 dark:text-white">
                Coordinator Command
              </h3>
              <p className="mt-1.5 text-[11px] text-zinc-500 dark:text-zinc-400 leading-relaxed">
                Audit scheduling algorithms, trigger alerts, manage emergency overrides, and reimburse expenses.
              </p>
            </Link>

            {/* Hospital Portal */}
            <Link 
              href="/login" 
              className="group block rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm hover:border-brand-500 transition-all dark:border-zinc-800 dark:bg-zinc-900/30"
            >
              <ShieldAlert className="h-6 w-6 text-brand-500 transition-transform group-hover:scale-110" />
              <h3 className="mt-4 font-display text-sm font-bold text-zinc-900 dark:text-white">
                Hospital Portal
              </h3>
              <p className="mt-1.5 text-[11px] text-zinc-500 dark:text-zinc-400 leading-relaxed">
                Update operational hours, confirm bed availability, manage daily transfusion queues, and sync records.
              </p>
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-zinc-200 py-10 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="mx-auto max-w-7xl px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-[10px] font-semibold text-zinc-500">
            © 2026 VeinConnect AI. Built for Thalassemia Welfare. All rights reserved.
          </p>
          <div className="flex gap-4 text-[10px] font-bold text-zinc-500 dark:text-zinc-400">
            <Link href="/login" className="hover:text-brand-500">Sign In</Link>
            <span>•</span>
            <Link href="/signup" className="hover:text-brand-500">Sign Up</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
