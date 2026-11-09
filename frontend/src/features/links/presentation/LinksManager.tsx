import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type SubmitEvent, useMemo, useState } from "react";
import { DataTable } from "@/components/site/DataTable";
import { FormDialog } from "@/components/site/FormDialog";
import { PageHeader } from "@/components/site/PageHeader";
import { Alert } from "@/components/ui/alert";
import { ConfirmDialog } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { CheckboxField, Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { isHttpUrl } from "@/features/publications/domain/types";
import { browserTransport } from "@/shared/api/browser";
import { getErrorMessage } from "@/shared/api/transport";
import { QueryProvider } from "@/shared/query/QueryProvider";
import type { InterestLink, LinkInput } from "../domain/types";
import { createLinksApi, type LinksApi } from "../infrastructure/links.api";

interface Props {
  initialItems: InterestLink[];
  api?: LinksApi;
}

export function LinksManager(props: Props) {
  return (
    <QueryProvider>
      <Manager {...props} />
    </QueryProvider>
  );
}

function Manager({ initialItems, api: injected }: Props) {
  const api = useMemo(() => injected ?? createLinksApi(browserTransport), [injected]);
  const queryClient = useQueryClient();
  const [editItem, setEditItem] = useState<InterestLink | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [toDelete, setToDelete] = useState<InterestLink | null>(null);
  const [formError, setFormError] = useState("");
  const [actionError, setActionError] = useState("");

  const { data: items = [] } = useQuery({ queryKey: ["links-manage"], queryFn: api.listAll, initialData: initialItems });
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["links-manage"] });

  const save = useMutation({
    mutationFn: (input: LinkInput) => (editItem ? api.update(editItem.id, input) : api.create(input)),
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

  const openForm = (item: InterestLink | null) => {
    setEditItem(item);
    setFormError("");
    setFormOpen(true);
  };

  const handleSubmit = (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const url = String(form.get("url")).trim();
    if (!isHttpUrl(url)) return setFormError("La URL debe empezar por http:// o https://");
    save.mutate({
      title: String(form.get("title")).trim(),
      url,
      description: String(form.get("description") ?? "").trim() || null,
      sort_order: Number(form.get("sort_order")) || 0,
      is_active: form.get("is_active") === "on",
    });
  };

  return (
    <>
      <PageHeader
        title="Enlaces de interés"
        subtitle="Recursos externos que aparecen en la sección pública de enlaces"
        action={<Button onClick={() => openForm(null)}>+ Nuevo enlace</Button>}
      />
      {actionError && <Alert>{actionError}</Alert>}
      <DataTable
        caption="Enlaces"
        columns={["Orden", "Título", "URL", "Visible", "Acciones"]}
        isEmpty={items.length === 0}
        emptyMessage="No hay enlaces."
      >
        {items.map((link) => (
          <tr key={link.id}>
            <td>{link.sort_order}</td>
            <td>{link.title}</td>
            <td>
              <a href={link.url} target="_blank" rel="noreferrer">
                {link.url}
              </a>
            </td>
            <td>{link.is_active ? "Sí" : "No"}</td>
            <td>
              <div className="actions">
                <Button variant="secondary" size="sm" onClick={() => openForm(link)}>
                  Editar
                </Button>
                <Button variant="danger" size="sm" onClick={() => setToDelete(link)}>
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
        title={editItem ? "Editar enlace" : "Nuevo enlace"}
        onSubmit={handleSubmit}
        loading={save.isPending}
        error={formError}
      >
        <Field label="Título">
          <Input name="title" defaultValue={editItem?.title ?? ""} required minLength={2} />
        </Field>
        <Field label="URL">
          <Input name="url" type="url" defaultValue={editItem?.url ?? ""} required />
        </Field>
        <Field label="Descripción">
          <Textarea name="description" rows={2} defaultValue={editItem?.description ?? ""} />
        </Field>
        <Field label="Orden">
          <Input name="sort_order" type="number" defaultValue={editItem?.sort_order ?? (items.length + 1) * 10} />
        </Field>
        <CheckboxField name="is_active" label="Visible en el portal" defaultChecked={editItem?.is_active ?? true} />
      </FormDialog>

      <ConfirmDialog
        open={!!toDelete}
        onOpenChange={(o) => !o && setToDelete(null)}
        title="¿Eliminar el enlace?"
        description={`«${toDelete?.title ?? ""}» se eliminará de forma permanente.`}
        pending={remove.isPending}
        onConfirm={() => toDelete && remove.mutate(toDelete.id)}
      />
    </>
  );
}
