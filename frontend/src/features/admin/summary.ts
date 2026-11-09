/** Resumen del panel: reglas puras para el feed de actividad (testeables sin red). */

export interface ActivityItem {
  kind: string;
  title: string;
  who: string | null;
  at: string;
  href: string;
}

/** Une las fuentes y devuelve las más recientes primero. */
export function latestActivity(sources: ActivityItem[][], limit = 8): ActivityItem[] {
  return sources
    .flat()
    .filter((i) => !Number.isNaN(Date.parse(i.at)))
    .sort((a, b) => Date.parse(b.at) - Date.parse(a.at))
    .slice(0, limit);
}

const PENDING_MARK = /^>\s*Borrador pendiente de validar/i;

/** Apartados de «Quiénes somos» que aún llevan la nota de borrador. */
export const pendingDrafts = (bodies: string[]) => bodies.filter((b) => PENDING_MARK.test(b.trim())).length;
