import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import type { FormEvent } from 'react';
import { getErrorMessage } from '../api/client';
import { diseasesApi, protocolsApi } from '../api/resources';
import { ContentModal } from '../components/ContentModal';
import { FormModal } from '../components/FormModal';
import { SearchBar } from '../components/SearchBar';
import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../context/AuthContext';
import type { TreatmentProtocol } from '../types';

export function TreatmentProtocolsPage() {
  const { canManageContent } = useAuth();
  const [search, setSearch] = useState('');
  const [viewItem, setViewItem] = useState<TreatmentProtocol | null>(null);
  const [editItem, setEditItem] = useState<TreatmentProtocol | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');
  const queryClient = useQueryClient();

  const { data: protocols = [], isLoading } = useQuery({
    queryKey: ['treatment-protocols', search],
    queryFn: () => protocolsApi.list(search || undefined),
  });

  const { data: diseases = [] } = useQuery({
    queryKey: ['diseases'],
    queryFn: () => diseasesApi.list(),
    enabled: canManageContent,
  });

  const saveMutation = useMutation({
    mutationFn: async (payload: { disease_id: string; title: string; content: string; id?: string }) => {
      if (payload.id) {
        const { id, ...rest } = payload;
        return protocolsApi.update(id, rest);
      }
      return protocolsApi.create(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['treatment-protocols'] });
      setShowForm(false);
      setEditItem(null);
      setError('');
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: protocolsApi.remove,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['treatment-protocols'] }),
  });

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    saveMutation.mutate({
      id: editItem?.id,
      disease_id: String(form.get('disease_id')),
      title: String(form.get('title')),
      content: String(form.get('content')),
    });
  };

  return (
    <section className="page">
      <PageHeader
        title="Protocolos de Tratamiento"
        subtitle="Protocolos terapéuticos institucionales — acceso público"
        action={
          canManageContent ? (
            <button
              className="btn btn-primary"
              onClick={() => {
                setEditItem(null);
                setShowForm(true);
              }}
            >
              + Nuevo protocolo
            </button>
          ) : undefined
        }
      />

      <SearchBar value={search} onChange={setSearch} placeholder="Buscar por título o enfermedad..." />

      {isLoading ? (
        <p className="muted">Cargando protocolos...</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Enfermedad</th>
              <th>Título</th>
              <th>Autor</th>
              <th>Actualizado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {protocols.map((protocol) => (
              <tr key={protocol.id}>
                <td>
                  <span className="badge">{protocol.disease_name}</span>
                </td>
                <td>{protocol.title}</td>
                <td>{protocol.author_name || '—'}</td>
                <td>{new Date(protocol.updated_at).toLocaleDateString('es-ES')}</td>
                <td className="actions">
                  <button className="btn btn-sm btn-outline" onClick={() => setViewItem(protocol)}>
                    Leer
                  </button>
                  {canManageContent && (
                    <>
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => {
                          setEditItem(protocol);
                          setShowForm(true);
                        }}
                      >
                        Editar
                      </button>
                      <button className="btn btn-sm btn-danger" onClick={() => deleteMutation.mutate(protocol.id)}>
                        Eliminar
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
            {protocols.length === 0 && (
              <tr>
                <td colSpan={5} className="muted">
                  No se encontraron protocolos.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      <ContentModal
        isOpen={!!viewItem}
        title={viewItem?.title || ''}
        content={viewItem?.content || ''}
        onClose={() => setViewItem(null)}
      />

      <FormModal
        isOpen={showForm}
        title={editItem ? 'Editar protocolo' : 'Nuevo protocolo de tratamiento'}
        onClose={() => {
          setShowForm(false);
          setEditItem(null);
        }}
        onSubmit={handleSubmit}
        loading={saveMutation.isPending}
      >
        {error && <div className="alert alert-error">{error}</div>}
        <label>
          Enfermedad
          <select name="disease_id" defaultValue={editItem?.disease_id || ''} required>
            <option value="">Seleccionar...</option>
            {diseases.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Título
          <input name="title" defaultValue={editItem?.title || ''} required />
        </label>
        <label>
          Contenido
          <textarea name="content" rows={8} defaultValue={editItem?.content || ''} required />
        </label>
      </FormModal>
    </section>
  );
}
