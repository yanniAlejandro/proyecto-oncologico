export interface Slot {
  /** 0 = lunes … 6 = domingo */
  weekday: number;
  start: string; // "HH:MM"
  end: string;
}

export interface Status {
  available_now: boolean;
  next_opening: string | null;
}

export interface Professional {
  id: string;
  full_name: string;
  specialty: string;
  phone: string;
  sort_order: number;
  is_active: boolean;
  slots: Slot[];
  status: Status | null;
}

export interface HelplineConfig {
  phone: string;
  label: string;
  off_hours_message: string;
  emergency_phone: string | null;
  slots: Slot[];
  daily_hours: number[];
  meets_minimum: boolean;
}

export interface Helpline {
  config: HelplineConfig;
  status: Status;
  professionals: Professional[];
  weekdays: string[];
}

export type ConfigInput = Pick<HelplineConfig, "phone" | "label" | "off_hours_message" | "emergency_phone" | "slots">;
export type ProfessionalInput = Pick<Professional, "full_name" | "specialty" | "phone" | "sort_order" | "is_active" | "slots">;

export const WEEKDAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];
export const MIN_DAILY_HOURS = 6;

/** `tel:` sin espacios ni paréntesis. */
export const telHref = (phone: string) => `tel:${phone.replace(/[^\d+]/g, "")}`;

const lower = (s: string) => s.toLowerCase();

/**
 * Agrupa días consecutivos con el mismo horario:
 * «Lunes a viernes: 08:00–16:00 · Sábado y domingo: 09:00–15:00».
 */
export function summarizeSlots(slots: Slot[]): string[] {
  const byDay = WEEKDAYS.map((_, d) =>
    slots
      .filter((s) => s.weekday === d)
      .sort((a, b) => a.start.localeCompare(b.start))
      .map((s) => `${s.start}–${s.end}`)
      .join(", "),
  );
  const lines: string[] = [];
  let d = 0;
  while (d < 7) {
    if (!byDay[d]) {
      d += 1;
      continue;
    }
    let end = d;
    while (end + 1 < 7 && byDay[end + 1] === byDay[d]) end += 1;
    const days =
      end === d
        ? WEEKDAYS[d]
        : end === d + 1
          ? `${WEEKDAYS[d]} y ${lower(WEEKDAYS[end])}`
          : `${WEEKDAYS[d]} a ${lower(WEEKDAYS[end])}`;
    lines.push(`${days}: ${byDay[d]}`);
    d = end + 1;
  }
  return lines;
}

const nextFormatter = new Intl.DateTimeFormat("es-ES", {
  timeZone: "America/Havana",
  weekday: "long",
  hour: "2-digit",
  minute: "2-digit",
});

/** «el lunes a las 08:00» (hora de La Habana). */
export function formatNextOpening(iso: string | null): string | null {
  if (!iso) return null;
  const parts = nextFormatter.formatToParts(new Date(iso));
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? "";
  return `el ${get("weekday")} a las ${get("hour")}:${get("minute")}`;
}

/** Validación en cliente del editor de franjas (el backend vuelve a validar). */
export function slotError(slot: Slot): string | null {
  if (!/^\d{2}:\d{2}$/.test(slot.start) || !/^\d{2}:\d{2}$/.test(slot.end)) return "Indica la hora de inicio y de fin";
  if (slot.start >= slot.end) return "La hora de inicio debe ser anterior a la de fin";
  return null;
}
