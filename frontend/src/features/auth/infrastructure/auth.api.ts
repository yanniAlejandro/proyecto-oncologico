import { ApiError, errorFromResponse } from "@/shared/api/transport";

/** Login contra el BFF de Astro: guarda el JWT en cookie httpOnly. */
export async function login(email: string, password: string, fetchImpl: typeof fetch = fetch): Promise<void> {
  const res = await fetchImpl("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw await errorFromResponse(res);
}

export { ApiError };
