"use client";

import { create } from "zustand";
import { api, resetRefreshState } from "@/lib/api";
import { setAccessToken, clearTokens } from "@/lib/auth";
import type { AuthResponse, User } from "@/lib/types";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchUser: () => Promise<void>;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,

  login: async (email: string, password: string) => {
    set({ isLoading: true });
    try {
      const { data } = await api.post<AuthResponse>("/auth/login", {
        email,
        password,
      });
      setAccessToken(data.access_token);
      resetRefreshState();
      set({ user: data.user, isAuthenticated: true, isLoading: false });
    } catch {
      set({ isLoading: false });
      throw new Error("Login failed. Please check your credentials.");
    }
  },

  register: async (name: string, email: string, password: string) => {
    set({ isLoading: true });
    try {
      const { data } = await api.post<AuthResponse>("/auth/register", {
        full_name: name,
        email,
        password,
      });
      setAccessToken(data.access_token);
      resetRefreshState();
      set({ user: data.user, isAuthenticated: true, isLoading: false });
    } catch {
      set({ isLoading: false });
      throw new Error("Registration failed. Please try again.");
    }
  },

  logout: async () => {
    try {
      await api.post("/auth/logout");
    } catch {
      // Proceed with local cleanup even if server logout fails
    } finally {
      clearTokens();
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  fetchUser: async () => {
    set({ isLoading: true });
    try {
      const { data } = await api.get<User>("/users/me");
      set({ user: data, isAuthenticated: true, isLoading: false });
    } catch {
      clearTokens();
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  setUser: (user: User) => {
    set({ user, isAuthenticated: true });
  },
}));
