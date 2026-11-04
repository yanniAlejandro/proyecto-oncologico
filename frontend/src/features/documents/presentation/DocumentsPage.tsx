import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, ExternalLink, Eye } from "lucide-react";
import { useMemo, useState } from "react";
import { DataTable } from "@/components/site/DataTable";
import { PageHeader } from "@/components/site/PageHeader";
import { SearchBar } from "@/components/site/SearchBar";
import { Alert } from "@/components/ui/alert";
import { ConfirmDialog } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { formatBytes, formatDate } from "@/lib/format";
import { browserTransport } from "@/shared/api/browser";
import { getErrorMessage } from "@/shared/api/transport";
import { useDebouncedValue } from "@/shared/hooks/useDebouncedValue";
import { QueryProvider } from "@/shared/query/QueryProvider";
import { type DocumentItem, documentFileUrl, type UploadPolicy } from "../domain/types";
import { createDocumentsApi, type DocumentsApi, type NewDocumentInput } from "../infrastructure/documents.api";
import { DocumentViewerDialog } from "./DocumentViewerDialog";
import { UploadDocumentDialog } from "./UploadDocumentDialog";

interface Props {
  initialItems: DocumentItem[];
  canManage: boolean;
  policy?: UploadPolicy;
  api?: DocumentsApi;
}

export function DocumentsPage(props: Props) {
  return (
    <QueryProvider>
      <Documents {...props} />
    </QueryProvider>
  );
}

function FileCell({ doc, onView }: { doc: DocumentItem; onView: (d: DocumentItem) => void }) {
  const meta = [doc.file_type, doc.has_file ? formatBytes(doc.size_bytes) : "enlace externo"].filter(Boolean).join(" · ");
  let link;
  if (!doc.has_file) {
    link = (
      <a href={doc.file_url ?? "#"} target="_blank" rel="noreferrer">
        {doc.file_name}
      </a>
    );
  } else if (doc.is_previewable) {
    link = (
      <button type="button" className="cursor-pointer text-left text-holh-blue hover:text-holh-teal" onClick={() => onView(doc)}>
        {doc.file_name}
      </button>
    );
  } else {
    link = (
      <a href={documentFileUrl(doc, "attachment")} download={doc.file_name}>
        {doc.file_name}
      </a>
    );
  }
  return (
    <>
      {link}
      <span className="block text-[0.78rem] text-holh-muted">{meta}</span>
    </>
  );
}

function Documents({ initialItems, canManage, policy, api: injected }: Props) {
  const api = useMemo(() => injected ?? createDocumentsApi(browserTransport), [injected]);
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const term = useDebouncedValue(search.trim());
  const [viewing, setViewing] = useState<DocumentItem | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [toDelete, setToDelete] = useState<DocumentItem | null>(null);
  const [actionError, setActionError] = useState("");

  const { data: documents = [], isLoading } = useQuery({
    queryKey: ["documents", term],
    queryFn: () => api.list(term || undefined),
    initialData: term ? undefined : initialItems,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["documents"] });

  const create = useMutation({
    mutationFn: (input: NewDocumentInput) => api.create(input),
    onSuccess: () => {
      invalidate();
      setUploadOpen(false);
    },
    onError: (err) => setUploadError(getErrorMessage(err)),
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

  return (
    <>
      <PageHeader
        title="Repositorio de Documentos"
        subtitle="Documentación clínica y recursos de referencia del hospital"
        action={
          canManage ? (
            <Button
              onClick={() => {
                setUploadError("");
                setUploadOpen(true);
              }}
            >
              + Nuevo documento
            </Button>
          ) : undefined
        }
      />

      <SearchBar value={search} onChange={setSearch} placeholder="Buscar por título o descripción..." />
      {actionError && <Alert>{actionError}</Alert>}

      {isLoading ? (
        <p className="muted">Cargando documentos...</p>
      ) : (
        <DataTable
          caption="Documentos"
          columns={["Título", "Descripción", "Archivo", "Fecha", "Acciones"]}
          isEmpty={documents.length === 0}
          emptyMessage="No se encontraron documentos."
        >
          {documents.map((doc) => (
            <tr key={doc.id}>
              <td>{doc.title}</td>
              <td>{doc.description || "—"}</td>
              <td>
                <FileCell doc={doc} onView={setViewing} />
              </td>
              <td>{formatDate(doc.created_at)}</td>
              <td>
                <div className="actions">
                  {doc.has_file && doc.is_previewable && (
                    <Button variant="outline" size="sm" onClick={() => setViewing(doc)} aria-label={`Ver ${doc.title}`}>
                      <Eye aria-hidden="true" /> Ver
                    </Button>
                  )}
                  {!doc.has_file && doc.file_url && (
                    <Button asChild variant="outline" size="sm">
                      <a href={doc.file_url} target="_blank" rel="noreferrer" aria-label={`Abrir ${doc.title} (enlace externo)`}>
                        <ExternalLink aria-hidden="true" /> Ver
                      </a>
                    </Button>
                  )}
                  {doc.has_file && (
                    <Button asChild variant="secondary" size="sm" className="px-2">
                      <a
                        href={documentFileUrl(doc, "attachment")}
                        download={doc.file_name}
                        aria-label={`Descargar ${doc.file_name}`}
                        title="Descargar"
                      >
                        <Download aria-hidden="true" />
                      </a>
                    </Button>
                  )}
                  {canManage && (
                    <Button variant="danger" size="sm" onClick={() => setToDelete(doc)}>
                      Eliminar
                    </Button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </DataTable>
      )}

      <DocumentViewerDialog doc={viewing} onOpenChange={(o) => !o && setViewing(null)} />

      {canManage && (
        <UploadDocumentDialog
          open={uploadOpen}
          onOpenChange={setUploadOpen}
          policy={policy}
          loading={create.isPending}
          error={uploadError}
          onSubmit={(input) => {
            setUploadError("");
            create.mutate(input);
          }}
        />
      )}

      <ConfirmDialog
        open={!!toDelete}
        onOpenChange={(o) => !o && setToDelete(null)}
        title="¿Eliminar el documento?"
        description={`«${toDelete?.title ?? ""}» y su archivo se eliminarán de forma permanente.`}
        pending={remove.isPending}
        onConfirm={() => toDelete && remove.mutate(toDelete.id)}
      />
    </>
  );
}
