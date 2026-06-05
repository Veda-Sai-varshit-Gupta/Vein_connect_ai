import { create } from "zustand";
import { persist } from "zustand/middleware";
import { User, UserRole } from "../types/common";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  setAuth: (user: User, token: string, refreshToken: string) => void;
  clearAuth: () => void;
  updateToken: (token: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      role: null,
      isAuthenticated: false,
      setAuth: (user, token, refreshToken) =>
        set({
          user,
          accessToken: token,
          refreshToken,
          role: user.role,
          isAuthenticated: true,
        }),
      clearAuth: () => {
        if (typeof document !== "undefined") {
          document.cookie = "veinconnect-token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax";
          document.cookie = "veinconnect-role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax";
        }
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          role: null,
          isAuthenticated: false,
        });
      },
      updateToken: (token) =>
        set({
          accessToken: token,
        }),
    }),
    {
      name: "veinconnect-auth",
    }
  )
);
