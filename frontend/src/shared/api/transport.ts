/**
 * Puerto de transporte HTTP. Las APIs de cada feature reciben un Transport,
 * así el mismo código sirve en SSR (servidor → FastAPI con el token de la cookie)
 * y en las islas React (navegador → proxy /api/v1 de Astro).
 */

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export type Query = Record<string, string | number | boolean | null | undefined>;

export interface RequestOptions {
  query?: Query;
  json?: unknown;
  body?: FormData;
}

export interface Transport {
  request<T>(method: string, path: string, options?: RequestOptions): Promise<T>;
}

const GENERIC_ERROR = "Ha ocurrido un error inesperado";

export function buildUrl(base: string, path: string, query?: Query): string {
  const url = `${base.replace(/\/$/, "")}${path}`;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null && value !== "") params.set(key, String(value));
  }
  const qs = params.toString();
  return qs ? `${url}?${qs}` : url;
}

/** Traduce el `detail` de FastAPI (string o lista de errores de validación) a texto. */
export async function errorFromResponse(res: Response): Promise<ApiError> {
  let message = GENERIC_ERROR;
  try {
    const data = (await res.json()) as { detail?: unknown };
    if (typeof data.detail === "string") message = data.detail;
    else if (Array.isArray(data.detail))
      message = data.detail.map((d: { msg?: string }) => d.msg ?? "").filter(Boolean).join(", ") || message;
  } catch {
    /* cuerpo no JSON */
  }
  return new ApiError(res.status, message);
}

export function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : GENERIC_ERROR;
}

export function createFetchTransport(
  baseUrl: string,
  getHeaders: () => HeadersInit = () => ({}),
  fetchImpl: typeof fetch = (...args) => fetch(...args),
): Transport {
  return {
    async request<T>(method: string, path: string, options: RequestOptions = {}): Promise<T> {
      const headers = new Headers(getHeaders());
      let body: BodyInit | undefined;
      if (options.json !== undefined) {
        headers.set("Content-Type", "application/json");
        body = JSON.stringify(options.json);
      } else if (options.body) {
        body = options.body; // el navegador pone el boundary del multipart
      }
      const res = await fetchImpl(buildUrl(baseUrl, path, options.query), { method, headers, body });
      if (!res.ok) throw await errorFromResponse(res);
      if (res.status === 204) return undefined as T;
      return (await res.json()) as T;
    },
  };
}
