import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type SubmitEvent, useMemo, useState } from "react";
import { DataTable } from "@/components/site/DataTable";
import { FormDialog } from "@/components/site/FormDialog";
import { PageHeader } from "@/components/site/PageHeader";
import { Alert } from "@/components/ui/alert";
import { ConfirmDialog } from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { browserTransport } from "@/shared/api/browser";
import { getErrorMessage } from "@/shared/api/transport";
import { QueryProvider } from "@/shared/query/QueryProvider";
import { canDeactivate, type UserAccount } from "../domain/types";
import { createUsersApi, type UsersApi } from "../infrastructure/users.api";

interface Props {
  initialItems: UserAccount[];
  api?: UsersApi;
}

export function UsersManager(props: Props) {
  return (
    <QueryProvider>
      <Manager {...props} />
    </QueryProvider>
  );
}

function Manager({ initialItems, api: injected }: Props) {
  const api = useMemo(() => injected ?? createUsersApi(browserTransport), [injected]);
  const queryClient = useQueryClient();
  const [formOpen, setFormOpen] = useState(false);
  const [toDeactivate, setToDeactivate] = useState<UserAccount | null>(null);
  const [formError, setFormError] = useState("");
  const [actionError, setActionError] = useState("");

  const { data: users = [] } = useQuery({ queryKey: ["users"], queryFn: api.list, initialData: initialItems });
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["users"] });

  const create = useMutation({
    mutationFn: api.createDoctor,
    onSuccess: () => {
      invalidate();
      setFormOpen(false);
    },
    onError: (err) => setFormError(getErrorMessage(err)),
  });

  const deactivate = useMutation({
    mutationFn: (id: string) => api.deactivate(id),
    onSuccess: () => {
      invalidate();
      setToDeactivate(null);
    },
    onError: (err) => {
      setActionError(getErrorMessage(err));
      setToDeactivate(null);
    },
  });

  const handleSubmit = (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    create.mutate({
      email: String(form.get("email")),
      password: String(form.get("password")),
      full_name: String(form.get("full_name")),
    });
  };

  return (
    <>
      <PageHeader
        title="Gestión de Usuarios"
        subtitle="Registro y administración de cuentas del personal médico"
        action={
          <Button
            onClick={() => {
              setFormError("");
              setFormOpen(true);
            }}
          >
            + Nuevo médico
          </Button>
        }
      />
      {actionError && <Alert>{actionError}</Alert>}

      <DataTable
        caption="Usuarios"
        columns={["Nombre", "Correo", "Rol", "Estado", "Acciones"]}
        isEmpty={users.length === 0}
        emptyMessage="No hay usuarios."
      >
        {users.map((user) => (
          <tr key={user.id}>
            <td>{user.full_name}</td>
            <td>{user.email}</td>
            <td>
              <Badge>{user.role}</Badge>
            </td>
            <td>{user.is_active ? "Activo" : "Inactivo"}</td>
            <td>
              <div className="actions">
                {canDeactivate(user) && (
                  <Button variant="danger" size="sm" onClick={() => setToDeactivate(user)}>
                    Desactivar
                  </Button>
                )}
              </div>
            </td>
          </tr>
        ))}
      </DataTable>

      <FormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        title="Crear cuenta de médico"
        onSubmit={handleSubmit}
        loading={create.isPending}
        submitLabel="Crear cuenta"
        error={formError}
      >
        <Field label="Nombre completo">
          <Input name="full_name" required minLength={2} autoComplete="off" />
        </Field>
        <Field label="Correo electrónico">
          <Input name="email" type="email" required autoComplete="off" />
        </Field>
        <Field label="Contraseña">
          <Input name="password" type="password" minLength={6} required autoComplete="new-password" />
        </Field>
      </FormDialog>

      <ConfirmDialog
        open={!!toDeactivate}
        onOpenChange={(o) => !o && setToDeactivate(null)}
        title="¿Desactivar la cuenta?"
        description={`${toDeactivate?.full_name ?? ""} ya no podrá iniciar sesión.`}
        confirmLabel="Desactivar"
        pendingLabel="Desactivando..."
        pending={deactivate.isPending}
        onConfirm={() => toDeactivate && deactivate.mutate(toDeactivate.id)}
      />
    </>
  );
}
