"use client";

import React from "react";
import { useEmergencyStore } from "../../lib/stores/emergencyStore";
import { AlertOctagon, ShieldAlert, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function EmergencyBanner() {
  const { isActive, activeEmergencyId, urgencyLevel } = useEmergencyStore();

  if (!isActive) return null;

  return (
    <div className="flex w-full items-center justify-between bg-red-600 px-6 py-2.5 text-white animate-pulse">
      <div className="flex items-center gap-2 text-xs font-bold tracking-wide">
        <AlertOctagon className="h-4 w-4 animate-spin text-white" />
        <span>
          CRITICAL ALERT: Active emergency match route initialized (ID: {activeEmergencyId}). Urgency level: {urgencyLevel?.toUpperCase()}.
        </span>
      </div>
      <Link
        href="/coordinator/emergency"
        className="flex items-center gap-1 rounded bg-white px-2.5 py-1 text-[10px] font-bold text-red-600 transition-colors hover:bg-zinc-100"
      >
        View Emergency Hub
        <ArrowRight className="h-3 w-3" />
      </Link>
    </div>
  );
}
