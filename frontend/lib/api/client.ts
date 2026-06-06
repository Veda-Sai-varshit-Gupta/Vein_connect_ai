import axios from "axios";
import { useAuthStore } from "../stores/authStore";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 60000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request Interceptor: Inject Auth JWT Header
apiClient.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Silent Token Refresh & Retry on 401
let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Do not attempt token refresh for auth requests (login, signup, refresh, logout)
    const isAuthRoute = originalRequest.url?.includes("/auth/login") || 
                        originalRequest.url?.includes("/auth/signup") || 
                        originalRequest.url?.includes("/auth/refresh") || 
                        originalRequest.url?.includes("/auth/logout");

    // Check if error is unauthorized, is not an auth route, and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry && !isAuthRoute) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      const refreshToken = useAuthStore.getState().refreshToken;

      // If we don't have a refresh token, clean up and redirect immediately
      if (!refreshToken) {
        useAuthStore.getState().clearAuth();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Exchange refresh token for a new access token
        const refreshResponse = await axios.post(
          `${API_BASE_URL}/api/v1/auth/refresh`,
          {
            refresh_token: refreshToken
          }
        );

        const newAccessToken = refreshResponse.data.access_token;
        if (newAccessToken) {
          useAuthStore.getState().updateToken(newAccessToken);
          
          // Update cookies as well so Next.js Middleware sees it
          if (typeof document !== "undefined") {
            const role = useAuthStore.getState().role;
            document.cookie = `veinconnect-token=${newAccessToken}; path=/; max-age=3600; SameSite=Lax`;
            if (role) {
              document.cookie = `veinconnect-role=${role}; path=/; max-age=3600; SameSite=Lax`;
            }
          }

          apiClient.defaults.headers.common["Authorization"] = `Bearer ${newAccessToken}`;
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          processQueue(null, newAccessToken);
          isRefreshing = false;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        processQueue(refreshError, null);
        isRefreshing = false;
        // Refresh token failed, clean up credentials and redirect
        useAuthStore.getState().clearAuth();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);
