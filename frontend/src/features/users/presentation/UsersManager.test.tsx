import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { UserAccount, UserChanges } from "../domain/types";
import type { UsersApi } from "../infrastructure/users.api";
import { UsersManager } from "./UsersManager";

const admin: UserAccount = { id: "a", email: "admin@x.cu", full_name: "Admin", role: "administrador", is_active: true, permissions: [] };
const doctor: UserAccount = { id: "d", email: "med@x.cu", full_name: "Dr. Juan", role: "medico", is_active: true, permissions: [] };

function fakeApi() {
  const updates: [string, UserChanges][] = [];
  const api: UsersApi = {
    list: async () => [admin, doctor],
    create: async (input) => ({ id: "n", is_active: true, ...input }),
    update: async (id, changes) => {
      updates.push([id, changes]);
      return { ...(id === "a" ? admin : doctor), ...changes };
    },
  };
  return { api, updates };
}

it("un médico sin permisos aparece como «Solo lectura» y el admin le concede secciones", async () => {
  const user = userEvent.setup();
  const { api, updates } = fakeApi();
  render(<UsersManager initialItems={[admin, doctor]} currentUserId="a" api={api} />);
  expect(screen.getByText("Solo lectura")).toBeInTheDocument();

  await user.click(screen.getAllByRole("button", { name: "Editar" })[1]);
  const dialog = screen.getByRole("dialog");
  await user.click(within(dialog).getByLabelText("Publicaciones"));
  await user.click(within(dialog).getByLabelText("Documentos"));
  await user.click(within(dialog).getByRole("button", { name: "Guardar" }));
  await waitFor(() => expect(updates).toHaveLength(1));
  expect(updates[0]).toEqual(["d", expect.objectContaining({ role: "medico", permissions: ["publicaciones", "documentos"] })]);
  expect(updates[0][1]).not.toHaveProperty("password"); // contraseña vacía = no se cambia
});

it("el admin no puede cambiarse el rol ni desactivarse a sí mismo", async () => {
  const user = userEvent.setup();
  render(<UsersManager initialItems={[admin, doctor]} currentUserId="a" api={fakeApi().api} />);
  expect(screen.getAllByRole("button", { name: "Desactivar" })).toHaveLength(1); // solo el médico
  await user.click(screen.getAllByRole("button", { name: "Editar" })[0]);
  const dialog = screen.getByRole("dialog");
  expect(within(dialog).getByLabelText("Rol")).toBeDisabled();
  expect(within(dialog).getByText(/gestiona todas las secciones/)).toBeInTheDocument();
});
