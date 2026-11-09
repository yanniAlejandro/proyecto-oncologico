import { load, serverTransport } from "@/shared/api/server";
import type { Helpline } from "../domain/types";
import { createHelplineApi } from "./helpline.api";

/**
 * La cabecera y el pie de TODAS las páginas muestran la línea de ayuda: se cachea 30 s en el
 * servidor para no llamar a la API en cada navegación. Es información pública (sin token).
 */
const TTL_MS = 30_000;
let cache: { at: number; data: Helpline } | null = null;

export async function getHelplineCached(now = Date.now()): Promise<Helpline | null> {
  if (cache && now - cache.at < TTL_MS) return cache.data;
  const { data } = await load(() => createHelplineApi(serverTransport(null)).get());
  if (data) cache = { at: now, data };
  return data ?? cache?.data ?? null;
}

export function invalidateHelplineCache() {
  cache = null;
}
