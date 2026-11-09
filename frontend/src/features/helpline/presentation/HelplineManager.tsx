import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type SubmitEvent, useEffect, useMemo, useState } from "react";
import { DataTable } from "@/components/site/DataTable";
import { FormDialog } from "@/components/site/FormDialog";
import { PageHeader } from "@/components/site/PageHeader";
import { Alert } from "@/components/ui/alert";
import { ConfirmDialog } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { CheckboxField, Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { browserTransport } from "@/shared/api/browser";
import { getErrorMessage } from "@/shared/api/transport";
import { QueryProvider } from "@/shared/query/QueryProvider";
import {
  type HelplineConfig,
  MIN_DAILY_HOURS,
  type Professional,
  type ProfessionalInput,
  type Slot,
  slotError,
  summarizeSlots,
  WEEKDAYS,
} from "../domain/types";
import { createHelplineApi, type HelplineApi } from "../infrastructure/helpline.api";
import { SlotsEditor } from "./SlotsEditor";

interface Props {
  initialConfig: HelplineConfig;
  initialProfessionals: Professional[];
  api?: HelplineApi;
}

export function HelplineManager(props: Props) {
  return (
    <QueryProvider>
      <Manager {...props} />
    </QueryProvider>
  );
}

const firstSlotError = (slots: Slot[]) => slots.map(slotError).find(Boolean) ?? null;

function Manager({ initialConfig, initialProfessionals, api: injected }: Props) {
  const api = useMemo(() => injected ?? createHelplineApi(browserTransport), [injected]);
  const queryClient = useQueryClient();

  // --- Teléfono del hospital ---
  const [config, setConfig] = useState(initialConfig);
  const [configSlots, setConfigSlots] = useState<Slot[]>(initialConfig.slots);
  const [configMsg, setConfigMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const saveConfig = useMutation({
    mutationFn: api.updateConfig,
    onSuccess: (saved) => {
      setConfig(saved);
      setConfigSlots(saved.slots);
      setConfigMsg({ ok: true, text: "Cambios guardados. La cabecera del portal se actualiza en menos de un minuto." });
    },
    onError: (err) => setConfigMsg({ ok: false, text: getErrorMessage(err) }),
  });

  const submitConfig = (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    setConfigMsg(null);
    const invalid = firstSlotError(configSlots);
    if (invalid) return setConfigMsg({ ok: false, text: invalid });
    const form = new FormData(e.currentTarget);
    saveConfig.mutate({
      phone: String(form.get("phone")),
      label: String(form.get("label")),
      off_hours_message: String(form.get("off_hours_message")),
      emergency_phone: String(form.get("emergency_phone") ?? ""),
      slots: configSlots,
    });
  };

  const shortDays = config.daily_hours
    .map((h, d) => (h < MIN_DAILY_HOURS ? `${WEEKDAYS[d]} (${h} h)` : null))
    .filter(Boolean);

  // --- Profesionales ---
  const { data: professionals = [] } = useQuery({
    queryKey: ["helpline-professionals"],
    queryFn: api.listProfessionals,
    initialData: initialProfessionals,
  });
  const [editItem, setEditItem] = useState<Professional | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [formError, setFormError] = useState("");
  const [toDelete, setToDelete] = useState<Professional | null>(null);
  const [proSlots, setProSlots] = useState<Slot[]>([]);
  const [actionError, setActionError] = useState("");

  useEffect(() => {
    if (formOpen) setProSlots(editItem?.slots ?? []);
  }, [formOpen, editItem]);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["helpline-professionals"] });

  const savePro = useMutation({
    mutationFn: (input: ProfessionalInput) =>
      editItem ? api.updateProfessional(editItem.id, input) : api.createProfessional(input),
    onSuccess: () => {
      invalidate();
      setFormOpen(false);
      setEditItem(null);
    },
    onError: (err) => setFormError(getErrorMessage(err)),
  });

  const removePro = useMutation({
    mutationFn: api.removeProfessional,
    onSuccess: () => {
      invalidate();
      setToDelete(null);
    },
    onError: (err) => {
      setActionError(getErrorMessage(err));
      setToDelete(null);
    },
  });

  const submitPro = (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    const invalid = firstSlotError(proSlots);
    if (invalid) return setFormError(invalid);
    const form = new FormData(e.currentTarget);
    savePro.mutate({
      full_name: String(form.get("full_name")),
      specialty: String(form.get("specialty")),
      phone: String(form.get("phone")),
      sort_order: Number(form.get("sort_order")) || 0,
      is_active: form.get("is_active") === "on",
      slots: proSlots,
    });
  };

  return (
    <>
      <PageHeader title="Gestión de la Línea de ayuda" subtitle="Teléfono del hospital y profesionales localizables" />

      <section className="card mb-8 grid gap-4" aria-labelledby="hl-config">
        <h3 id="hl-config">Teléfono del hospital</h3>
        {!config.meets_minimum && (
          <Alert>
            El horario no cubre las {MIN_DAILY_HOURS} horas diarias del estándar de atención
            {shortDays.length ? `: ${shortDays.join(", ")}` : ""}.
          </Alert>
        )}
        {configMsg && (
          <p role="status" className={configMsg.ok ? "m-0 text-[0.88rem] text-[#1a7f4b]" : "m-0 text-[0.88rem] text-holh-danger"}>
            {configMsg.text}
          </p>
        )}
        <form onSubmit={submitConfig} className="grid gap-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Field label="Teléfono">
              <Input name="phone" defaultValue={config.phone} required />
            </Field>
            <Field label="Teléfono de urgencias (fuera de horario)">
              <Input name="emergency_phone" defaultValue={config.emergency_phone ?? ""} />
            </Field>
          </div>
          <Field label="Descripción">
            <Input name="label" defaultValue={config.label} required />
          </Field>
          <Field label="Mensaje fuera de horario">
            <Textarea name="off_hours_message" rows={3} defaultValue={config.off_hours_message} required />
          </Field>
          <SlotsEditor label="Horario de atención" slots={configSlots} onChange={setConfigSlots} />
          <div>
            <Button type="submit" disabled={saveConfig.isPending}>
              {saveConfig.isPending ? "Guardando..." : "Guardar teléfono y horario"}
            </Button>
          </div>
        </form>
      </section>

      <div className="section-heading flex flex-wrap items-end justify-between gap-4">
        <div>
          <h3>Profesionales</h3>
          <p>Contactos que pacientes y familias pueden llamar directamente</p>
        </div>
        <Button
          onClick={() => {
            setEditItem(null);
            setFormError("");
            setFormOpen(true);
          }}
        >
          + Nuevo profesional
        </Button>
      </div>
      {actionError && <Alert>{actionError}</Alert>}
      <DataTable
        caption="Profesionales"
        columns={["Nombre", "Especialidad", "Teléfono", "Horario", "Visible", "Acciones"]}
        isEmpty={professionals.length === 0}
        emptyMessage="No hay profesionales."
      >
        {professionals.map((p) => (
          <tr key={p.id}>
            <td>{p.full_name}</td>
            <td>{p.specialty}</td>
            <td>{p.phone}</td>
            <td>{summarizeSlots(p.slots).join(" · ") || "—"}</td>
            <td>{p.is_active ? "Sí" : "No"}</td>
            <td>
              <div className="actions">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setEditItem(p);
                    setFormError("");
                    setFormOpen(true);
                  }}
                >
                  Editar
                </Button>
                <Button variant="danger" size="sm" onClick={() => setToDelete(p)}>
                  Eliminar
                </Button>
              </div>
            </td>
          </tr>
        ))}
      </DataTable>

      <FormDialog
        open={formOpen}
        onOpenChange={(o) => {
          setFormOpen(o);
          if (!o) setEditItem(null);
        }}
        title={editItem ? "Editar profesional" : "Nuevo profesional"}
        onSubmit={submitPro}
        loading={savePro.isPending}
        error={formError}
      >
        <Field label="Nombre">
          <Input name="full_name" defaultValue={editItem?.full_name ?? ""} required minLength={2} />
        </Field>
        <Field label="Especialidad o servicio">
          <Input name="specialty" defaultValue={editItem?.specialty ?? ""} required minLength={2} />
        </Field>
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Teléfono">
            <Input name="phone" type="tel" defaultValue={editItem?.phone ?? ""} required />
          </Field>
          <Field label="Orden">
            <Input name="sort_order" type="number" defaultValue={editItem?.sort_order ?? (professionals.length + 1) * 10} />
          </Field>
        </div>
        <SlotsEditor label="Franja horaria de atención" slots={proSlots} onChange={setProSlots} />
        <CheckboxField name="is_active" label="Visible en el portal" defaultChecked={editItem?.is_active ?? true} />
      </FormDialog>

      <ConfirmDialog
        open={!!toDelete}
        onOpenChange={(o) => !o && setToDelete(null)}
        title="¿Eliminar el profesional?"
        description={`«${toDelete?.full_name ?? ""}» dejará de aparecer en la línea de ayuda.`}
        pending={removePro.isPending}
        onConfirm={() => toDelete && removePro.mutate(toDelete.id)}
      />
    </>
  );
}
