import type { APIRoute } from "astro";
import { serverTransport } from "@/shared/api/server";
import { ApiError } from "@/shared/api/transport";
import { writeSessionToken } from "@/shared/auth/session";

/** Inicia sesión contra FastAPI y guarda el JWT en una cookie httpOnly (el navegador nunca lo ve). */
export const POST: APIRoute = async ({ request, cookies }) => {
  let payload: { email?: unknown; password?: unknown };
  try {
    payload = await request.json();
  } catch {
    return Response.json({ detail: "Solicitud inválida" }, { status: 400 });
  }
  try {
    const { access_token } = await serverTransport(null).request<{ access_token: string }>("POST", "/auth/login", {
      json: { email: payload.email, password: payload.password },
    });
    writeSessionToken(cookies, access_token);
    return Response.json({ ok: true });
  } catch (error) {
    if (error instanceof ApiError) return Response.json({ detail: error.message }, { status: error.status });
    return Response.json({ detail: "No se pudo contactar con el servidor" }, { status: 502 });
  }
};
