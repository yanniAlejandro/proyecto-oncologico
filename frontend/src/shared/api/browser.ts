import { createFetchTransport } from "./transport";

/** Prefijo del proxy de Astro hacia FastAPI (añade el token de la cookie en el servidor). */
export const API_PROXY_BASE = "/api/v1";

export const browserTransport = createFetchTransport(API_PROXY_BASE);
