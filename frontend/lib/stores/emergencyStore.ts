import { create } from "zustand";

interface EmergencyState {
  activeEmergencyId: string | null;
  urgencyLevel: "routine" | "urgent" | "emergency" | null;
  isActive: boolean;
  setEmergency: (id: string | null, urgency?: "routine" | "urgent" | "emergency") => void;
  clearEmergency: () => void;
}

export const useEmergencyStore = create<EmergencyState>((set) => ({
  activeEmergencyId: null,
  urgencyLevel: null,
  isActive: false,
  setEmergency: (id, urgency = "emergency") =>
    set({
      activeEmergencyId: id,
      urgencyLevel: urgency,
      isActive: id !== null,
    }),
  clearEmergency: () =>
    set({
      activeEmergencyId: null,
      urgencyLevel: null,
      isActive: false,
    }),
}));
