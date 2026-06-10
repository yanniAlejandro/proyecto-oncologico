import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import type { FormEvent } from 'react';
import { Navigate } from 'react-router-dom';
import { getErrorMessage } from '../api/client';
import { usersApi } from '../api/resources';
import { FormModal } from '../components/FormModal';
import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../context/AuthContext';

export function ManageUsersPage() {
  const { isAdmin } = useAuth();
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');
  const queryClient = useQueryClient();

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: usersApi.list,
    enabled: isAdmin,
  });

  const createMutation = useMutation({
    mutationFn: usersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setShowForm(false);
      setError('');
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const deactivateMutation = useMutation({
    mutationFn: usersApi.deactivate,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  });

  if (!isAdmin) return <Navigate to="/" replace />;

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    createMutation.mutate({
      email: String(form.get('email')),
      password: String(form.get('password')),
      full_name: String(form.get('full_name')),
    });
  };

  return (
    <section className="page">
      <PageHeader
        title="Gestión de Usuarios"
        subtitle="Registro y administración de cuentas del personal médico"
        action={
          <button className="btn btn-primary" onClick={() => setShowForm(true)}>
            + Nuevo médico
          </button>
        }
      />

      {isLoading ? (
        <p className="muted">Cargando usuarios...</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Correo</th>
              <th>Rol</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.full_name}</td>
                <td>{user.email}</td>
                <td>
                  <span className="badge">{user.role}</span>
                </td>
                <td>{user.is_active ? 'Activo' : 'Inactivo'}</td>
                <td className="actions">
                  {user.is_active && user.role === 'medico' && (
                    <button className="btn btn-sm btn-danger" onClick={() => deactivateMutation.mutate(user.id)}>
                      Desactivar
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <FormModal
        isOpen={showForm}
        title="Crear cuenta de médico"
        onClose={() => setShowForm(false)}
        onSubmit={handleSubmit}
        loading={createMutation.isPending}
        submitLabel="Crear cuenta"
      >
        {error && <div className="alert alert-error">{error}</div>}
        <label>
          Nombre completo
          <input name="full_name" required />
        </label>
        <label>
          Correo electrónico
          <input name="email" type="email" required />
        </label>
        <label>
          Contraseña
          <input name="password" type="password" minLength={6} required />
        </label>
      </FormModal>
    </section>
  );
}
