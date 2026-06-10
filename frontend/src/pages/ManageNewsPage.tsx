import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import type { FormEvent } from 'react';
import { Navigate } from 'react-router-dom';
import { getErrorMessage } from '../api/client';
import { newsApi } from '../api/resources';
import { FormModal } from '../components/FormModal';
import { SearchBar } from '../components/SearchBar';
import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../context/AuthContext';
import type { News } from '../types';

export function ManageNewsPage() {
  const { canManageContent } = useAuth();
  const [search, setSearch] = useState('');
  const [editItem, setEditItem] = useState<News | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');
  const queryClient = useQueryClient();

  const { data: news = [], isLoading } = useQuery({
    queryKey: ['news-manage', search],
    queryFn: () => newsApi.listManage(search || undefined),
    enabled: canManageContent,
  });

  const saveMutation = useMutation({
    mutationFn: async (payload: Partial<News> & { id?: string }) => {
      if (payload.id) {
        const { id, ...rest } = payload;
        return newsApi.update(id, rest);
      }
      return newsApi.create(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['news-manage'] });
      queryClient.invalidateQueries({ queryKey: ['news'] });
      setShowForm(false);
      setEditItem(null);
      setError('');
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: newsApi.remove,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['news-manage'] });
      queryClient.invalidateQueries({ queryKey: ['news'] });
    },
  });

  if (!canManageContent) return <Navigate to="/" replace />;

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    saveMutation.mutate({
      id: editItem?.id,
      title: String(form.get('title')),
      summary: String(form.get('summary') || ''),
      content: String(form.get('content')),
      is_published: form.get('is_published') === 'on',
    });
  };

  return (
    <section className="page">
      <PageHeader
        title="Gestión de Noticias"
        subtitle="Administración de comunicados institucionales"
        action={
          <button
            className="btn btn-primary"
            onClick={() => {
              setEditItem(null);
              setShowForm(true);
            }}
          >
            + Nueva noticia
          </button>
        }
      />

      <SearchBar value={search} onChange={setSearch} placeholder="Buscar noticias..." />

      {isLoading ? (
        <p className="muted">Cargando...</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Título</th>
              <th>Resumen</th>
              <th>Publicada</th>
              <th>Fecha</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {news.map((item) => (
              <tr key={item.id}>
                <td>{item.title}</td>
                <td>{item.summary || '—'}</td>
                <td>{item.is_published ? 'Sí' : 'No'}</td>
                <td>{new Date(item.created_at).toLocaleDateString('es-ES')}</td>
                <td className="actions">
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => {
                      setEditItem(item);
                      setShowForm(true);
                    }}
                  >
                    Editar
                  </button>
                  <button className="btn btn-sm btn-danger" onClick={() => deleteMutation.mutate(item.id)}>
                    Eliminar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <FormModal
        isOpen={showForm}
        title={editItem ? 'Editar noticia' : 'Nueva noticia'}
        onClose={() => {
          setShowForm(false);
          setEditItem(null);
        }}
        onSubmit={handleSubmit}
        loading={saveMutation.isPending}
      >
        {error && <div className="alert alert-error">{error}</div>}
        <label>
          Título
          <input name="title" defaultValue={editItem?.title || ''} required />
        </label>
        <label>
          Resumen
          <input name="summary" defaultValue={editItem?.summary || ''} />
        </label>
        <label>
          Contenido
          <textarea name="content" rows={6} defaultValue={editItem?.content || ''} required />
        </label>
        <label className="checkbox-label">
          <input type="checkbox" name="is_published" defaultChecked={editItem?.is_published ?? true} />
          Publicada
        </label>
      </FormModal>
    </section>
  );
}
