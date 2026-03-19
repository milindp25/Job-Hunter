import type { AuthResponse } from "@/lib/types";

const TOKEN_KEY = "jh_access_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

export async function refreshAccessToken(): Promise<string | null> {
  try {
    const baseUrl =
      process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

    const response = await fetch(`${baseUrl}/api/v1/auth/refresh`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      clearTokens();
      return null;
    }

    const data: AuthResponse = await response.json();
    setAccessToken(data.access_token);
    return data.access_token;
  } catch {
    clearTokens();
    return null;
  }
}
