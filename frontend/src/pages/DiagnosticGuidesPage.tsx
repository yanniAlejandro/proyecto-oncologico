import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import type { FormEvent } from 'react';
import { getErrorMessage } from '../api/client';
import { diseasesApi, guidesApi } from '../api/resources';
import { ContentModal } from '../components/ContentModal';
import { FormModal } from '../components/FormModal';
import { LoginModal } from '../components/LoginModal';
import { SearchBar } from '../components/SearchBar';
import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../context/AuthContext';
import type { DiagnosticGuide } from '../types';

export function DiagnosticGuidesPage() {
  const { user, canManageContent, canReadGuides } = useAuth();
  const [search, setSearch] = useState('');
  const [showLogin, setShowLogin] = useState(false);
  const [viewItem, setViewItem] = useState<DiagnosticGuide | null>(null);
  const [editItem, setEditItem] = useState<DiagnosticGuide | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');
  const queryClient = useQueryClient();

  const enabled = canReadGuides;

  const { data: guides = [], isLoading, isError } = useQuery({
    queryKey: ['diagnostic-guides', search],
    queryFn: () => guidesApi.list(search || undefined),
    enabled,
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
        return guidesApi.update(id, rest);
      }
      return guidesApi.create(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['diagnostic-guides'] });
      setShowForm(false);
      setEditItem(null);
      setError('');
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: guidesApi.remove,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['diagnostic-guides'] }),
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

  if (!user) {
    return (
      <section className="page">
        <PageHeader title="Guías de Diagnóstico" subtitle="Acceso restringido al personal autorizado" />
        <div className="access-notice">
          <p>Debes iniciar sesión como médico, encargado o administrador del Hospital Oncológico de La Habana.</p>
          <button className="btn btn-primary" onClick={() => setShowLogin(true)}>
            Iniciar sesión
          </button>
        </div>
        <LoginModal isOpen={showLogin} onClose={() => setShowLogin(false)} />
      </section>
    );
  }

  if (!canReadGuides) {
    return (
      <section className="page">
        <PageHeader title="Guías de Diagnóstico" />
        <p className="alert alert-error">Tu rol no tiene permisos para ver las guías de diagnóstico.</p>
      </section>
    );
  }

  return (
    <section className="page">
      <PageHeader
        title="Guías de Diagnóstico"
        subtitle="Protocolos y criterios diagnósticos por enfermedad"
        action={
          canManageContent ? (
            <button
              className="btn btn-primary"
              onClick={() => {
                setEditItem(null);
                setShowForm(true);
              }}
            >
              + Nueva guía
            </button>
          ) : undefined
        }
      />

      <SearchBar value={search} onChange={setSearch} placeholder="Buscar por título o enfermedad..." />

      {isLoading ? (
        <p className="muted">Cargando guías...</p>
      ) : isError ? (
        <p className="alert alert-error">Error al cargar las guías. Verifica tu sesión.</p>
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
            {guides.map((guide) => (
              <tr key={guide.id}>
                <td>
                  <span className="badge">{guide.disease_name}</span>
                </td>
                <td>{guide.title}</td>
                <td>{guide.author_name || '—'}</td>
                <td>{new Date(guide.updated_at).toLocaleDateString('es-ES')}</td>
                <td className="actions">
                  <button className="btn btn-sm btn-outline" onClick={() => setViewItem(guide)}>
                    Leer
                  </button>
                  {canManageContent && (
                    <>
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => {
                          setEditItem(guide);
                          setShowForm(true);
                        }}
                      >
                        Editar
                      </button>
                      <button className="btn btn-sm btn-danger" onClick={() => deleteMutation.mutate(guide.id)}>
                        Eliminar
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
            {guides.length === 0 && (
              <tr>
                <td colSpan={5} className="muted">
                  No se encontraron guías.
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
        title={editItem ? 'Editar guía' : 'Nueva guía de diagnóstico'}
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
