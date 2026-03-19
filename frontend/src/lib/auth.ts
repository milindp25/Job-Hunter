import type { AuthResponse } from "@/lib/types";

let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string): void {
  accessToken = token;
}

export function clearTokens(): void {
  accessToken = null;
}

export async function refreshAccessToken(): Promise<string | null> {
  try {
    const baseUrl =
      process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

    const response = await fetch(`${baseUrl}/auth/refresh`, {
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
