import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type SubmitEvent, useMemo, useState } from "react";
import { DataTable } from "@/components/site/DataTable";
import { FormDialog } from "@/components/site/FormDialog";
import { PageHeader } from "@/components/site/PageHeader";
import { SearchBar } from "@/components/site/SearchBar";
import { Alert } from "@/components/ui/alert";
import { ConfirmDialog } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { CheckboxField, Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { formatDate } from "@/lib/format";
import { browserTransport } from "@/shared/api/browser";
import { getErrorMessage } from "@/shared/api/transport";
import { useDebouncedValue } from "@/shared/hooks/useDebouncedValue";
import { QueryProvider } from "@/shared/query/QueryProvider";
import type { News, NewsInput } from "../domain/types";
import { createNewsApi, type NewsApi } from "../infrastructure/news.api";

interface Props {
  initialItems: News[];
  api?: NewsApi;
}

export function NewsManager(props: Props) {
  return (
    <QueryProvider>
      <Manager {...props} />
    </QueryProvider>
  );
}

function Manager({ initialItems, api: injected }: Props) {
  const api = useMemo(() => injected ?? createNewsApi(browserTransport), [injected]);
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const term = useDebouncedValue(search.trim());
  const [editItem, setEditItem] = useState<News | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [toDelete, setToDelete] = useState<News | null>(null);
  const [formError, setFormError] = useState("");
  const [actionError, setActionError] = useState("");

  const { data: news = [], isLoading } = useQuery({
    queryKey: ["news-manage", term],
    queryFn: () => api.listAll(term || undefined),
    initialData: term ? undefined : initialItems,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["news-manage"] });

  const save = useMutation({
    mutationFn: ({ id, ...input }: NewsInput & { id?: string }) => (id ? api.update(id, input) : api.create(input)),
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

  const openForm = (item: News | null) => {
    setEditItem(item);
    setFormError("");
    setFormOpen(true);
  };

  const handleSubmit = (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    save.mutate({
      id: editItem?.id,
      title: String(form.get("title")),
      summary: String(form.get("summary") || ""),
      content: String(form.get("content")),
      is_published: form.get("is_published") === "on",
    });
  };

  return (
    <>
      <PageHeader
        title="Gestión de Noticias"
        subtitle="Administración de comunicados institucionales"
        action={<Button onClick={() => openForm(null)}>+ Nueva noticia</Button>}
      />
      <SearchBar value={search} onChange={setSearch} placeholder="Buscar noticias..." />
      {actionError && <Alert>{actionError}</Alert>}

      {isLoading ? (
        <p className="muted">Cargando...</p>
      ) : (
        <DataTable
          caption="Noticias"
          columns={["Título", "Resumen", "Publicada", "Fecha", "Acciones"]}
          isEmpty={news.length === 0}
          emptyMessage="No se encontraron noticias."
        >
          {news.map((item) => (
            <tr key={item.id}>
              <td>{item.title}</td>
              <td>{item.summary || "—"}</td>
              <td>{item.is_published ? "Sí" : "No"}</td>
              <td>{formatDate(item.created_at)}</td>
              <td>
                <div className="actions">
                  <Button variant="secondary" size="sm" onClick={() => openForm(item)}>
                    Editar
                  </Button>
                  <Button variant="danger" size="sm" onClick={() => setToDelete(item)}>
                    Eliminar
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </DataTable>
      )}

      <FormDialog
        open={formOpen}
        onOpenChange={(o) => {
          setFormOpen(o);
          if (!o) setEditItem(null);
        }}
        title={editItem ? "Editar noticia" : "Nueva noticia"}
        onSubmit={handleSubmit}
        loading={save.isPending}
        error={formError}
      >
        <Field label="Título">
          <Input name="title" defaultValue={editItem?.title ?? ""} required minLength={3} />
        </Field>
        <Field label="Resumen">
          <Input name="summary" defaultValue={editItem?.summary ?? ""} />
        </Field>
        <Field label="Contenido">
          <Textarea name="content" rows={6} defaultValue={editItem?.content ?? ""} required minLength={10} />
        </Field>
        <CheckboxField name="is_published" label="Publicada" defaultChecked={editItem?.is_published ?? true} />
      </FormDialog>

      <ConfirmDialog
        open={!!toDelete}
        onOpenChange={(o) => !o && setToDelete(null)}
        title="¿Eliminar la noticia?"
        description={`«${toDelete?.title ?? ""}» se eliminará de forma permanente.`}
        pending={remove.isPending}
        onConfirm={() => toDelete && remove.mutate(toDelete.id)}
      />
    </>
  );
}
