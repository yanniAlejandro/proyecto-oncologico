import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import { type Slot, WEEKDAYS } from "../domain/types";

interface Props {
  slots: Slot[];
  onChange: (slots: Slot[]) => void;
  label: string;
}

const WORKDAYS = [0, 1, 2, 3, 4];

/** Lista editable de franjas (día + hora de inicio + hora de fin). */
export function SlotsEditor({ slots, onChange, label }: Props) {
  const set = (i: number, patch: Partial<Slot>) => onChange(slots.map((s, j) => (j === i ? { ...s, ...patch } : s)));
  const last = slots.at(-1);

  return (
    <fieldset className="grid gap-2 border-0 p-0">
      <legend className="mb-1 text-[0.88rem] font-semibold text-holh-text">{label}</legend>
      {slots.length === 0 && <p className="m-0 text-[0.85rem] text-holh-muted">Sin franjas: aparecerá «Fuera de horario».</p>}
      {slots.map((slot, i) => (
        <div key={i} className="grid grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)_minmax(0,1fr)_auto] items-center gap-2">
          <NativeSelect
            aria-label={`Día de la franja ${i + 1}`}
            value={slot.weekday}
            onChange={(e) => set(i, { weekday: Number(e.target.value) })}
          >
            {WEEKDAYS.map((day, d) => (
              <option key={day} value={d}>
                {day}
              </option>
            ))}
          </NativeSelect>
          <Input
            type="time"
            aria-label={`Inicio de la franja ${i + 1}`}
            value={slot.start}
            onChange={(e) => set(i, { start: e.target.value })}
            required
          />
          <Input
            type="time"
            aria-label={`Fin de la franja ${i + 1}`}
            value={slot.end}
            onChange={(e) => set(i, { end: e.target.value })}
            required
          />
          <Button
            variant="outline"
            size="sm"
            aria-label={`Quitar la franja ${i + 1}`}
            onClick={() => onChange(slots.filter((_, j) => j !== i))}
          >
            ✕
          </Button>
        </div>
      ))}
      <div className="flex flex-wrap gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() =>
            onChange([...slots, { weekday: last ? (last.weekday + 1) % 7 : 0, start: last?.start ?? "08:00", end: last?.end ?? "14:00" }])
          }
        >
          + Añadir franja
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() =>
            onChange([
              ...slots.filter((s) => !WORKDAYS.includes(s.weekday)),
              ...WORKDAYS.map((weekday) => ({ weekday, start: "08:00", end: "14:00" })),
            ])
          }
        >
          Lunes a viernes 08:00–14:00
        </Button>
      </div>
    </fieldset>
  );
}
