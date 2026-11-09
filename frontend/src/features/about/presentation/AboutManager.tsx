import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type SubmitEvent, useEffect, useMemo, useState } from "react";
import { DataTable } from "@/components/site/DataTable";
import { FormDialog } from "@/components/site/FormDialog";
import { PageHeader } from "@/components/site/PageHeader";
import { RichText } from "@/components/site/RichText";
import { Alert } from "@/components/ui/alert";
import { ConfirmDialog } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { IMAGE_TYPES, validateImageFile } from "@/features/publications/domain/types";
import { browserTransport } from "@/shared/api/browser";
import { getErrorMessage } from "@/shared/api/transport";
import { QueryProvider } from "@/shared/query/QueryProvider";
import type { AboutSection, AboutSectionInput } from "../domain/types";
import { type AboutApi, createAboutApi } from "../infrastructure/about.api";

interface Props {
  initialItems: AboutSection[];
  api?: AboutApi;
}

export function AboutManager(props: Props) {
  return (
    <QueryProvider>
      <Manager {...props} />
    </QueryProvider>
  );
}

type ImageMode = "keep" | "upload" | "none";

function Manager({ initialItems, api: injected }: Props) {
  const api = useMemo(() => injected ?? createAboutApi(browserTransport), [injected]);
  const queryClient = useQueryClient();
  const [editItem, setEditItem] = useState<AboutSection | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [toDelete, setToDelete] = useState<AboutSection | null>(null);
  const [formError, setFormError] = useState("");
  const [actionError, setActionError] = useState("");
  const [body, setBody] = useState("");
  const [showPreview, setShowPreview] = useState(false);
  const [imageMode, setImageMode] = useState<ImageMode>("none");

  const { data: sections = [] } = useQuery({ queryKey: ["about"], queryFn: api.list, initialData: initialItems });
  const nextOrder = (sections.at(-1)?.sort_order ?? 0) + 10;

  useEffect(() => {
    if (!formOpen) return;
    setBody(editItem?.body ?? "");
    setShowPreview(false);
    setImageMode(editItem?.image_url ? "keep" : "none");
  }, [formOpen, editItem]);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["about"] });

  const save = useMutation({
    mutationFn: (input: AboutSectionInput) => (editItem ? api.update(editItem.id, input) : api.create(input)),
    onSuccess: () => {
      invalidate();
      setFormOpen(false);
      setEditItem(null);
    },
    onError: (err) => setFormError(getErrorMessage(err)),
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.remove(id),
    onSuccess: () => {
      invalidate();
      setToDelete(null);
    },
    onError: (err) => {
      setActionError(getErrorMessage(err));
      setToDelete(null);
    },
  });

  const move = useMutation({
    mutationFn: async ({ a, b }: { a: AboutSection; b: AboutSection }) => {
      const keep = { kind: "keep" } as const;
      await api.update(a.id, { title: a.title, body: a.body, sort_order: b.sort_order, image: keep });
      await api.update(b.id, { title: b.title, body: b.body, sort_order: a.sort_order, image: keep });
    },
    onSettled: invalidate,
    onError: (err) => setActionError(getErrorMessage(err)),
  });

  const openForm = (item: AboutSection | null) => {
    setEditItem(item);
    setFormError("");
    setFormOpen(true);
  };

  const handleSubmit = (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const file = form.get("image");
    let image: AboutSectionInput["image"] = { kind: imageMode === "keep" ? "keep" : "none" };
    if (imageMode === "upload") {
      if (!(file instanceof File) || !file.size) return setFormError("Selecciona una foto o elige otra opción");
      const invalid = validateImageFile(file);
      if (invalid) return setFormError(invalid);
      image = { kind: "upload", file };
    }
    save.mutate({
      title: String(form.get("title")),
      body,
      sort_order: Number(form.get("sort_order")) || nextOrder,
      image,
    });
  };

  return (
    <>
      <PageHeader
        title="Gestión de «Quiénes somos»"
        subtitle="Apartados de la portada del portal, en el orden en que se muestran"
        action={<Button onClick={() => openForm(null)}>+ Nuevo apartado</Button>}
      />
      {actionError && <Alert>{actionError}</Alert>}

      <DataTable
        caption="Apartados"
        columns={["Orden", "Título", "Foto", "Acciones"]}
        isEmpty={sections.length === 0}
        emptyMessage="No hay apartados."
      >
        {sections.map((s, i) => (
          <tr key={s.id}>
            <td>
              <div className="actions">
                <Button
                  variant="outline"
                  size="sm"
                  aria-label={`Subir «${s.title}»`}
                  disabled={i === 0 || move.isPending}
                  onClick={() => move.mutate({ a: s, b: sections[i - 1] })}
                >
                  ↑
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  aria-label={`Bajar «${s.title}»`}
                  disabled={i === sections.length - 1 || move.isPending}
                  onClick={() => move.mutate({ a: s, b: sections[i + 1] })}
                >
                  ↓
                </Button>
              </div>
            </td>
            <td>
              <a href={`/#${s.slug}`}>{s.title}</a>
            </td>
            <td>{s.image_url ? <img src={s.image_url} alt="" className="publication-thumb" /> : "—"}</td>
            <td>
              <div className="actions">
                <Button variant="secondary" size="sm" onClick={() => openForm(s)}>
                  Editar
                </Button>
                <Button variant="danger" size="sm" onClick={() => setToDelete(s)}>
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
        title={editItem ? "Editar apartado" : "Nuevo apartado"}
        onSubmit={handleSubmit}
        loading={save.isPending}
        error={formError}
      >
        <Field label="Título">
          <Input name="title" defaultValue={editItem?.title ?? ""} required minLength={3} maxLength={255} />
        </Field>
        <Field label="Orden">
          <Input name="sort_order" type="number" defaultValue={editItem?.sort_order ?? nextOrder} step={10} />
        </Field>
        <div className="grid gap-[0.35rem]">
          <div className="flex items-center justify-between">
            <label htmlFor="about-body" className="text-[0.88rem] font-semibold text-holh-text">
              Texto
            </label>
            <Button variant="outline" size="sm" onClick={() => setShowPreview((v) => !v)}>
              {showPreview ? "Editar texto" : "Ver cómo queda"}
            </Button>
          </div>
          {showPreview ? (
            <div className="rich-text-preview">
              <RichText text={body} />
            </div>
          ) : (
            <Textarea id="about-body" rows={12} value={body} onChange={(e) => setBody(e.target.value)} required />
          )}
          <p className="m-0 text-[0.78rem] text-holh-muted">
            Línea en blanco = nuevo párrafo · «- » lista · «### » subtítulo · «**texto**» negrita · «&gt; » nota
          </p>
        </div>
        <fieldset className="grid gap-2 border-0 p-0">
          <legend className="mb-1 text-[0.88rem] font-semibold text-holh-text">Foto (opcional)</legend>
          {(
            [
              ["keep", "Mantener la foto actual", !!editItem?.image_url],
              ["upload", editItem?.image_url ? "Cambiar la foto" : "Subir una foto", true],
              ["none", "Sin foto", true],
            ] as const
          )
            .filter(([, , show]) => show)
            .map(([value, label]) => (
              <label key={value} className="flex items-center gap-2 text-[0.88rem] text-holh-text">
                <input
                  type="radio"
                  name="image_mode"
                  checked={imageMode === value}
                  onChange={() => setImageMode(value)}
                  className="accent-holh-teal"
                />
                {label}
              </label>
            ))}
          {imageMode === "upload" && (
            <Input name="image" type="file" aria-label="Archivo de la foto" accept={IMAGE_TYPES.join(",")} />
          )}
        </fieldset>
      </FormDialog>

      <ConfirmDialog
        open={!!toDelete}
        onOpenChange={(o) => !o && setToDelete(null)}
        title="¿Eliminar el apartado?"
        description={`«${toDelete?.title ?? ""}» desaparecerá de la portada.`}
        pending={remove.isPending}
        onConfirm={() => toDelete && remove.mutate(toDelete.id)}
      />
    </>
  );
}
