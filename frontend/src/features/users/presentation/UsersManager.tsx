import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type SubmitEvent, useEffect, useMemo, useState } from "react";
import { DataTable } from "@/components/site/DataTable";
import { FormDialog } from "@/components/site/FormDialog";
import { PageHeader } from "@/components/site/PageHeader";
import { Alert } from "@/components/ui/alert";
import { ConfirmDialog } from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import { browserTransport } from "@/shared/api/browser";
import { getErrorMessage } from "@/shared/api/transport";
import { SECTION_LABELS, SECTIONS, type Section, type UserRole } from "@/shared/auth/roles";
import { QueryProvider } from "@/shared/query/QueryProvider";
import { isSelf, type UserAccount, type UserChanges } from "../domain/types";
import { createUsersApi, type UsersApi } from "../infrastructure/users.api";

interface Props {
  initialItems: UserAccount[];
  currentUserId: string;
  api?: UsersApi;
}

export function UsersManager(props: Props) {
  return (
    <QueryProvider>
      <Manager {...props} />
    </QueryProvider>
  );
}

const ROLE_LABEL: Record<UserRole, string> = { administrador: "Administrador", medico: "Médico" };

function PermissionsField({
  role,
  value,
  onChange,
}: {
  role: UserRole;
  value: Section[];
  onChange: (next: Section[]) => void;
}) {
  if (role === "administrador") {
    return <p className="m-0 text-[0.85rem] text-holh-muted">Un administrador gestiona todas las secciones.</p>;
  }
  return (
    <fieldset className="grid gap-2 border-0 p-0">
      <legend className="mb-1 text-[0.88rem] font-semibold text-holh-text">Puede gestionar</legend>
      <p className="m-0 text-[0.8rem] text-holh-muted">
        Sin ninguna marcada, el médico solo puede ver y descargar contenido.
      </p>
      <div className="permission-grid">
        {SECTIONS.map((section) => (
          <label key={section} className="flex items-center gap-2 text-[0.88rem] text-holh-text">
            <input
              type="checkbox"
              className="size-[13px] accent-holh-teal"
              checked={value.includes(section)}
              onChange={(e) =>
                onChange(e.target.checked ? [...value, section] : value.filter((s) => s !== section))
              }
            />
            {SECTION_LABELS[section]}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function Manager({ initialItems, currentUserId, api: injected }: Props) {
  const api = useMemo(() => injected ?? createUsersApi(browserTransport), [injected]);
  const queryClient = useQueryClient();
  const [editItem, setEditItem] = useState<UserAccount | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [toToggle, setToToggle] = useState<UserAccount | null>(null);
  const [formError, setFormError] = useState("");
  const [actionError, setActionError] = useState("");
  const [role, setRole] = useState<UserRole>("medico");
  const [permissions, setPermissions] = useState<Section[]>([]);

  const { data: users = [] } = useQuery({ queryKey: ["users"], queryFn: api.list, initialData: initialItems });
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["users"] });

  useEffect(() => {
    if (!formOpen) return;
    setRole(editItem?.role ?? "medico");
    setPermissions(editItem?.permissions ?? []);
  }, [formOpen, editItem]);

  const save = useMutation({
    mutationFn: async (form: FormData) => {
      const password = String(form.get("password") ?? "");
      const fullName = String(form.get("full_name"));
      if (!editItem) {
        return api.create({
          email: String(form.get("email")),
          password,
          full_name: fullName,
          role,
          permissions: role === "medico" ? permissions : [],
        });
      }
      const changes: UserChanges = { full_name: fullName, permissions: role === "medico" ? permissions : [] };
      if (!isSelf(editItem, currentUserId)) changes.role = role;
      if (password) changes.password = password;
      return api.update(editItem.id, changes);
    },
    onSuccess: () => {
      invalidate();
      setFormOpen(false);
      setEditItem(null);
    },
    onError: (err) => setFormError(getErrorMessage(err)),
  });

  const toggleActive = useMutation({
    mutationFn: (u: UserAccount) => api.update(u.id, { is_active: !u.is_active }),
    onSuccess: () => {
      invalidate();
      setToToggle(null);
    },
    onError: (err) => {
      setActionError(getErrorMessage(err));
      setToToggle(null);
    },
  });

  const openForm = (item: UserAccount | null) => {
    setEditItem(item);
    setFormError("");
    setFormOpen(true);
  };

  const handleSubmit = (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    save.mutate(new FormData(e.currentTarget));
  };

  const editingSelf = !!editItem && isSelf(editItem, currentUserId);

  return (
    <>
      <PageHeader
        title="Usuarios y permisos"
        subtitle="Cuentas del personal y secciones que cada médico puede gestionar"
        action={<Button onClick={() => openForm(null)}>+ Nuevo usuario</Button>}
      />
      {actionError && <Alert>{actionError}</Alert>}

      <DataTable
        caption="Usuarios"
        columns={["Nombre", "Correo", "Rol", "Permisos", "Estado", "Acciones"]}
        isEmpty={users.length === 0}
        emptyMessage="No hay usuarios."
      >
        {users.map((user) => (
          <tr key={user.id} className={user.is_active ? undefined : "opacity-60"}>
            <td>
              {user.full_name}
              {isSelf(user, currentUserId) && <span className="muted"> (tú)</span>}
            </td>
            <td>{user.email}</td>
            <td>
              <Badge>{ROLE_LABEL[user.role]}</Badge>
            </td>
            <td>
              {user.role === "administrador" ? (
                <span className="muted">Todas</span>
              ) : user.permissions.length === 0 ? (
                <span className="muted">Solo lectura</span>
              ) : (
                <div className="permission-chips">
                  {user.permissions.map((p) => (
                    <Badge key={p} className="text-[0.75rem]">
                      {SECTION_LABELS[p]}
                    </Badge>
                  ))}
                </div>
              )}
            </td>
            <td>{user.is_active ? "Activo" : "Inactivo"}</td>
            <td>
              <div className="actions">
                <Button variant="secondary" size="sm" onClick={() => openForm(user)}>
                  Editar
                </Button>
                {!isSelf(user, currentUserId) && (
                  <Button
                    variant={user.is_active ? "danger" : "outline"}
                    size="sm"
                    onClick={() => setToToggle(user)}
                  >
                    {user.is_active ? "Desactivar" : "Reactivar"}
                  </Button>
                )}
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
        title={editItem ? `Editar a ${editItem.full_name}` : "Nuevo usuario"}
        onSubmit={handleSubmit}
        loading={save.isPending}
        submitLabel={editItem ? "Guardar" : "Crear cuenta"}
        error={formError}
      >
        <Field label="Nombre completo">
          <Input name="full_name" defaultValue={editItem?.full_name ?? ""} required minLength={2} autoComplete="off" />
        </Field>
        {!editItem && (
          <Field label="Correo electrónico">
            <Input name="email" type="email" required autoComplete="off" />
          </Field>
        )}
        <Field label={editItem ? "Nueva contraseña (opcional)" : "Contraseña"}>
          <Input name="password" type="password" minLength={6} required={!editItem} autoComplete="new-password" />
        </Field>
        <Field label="Rol">
          <NativeSelect
            name="role"
            value={role}
            onChange={(e) => setRole(e.target.value as UserRole)}
            disabled={editingSelf}
          >
            <option value="medico">Médico</option>
            <option value="administrador">Administrador</option>
          </NativeSelect>
        </Field>
        {editingSelf && (
          <p className="m-0 text-[0.8rem] text-holh-muted">No puedes cambiar tu propio rol ni desactivarte.</p>
        )}
        <PermissionsField role={role} value={permissions} onChange={setPermissions} />
      </FormDialog>

      <ConfirmDialog
        open={!!toToggle}
        onOpenChange={(o) => !o && setToToggle(null)}
        title={toToggle?.is_active ? "¿Desactivar la cuenta?" : "¿Reactivar la cuenta?"}
        description={
          toToggle?.is_active
            ? `${toToggle?.full_name ?? ""} ya no podrá iniciar sesión.`
            : `${toToggle?.full_name ?? ""} podrá volver a iniciar sesión.`
        }
        confirmLabel={toToggle?.is_active ? "Desactivar" : "Reactivar"}
        pendingLabel="Guardando..."
        pending={toggleActive.isPending}
        onConfirm={() => toToggle && toggleActive.mutate(toToggle)}
      />
    </>
  );
}
