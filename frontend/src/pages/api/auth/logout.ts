import type { APIRoute } from "astro";
import { clearSessionToken } from "@/shared/auth/session";

export const POST: APIRoute = ({ cookies, redirect }) => {
  clearSessionToken(cookies);
  return redirect("/", 303);
};
