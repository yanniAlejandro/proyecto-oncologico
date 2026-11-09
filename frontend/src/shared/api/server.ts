import { API_URL } from "astro:env/server";
import { createFetchTransport, getErrorMessage, type Transport } from "./transport";

/** Transporte SSR: llama a FastAPI directamente con el JWT de la sesión. */
export function serverTransport(token: string | null): Transport {
  return createFetchTransport(API_URL, (): Record<string, string> => (token ? { Authorization: `Bearer ${token}` } : {}));
}

export { API_URL };

/** Carga SSR que no rompe la página si la API falla: devuelve el mensaje para mostrarlo. */
export async function load<T>(fn: () => Promise<T>): Promise<{ data: T | null; error: string | null }> {
  try {
    return { data: await fn(), error: null };
  } catch (error) {
    console.error(error);
    return { data: null, error: getErrorMessage(error) };
  }
}
