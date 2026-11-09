import { formatNextOpening, slotError, summarizeSlots, telHref } from "./types";

const week = (start: string, end: string, days: number[]) => days.map((weekday) => ({ weekday, start, end }));

describe("línea de ayuda: reglas puras", () => {
  it("agrupa días consecutivos con el mismo horario", () => {
    const slots = [...week("08:00", "16:00", [0, 1, 2, 3, 4]), ...week("09:00", "15:00", [5, 6])];
    expect(summarizeSlots(slots)).toEqual(["Lunes a viernes: 08:00–16:00", "Sábado y domingo: 09:00–15:00"]);
  });

  it("varias franjas en un día y días sueltos", () => {
    const slots = [
      { weekday: 2, start: "14:00", end: "16:00" },
      { weekday: 2, start: "08:00", end: "12:00" },
      { weekday: 4, start: "08:00", end: "12:00" },
    ];
    expect(summarizeSlots(slots)).toEqual(["Miércoles: 08:00–12:00, 14:00–16:00", "Viernes: 08:00–12:00"]);
    expect(summarizeSlots([])).toEqual([]);
  });

  it("enlace tel: limpio", () => {
    expect(telHref("+53 (7) 649-0000")).toBe("tel:+5376490000");
  });

  it("próxima apertura en hora de La Habana", () => {
    // 16 nov 2026 13:00 UTC = lunes 08:00 en La Habana (UTC-5)
    expect(formatNextOpening("2026-11-16T13:00:00Z")).toBe("el lunes a las 08:00");
    expect(formatNextOpening(null)).toBeNull();
  });

  it("valida las franjas", () => {
    expect(slotError({ weekday: 0, start: "16:00", end: "08:00" })).toMatch(/anterior/);
    expect(slotError({ weekday: 0, start: "", end: "08:00" })).toMatch(/Indica/);
    expect(slotError({ weekday: 0, start: "08:00", end: "16:00" })).toBeNull();
  });
});
