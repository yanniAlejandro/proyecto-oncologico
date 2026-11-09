import type { AstroCookies } from "astro";
import { SESSION_COOKIE_SECURE } from "astro:env/server";

export const SESSION_COOKIE = "holh_session";
const MAX_AGE_SECONDS = 8 * 60 * 60; // igual que ACCESS_TOKEN_EXPIRE_MINUTES del backend

export function readSessionToken(cookies: AstroCookies): string | null {
  return cookies.get(SESSION_COOKIE)?.value ?? null;
}

export function writeSessionToken(cookies: AstroCookies, token: string): void {
  cookies.set(SESSION_COOKIE, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: SESSION_COOKIE_SECURE,
    path: "/",
    maxAge: MAX_AGE_SECONDS,
  });
}

export function clearSessionToken(cookies: AstroCookies): void {
  cookies.delete(SESSION_COOKIE, { path: "/" });
}
