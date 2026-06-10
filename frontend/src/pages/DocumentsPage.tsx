import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import type { FormEvent } from 'react';
import { getErrorMessage } from '../api/client';
import { documentsApi } from '../api/resources';
import { FormModal } from '../components/FormModal';
import { SearchBar } from '../components/SearchBar';
import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../context/AuthContext';

export function DocumentsPage() {
  const { canManageContent } = useAuth();
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');
  const queryClient = useQueryClient();

  const { data: documents = [], isLoading } = useQuery({
    queryKey: ['documents', search],
    queryFn: () => documentsApi.list(search || undefined),
  });

  const createMutation = useMutation({
    mutationFn: documentsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setShowForm(false);
      setError('');
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: documentsApi.remove,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['documents'] }),
  });

  const handleCreate = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    createMutation.mutate({
      title: String(form.get('title')),
      description: String(form.get('description') || ''),
      file_name: String(form.get('file_name')),
      file_url: String(form.get('file_url')),
      file_type: String(form.get('file_type') || ''),
    });
  };

  return (
    <section className="page">
      <PageHeader
        title="Repositorio de Documentos"
        subtitle="Documentación clínica y recursos de referencia del hospital"
        action={
          canManageContent ? (
            <button className="btn btn-primary" onClick={() => setShowForm(true)}>
              + Nuevo documento
            </button>
          ) : undefined
        }
      />

      <SearchBar value={search} onChange={setSearch} placeholder="Buscar por título o descripción..." />

      {isLoading ? (
        <p className="muted">Cargando documentos...</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Título</th>
              <th>Descripción</th>
              <th>Archivo</th>
              <th>Fecha</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr key={doc.id}>
                <td>{doc.title}</td>
                <td>{doc.description || '—'}</td>
                <td>
                  <a href={doc.file_url} target="_blank" rel="noreferrer">
                    {doc.file_name}
                  </a>
                </td>
                <td>{new Date(doc.created_at).toLocaleDateString('es-ES')}</td>
                <td className="actions">
                  <a href={doc.file_url} target="_blank" rel="noreferrer" className="btn btn-sm btn-outline">
                    Ver
                  </a>
                  {canManageContent && (
                    <button className="btn btn-sm btn-danger" onClick={() => deleteMutation.mutate(doc.id)}>
                      Eliminar
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {documents.length === 0 && (
              <tr>
                <td colSpan={5} className="muted">
                  No se encontraron documentos.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      <FormModal
        isOpen={showForm}
        title="Nuevo documento"
        onClose={() => setShowForm(false)}
        onSubmit={handleCreate}
        loading={createMutation.isPending}
      >
        {error && <div className="alert alert-error">{error}</div>}
        <label>
          Título
          <input name="title" required />
        </label>
        <label>
          Descripción
          <textarea name="description" rows={2} />
        </label>
        <label>
          Nombre del archivo
          <input name="file_name" required />
        </label>
        <label>
          URL del archivo
          <input name="file_url" type="url" required />
        </label>
        <label>
          Tipo de archivo
          <input name="file_type" placeholder="PDF, DOCX..." />
        </label>
      </FormModal>
    </section>
  );
}
