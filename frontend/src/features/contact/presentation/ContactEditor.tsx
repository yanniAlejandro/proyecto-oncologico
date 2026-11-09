import { type SubmitEvent, useMemo, useState } from "react";
import { PageHeader } from "@/components/site/PageHeader";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { browserTransport } from "@/shared/api/browser";
import { getErrorMessage } from "@/shared/api/transport";
import type { ContactInfo } from "../domain/types";
import { type ContactApi, createContactApi } from "../infrastructure/contact.api";

interface Props {
  initial: ContactInfo;
  api?: ContactApi;
}

export function ContactEditor({ initial, api: injected }: Props) {
  const api = useMemo(() => injected ?? createContactApi(browserTransport), [injected]);
  const [info, setInfo] = useState(initial);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const handleSubmit = async (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const value = (key: string) => String(form.get(key) ?? "").trim() || null;
    setSaving(true);
    setMsg(null);
    try {
      const saved = await api.update({
        organization_name: value("organization_name") ?? info.organization_name,
        address: value("address"),
        phone: value("phone"),
        email: value("email"),
        schedule: value("schedule"),
        map_url: value("map_url"),
      });
      setInfo(saved);
      setMsg({ ok: true, text: "Datos de contacto guardados." });
    } catch (err) {
      setMsg({ ok: false, text: getErrorMessage(err) });
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <PageHeader title="Contacto" subtitle="Datos institucionales que se muestran en la página de contacto" />
      <form onSubmit={handleSubmit} className="card grid max-w-3xl gap-4">
        {msg && (
          <p role="status" className={msg.ok ? "m-0 text-[0.88rem] text-[#1a7f4b]" : "m-0 text-[0.88rem] text-holh-danger"}>
            {msg.text}
          </p>
        )}
        <Field label="Nombre de la institución">
          <Input name="organization_name" defaultValue={info.organization_name} required minLength={3} />
        </Field>
        <Field label="Dirección">
          <Input name="address" defaultValue={info.address ?? ""} />
        </Field>
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Teléfono">
            <Input name="phone" defaultValue={info.phone ?? ""} />
          </Field>
          <Field label="Correo electrónico">
            <Input name="email" type="email" defaultValue={info.email ?? ""} />
          </Field>
        </div>
        <Field label="Horario de atención">
          <Textarea name="schedule" rows={2} defaultValue={info.schedule ?? ""} />
        </Field>
        <Field label="Enlace al mapa">
          <Input name="map_url" type="url" defaultValue={info.map_url ?? ""} />
        </Field>
        <div>
          <Button type="submit" disabled={saving}>
            {saving ? "Guardando..." : "Guardar"}
          </Button>
        </div>
      </form>
    </>
  );
}
