import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { DataTable } from "@/components/site/DataTable";
import { PageHeader } from "@/components/site/PageHeader";
import { SearchBar } from "@/components/site/SearchBar";
import { Alert } from "@/components/ui/alert";
import { ConfirmDialog } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/format";
import { browserTransport } from "@/shared/api/browser";
import { getErrorMessage } from "@/shared/api/transport";
import { useDebouncedValue } from "@/shared/hooks/useDebouncedValue";
import { QueryProvider } from "@/shared/query/QueryProvider";
import type { Publication, PublicationInput } from "../domain/types";
import { createPublicationsApi, type PublicationsApi } from "../infrastructure/publications.api";
import { PublicationFormDialog } from "./PublicationFormDialog";

interface Props {
  initialItems: Publication[];
  api?: PublicationsApi;
}

export function PublicationsManager(props: Props) {
  return (
    <QueryProvider>
      <Manager {...props} />
    </QueryProvider>
  );
}

function Manager({ initialItems, api: injected }: Props) {
  const api = useMemo(() => injected ?? createPublicationsApi(browserTransport), [injected]);
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const term = useDebouncedValue(search.trim());
  const [editItem, setEditItem] = useState<Publication | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [toDelete, setToDelete] = useState<Publication | null>(null);
  const [formError, setFormError] = useState("");
  const [actionError, setActionError] = useState("");

  const { data: items = [], isLoading } = useQuery({
    queryKey: ["publications", term],
    queryFn: () => api.list(term || undefined),
    initialData: term ? undefined : initialItems,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["publications"] });

  const save = useMutation({
    mutationFn: (input: PublicationInput) => (editItem ? api.update(editItem.id, input) : api.create(input)),
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

  const openForm = (item: Publication | null) => {
    setEditItem(item);
    setFormError("");
    setFormOpen(true);
  };

  return (
    <>
      <PageHeader
        title="Gestión de Publicaciones"
        subtitle="Pega un enlace: el título y la imagen se completan solos"
        action={<Button onClick={() => openForm(null)}>+ Nueva publicación</Button>}
      />
      <SearchBar value={search} onChange={setSearch} placeholder="Buscar publicaciones..." />
      {actionError && <Alert>{actionError}</Alert>}

      {isLoading ? (
        <p className="muted">Cargando...</p>
      ) : (
        <DataTable
          caption="Publicaciones"
          columns={["Imagen", "Título", "Enlace", "Autor", "Fecha", "Acciones"]}
          isEmpty={items.length === 0}
          emptyMessage="No hay publicaciones."
        >
          {items.map((item) => (
            <tr key={item.id}>
              <td>
                {item.image_url ? (
                  <img src={item.image_url} alt="" className="publication-thumb" loading="lazy" />
                ) : (
                  <span className="muted">—</span>
                )}
              </td>
              <td>{item.title}</td>
              <td>
                <a href={item.url} target="_blank" rel="noreferrer">
                  {item.domain}
                </a>
              </td>
              <td>{item.author_name ?? "—"}</td>
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

      <PublicationFormDialog
        open={formOpen}
        onOpenChange={(o) => {
          setFormOpen(o);
          if (!o) setEditItem(null);
        }}
        item={editItem}
        api={api}
        onSubmit={(input) => save.mutate(input)}
        saving={save.isPending}
        error={formError}
      />

      <ConfirmDialog
        open={!!toDelete}
        onOpenChange={(o) => !o && setToDelete(null)}
        title="¿Eliminar la publicación?"
        description={`«${toDelete?.title ?? ""}» y su imagen se eliminarán de forma permanente.`}
        pending={remove.isPending}
        onConfirm={() => toDelete && remove.mutate(toDelete.id)}
      />
    </>
  );
}
