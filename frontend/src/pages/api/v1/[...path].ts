import type { APIRoute } from "astro";
import { API_URL } from "@/shared/api/server";

/**
 * Proxy del navegador hacia FastAPI: añade `Authorization` a partir de la cookie
 * httpOnly y reenvía el cuerpo (JSON o multipart) y la respuesta en streaming
 * (descargas y visor de documentos).
 */
const FORWARD_REQUEST_HEADERS = ["content-type", "accept", "range"];
const FORWARD_RESPONSE_HEADERS = [
  "content-type",
  "content-length",
  "content-disposition",
  "content-range",
  "accept-ranges",
  "cache-control",
  "etag",
  "last-modified",
  "x-content-type-options",
];

export const ALL: APIRoute = async ({ request, params, url, locals }) => {
  const target = `${API_URL.replace(/\/$/, "")}/${params.path ?? ""}${url.search}`;
  const headers = new Headers();
  for (const name of FORWARD_REQUEST_HEADERS) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  if (locals.token) headers.set("Authorization", `Bearer ${locals.token}`);

  const hasBody = !["GET", "HEAD"].includes(request.method);
  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: request.method,
      headers,
      body: hasBody ? request.body : undefined,
      // @ts-expect-error: necesario en Node para enviar un ReadableStream como cuerpo
      duplex: hasBody ? "half" : undefined,
      redirect: "manual",
    });
  } catch {
    return Response.json({ detail: "No se pudo contactar con el servidor" }, { status: 502 });
  }

  const out = new Headers();
  for (const name of FORWARD_RESPONSE_HEADERS) {
    const value = upstream.headers.get(name);
    if (value) out.set(name, value);
  }
  return new Response(upstream.body, { status: upstream.status, headers: out });
};
