import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type SubmitEvent, useMemo, useState } from "react";
import { ContentDialog } from "@/components/site/ContentDialog";
import { DataTable } from "@/components/site/DataTable";
import { FormDialog } from "@/components/site/FormDialog";
import { PageHeader } from "@/components/site/PageHeader";
import { SearchBar } from "@/components/site/SearchBar";
import { Alert } from "@/components/ui/alert";
import { ConfirmDialog } from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import { Textarea } from "@/components/ui/textarea";
import type { Disease } from "@/features/diseases/domain/types";
import { formatDate } from "@/lib/format";
import { browserTransport } from "@/shared/api/browser";
import { getErrorMessage } from "@/shared/api/transport";
import { useDebouncedValue } from "@/shared/hooks/useDebouncedValue";
import { QueryProvider } from "@/shared/query/QueryProvider";
import { CLINICAL_COPY, type ClinicalDoc, type ClinicalKind } from "../domain/types";
import { type ClinicalApi, createClinicalApi } from "../infrastructure/clinical.api";

interface Props {
  kind: ClinicalKind;
  initialItems: ClinicalDoc[];
  diseases: Disease[];
  canManage: boolean;
  api?: ClinicalApi;
}

export function ClinicalDocsPage(props: Props) {
  return (
    <QueryProvider>
      <ClinicalDocs {...props} />
    </QueryProvider>
  );
}

function ClinicalDocs({ kind, initialItems, diseases, canManage, api: injected }: Props) {
  const copy = CLINICAL_COPY[kind];
  const api = useMemo(() => injected ?? createClinicalApi(browserTransport, kind), [injected, kind]);
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const term = useDebouncedValue(search.trim());
  const [viewItem, setViewItem] = useState<ClinicalDoc | null>(null);
  const [editItem, setEditItem] = useState<ClinicalDoc | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [toDelete, setToDelete] = useState<ClinicalDoc | null>(null);
  const [formError, setFormError] = useState("");
  const [actionError, setActionError] = useState("");

  const { data: items = [], isLoading, isError } = useQuery({
    queryKey: [copy.queryKey, term],
    queryFn: () => api.list(term || undefined),
    initialData: term ? undefined : initialItems,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: [copy.queryKey] });

  const save = useMutation({
    mutationFn: (input: { id?: string; disease_id: string; title: string; content: string }) => {
      const { id, ...rest } = input;
      return id ? api.update(id, rest) : api.create(rest);
    },
    onSuccess: () => {
      invalidate();
      closeForm();
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

  const openForm = (item: ClinicalDoc | null) => {
    setEditItem(item);
    setFormError("");
    setFormOpen(true);
  };
  const closeForm = () => {
    setFormOpen(false);
    setEditItem(null);
  };

  const handleSubmit = (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    save.mutate({
      id: editItem?.id,
      disease_id: String(form.get("disease_id")),
      title: String(form.get("title")),
      content: String(form.get("content")),
    });
  };

  return (
    <>
      <PageHeader
        title={copy.title}
        subtitle={copy.subtitle}
        action={canManage ? <Button onClick={() => openForm(null)}>{copy.newLabel}</Button> : undefined}
      />

      <SearchBar value={search} onChange={setSearch} placeholder="Buscar por título o enfermedad..." />

      {actionError && <Alert>{actionError}</Alert>}

      {isLoading ? (
        <p className="muted">{copy.loading}</p>
      ) : isError ? (
        <Alert>{copy.loadError}</Alert>
      ) : (
        <DataTable
          caption={copy.title}
          columns={["Enfermedad", "Título", "Autor", "Actualizado", "Acciones"]}
          isEmpty={items.length === 0}
          emptyMessage={copy.empty}
        >
          {items.map((item) => (
            <tr key={item.id}>
              <td>
                <Badge>{item.disease_name}</Badge>
              </td>
              <td>{item.title}</td>
              <td>{item.author_name || "—"}</td>
              <td>{formatDate(item.updated_at)}</td>
              <td>
                <div className="actions">
                  <Button variant="outline" size="sm" onClick={() => setViewItem(item)}>
                    Leer
                  </Button>
                  {canManage && (
                    <>
                      <Button variant="secondary" size="sm" onClick={() => openForm(item)}>
                        Editar
                      </Button>
                      <Button variant="danger" size="sm" onClick={() => setToDelete(item)}>
                        Eliminar
                      </Button>
                    </>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </DataTable>
      )}

      <ContentDialog
        open={!!viewItem}
        onOpenChange={(o) => !o && setViewItem(null)}
        title={viewItem?.title ?? ""}
        content={viewItem?.content ?? ""}
      />

      <FormDialog
        open={formOpen}
        onOpenChange={(o) => (o ? setFormOpen(true) : closeForm())}
        title={editItem ? copy.editTitle : copy.createTitle}
        onSubmit={handleSubmit}
        loading={save.isPending}
        error={formError}
      >
        <Field label="Enfermedad">
          <NativeSelect name="disease_id" defaultValue={editItem?.disease_id ?? ""} required>
            <option value="">Seleccionar...</option>
            {diseases.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </NativeSelect>
        </Field>
        <Field label="Título">
          <Input name="title" defaultValue={editItem?.title ?? ""} required minLength={3} />
        </Field>
        <Field label="Contenido">
          <Textarea name="content" rows={8} defaultValue={editItem?.content ?? ""} required minLength={10} />
        </Field>
      </FormDialog>

      <ConfirmDialog
        open={!!toDelete}
        onOpenChange={(o) => !o && setToDelete(null)}
        title={`¿Eliminar ${copy.noun}?`}
        description={`«${toDelete?.title ?? ""}» se eliminará de forma permanente.`}
        pending={remove.isPending}
        onConfirm={() => toDelete && remove.mutate(toDelete.id)}
      />
    </>
  );
}
