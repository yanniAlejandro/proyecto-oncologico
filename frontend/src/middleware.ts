import { defineMiddleware } from "astro:middleware";
import { isRouteAllowed, type SessionUser } from "@/shared/auth/roles";
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

  if (!isRouteAllowed(context.url.pathname, context.locals.user)) {
    return context.redirect("/", 302);
  }

  const response = await next();
  // Las páginas dependen de la sesión: que ningún intermediario las cachee.
  if (response.headers.get("content-type")?.includes("text/html")) {
    response.headers.set("Cache-Control", "private, no-store");
  }
  return response;
});
