import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type SubmitEvent, useMemo, useState } from "react";
import { DataTable } from "@/components/site/DataTable";
import { FormDialog } from "@/components/site/FormDialog";
import { PageHeader } from "@/components/site/PageHeader";
import { SearchBar } from "@/components/site/SearchBar";
import { Alert } from "@/components/ui/alert";
import { ConfirmDialog } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { browserTransport } from "@/shared/api/browser";
import { getErrorMessage } from "@/shared/api/transport";
import { useDebouncedValue } from "@/shared/hooks/useDebouncedValue";
import { QueryProvider } from "@/shared/query/QueryProvider";
import type { Disease, DiseaseInput } from "../domain/types";
import { createDiseasesApi, type DiseasesApi } from "../infrastructure/diseases.api";

interface Props {
  initialItems: Disease[];
  api?: DiseasesApi;
}

export function DiseasesManager(props: Props) {
  return (
    <QueryProvider>
      <Manager {...props} />
    </QueryProvider>
  );
}

function Manager({ initialItems, api: injected }: Props) {
  const api = useMemo(() => injected ?? createDiseasesApi(browserTransport), [injected]);
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const term = useDebouncedValue(search.trim());
  const [editItem, setEditItem] = useState<Disease | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [toDelete, setToDelete] = useState<Disease | null>(null);
  const [formError, setFormError] = useState("");
  const [actionError, setActionError] = useState("");

  const { data: items = [] } = useQuery({
    queryKey: ["diseases", term],
    queryFn: () => api.list(term || undefined),
    initialData: term ? undefined : initialItems,
  });
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["diseases"] });

  const save = useMutation({
    mutationFn: (input: DiseaseInput) => (editItem ? api.update(editItem.id, input) : api.create(input)),
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

  const openForm = (item: Disease | null) => {
    setEditItem(item);
    setFormError("");
    setFormOpen(true);
  };

  const handleSubmit = (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    save.mutate({ name: String(form.get("name")), description: String(form.get("description") ?? "") });
  };

  return (
    <>
      <PageHeader
        title="Enfermedades"
        subtitle="Catálogo que clasifica las guías y los protocolos"
        action={<Button onClick={() => openForm(null)}>+ Nueva enfermedad</Button>}
      />
      <SearchBar value={search} onChange={setSearch} placeholder="Buscar enfermedades..." />
      {actionError && <Alert>{actionError}</Alert>}
      <DataTable
        caption="Enfermedades"
        columns={["Nombre", "Descripción", "Acciones"]}
        isEmpty={items.length === 0}
        emptyMessage="No hay enfermedades."
      >
        {items.map((d) => (
          <tr key={d.id}>
            <td>{d.name}</td>
            <td>{d.description || "—"}</td>
            <td>
              <div className="actions">
                <Button variant="secondary" size="sm" onClick={() => openForm(d)}>
                  Editar
                </Button>
                <Button variant="danger" size="sm" onClick={() => setToDelete(d)}>
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
        title={editItem ? "Editar enfermedad" : "Nueva enfermedad"}
        onSubmit={handleSubmit}
        loading={save.isPending}
        error={formError}
      >
        <Field label="Nombre">
          <Input name="name" defaultValue={editItem?.name ?? ""} required minLength={2} />
        </Field>
        <Field label="Descripción">
          <Textarea name="description" rows={3} defaultValue={editItem?.description ?? ""} />
        </Field>
      </FormDialog>

      <ConfirmDialog
        open={!!toDelete}
        onOpenChange={(o) => !o && setToDelete(null)}
        title="¿Eliminar la enfermedad?"
        description={`«${toDelete?.name ?? ""}» se eliminará. No es posible si alguna guía o protocolo la usa.`}
        pending={remove.isPending}
        onConfirm={() => toDelete && remove.mutate(toDelete.id)}
      />
    </>
  );
}
