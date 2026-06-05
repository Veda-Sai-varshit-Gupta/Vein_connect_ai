"use client";

import React from "react";
import Link from "next/link";

interface AuthLayoutProps {
  children: React.ReactNode;
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen w-full flex-col md:flex-row bg-zinc-50 dark:bg-zinc-950">
      {/* Brand Side Panel */}
      <div className="hidden flex-col justify-between bg-zinc-900 px-10 py-12 text-white md:flex md:w-[40%] lg:w-[35%] dark:bg-black border-r border-zinc-800">
        <div>
          <Link href="/" className="flex items-center gap-2 text-xl font-bold tracking-tight">
            <div className="relative flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-accent-500 p-[1.5px] shadow-sm">
              <div className="flex h-full w-full items-center justify-center rounded-full bg-zinc-900 text-[10px] font-black tracking-tighter text-white">
                <span className="text-brand-400">V</span>
                <span className="text-accent-500">C</span>
              </div>
            </div>
            <span>VeinConnect AI</span>
          </Link>
          <p className="mt-2 text-xs font-semibold text-zinc-400">
            Recurring Transfusion Coordination Platform
          </p>
        </div>

        <div className="my-auto space-y-6">
          <blockquote className="space-y-2">
            <p className="text-lg font-medium leading-relaxed italic text-zinc-100">
              "Thalassemia care demands coordination, not just donor discovery. VeinConnect automates matching to make regular transfusions stress-free."
            </p>
            <footer className="text-xs font-semibold text-brand-500">
              — Thalassemia Welfare Association India
            </footer>
          </blockquote>

          {/* Mini Statistics Strip */}
          <div className="grid grid-cols-2 gap-4 border-t border-zinc-800 pt-6">
            <div>
              <p className="text-2xl font-bold text-white">500+</p>
              <p className="text-[10px] font-medium uppercase tracking-wider text-zinc-400">
                Patients Tracked
              </p>
            </div>
            <div>
              <p className="text-2xl font-bold text-white">2,000+</p>
              <p className="text-[10px] font-medium uppercase tracking-wider text-zinc-400">
                Matched Donors
              </p>
            </div>
          </div>
        </div>

        <div>
          <p className="text-[10px] font-medium text-zinc-500">
            © 2026 VeinConnect AI. All rights reserved.
          </p>
        </div>
      </div>

      {/* Main Credentials Panel */}
      <div className="flex flex-1 items-center justify-center p-6 md:p-12 lg:p-16">
        <div className="w-full max-w-md">{children}</div>
      </div>
    </div>
  );
}
