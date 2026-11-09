import { defineMiddleware } from "astro:middleware";
import { canUsePanel, LEGACY_REDIRECTS, loginHref, routeDecision, safeNext, type SessionUser } from "@/shared/auth/roles";
import { clearSessionToken, readSessionToken } from "@/shared/auth/session";
import { serverTransport } from "@/shared/api/server";
import { ApiError } from "@/shared/api/transport";

/**
 * 1. Resuelve el usuario de la cookie de sesión (GET /auth/me).
 * 2. Aplica las guardas de rol en el servidor: sin parpadeos ni expulsiones al
 *    recargar (BUG-001).
 * El proxy /api/v1 no necesita el usuario: FastAPI valida el token.
 */
export const onRequest = defineMiddleware(async (context, next) => {
  const token = readSessionToken(context.cookies);
  context.locals.token = token;
  context.locals.user = null;

  if (context.url.pathname.startsWith("/api/v1/")) return next();

  if (token) {
    try {
      context.locals.user = await serverTransport(token).request<SessionUser>("GET", "/auth/me");
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        clearSessionToken(context.cookies); // token caducado o usuario desactivado
        context.locals.token = null;
      } else {
        console.error("No se pudo resolver la sesión", error);
      }
    }
  }

  const legacy = LEGACY_REDIRECTS[context.url.pathname.replace(/\/$/, "")];
  if (legacy) return context.redirect(legacy, 301);

  const { pathname, search } = context.url;
  const user = context.locals.user;

  // Con sesión, /login no tiene sentido: directo al destino.
  if (pathname === "/login" && user) return context.redirect(safeNext(context.url.searchParams.get("next")), 302);

  const decision = routeDecision(pathname, user);
  if (decision === "login") return context.redirect(loginHref(pathname + search), 302);
  if (decision === "forbidden") return context.redirect(canUsePanel(user) && pathname !== "/admin" ? "/admin" : "/", 302);

  const response = await next();
  // Las páginas dependen de la sesión: que ningún intermediario las cachee.
  if (response.headers.get("content-type")?.includes("text/html")) {
    response.headers.set("Cache-Control", "private, no-store");
  }
  return response;
});
