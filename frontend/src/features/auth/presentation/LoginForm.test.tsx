import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ApiError } from "@/shared/api/transport";
import { LoginForm } from "./LoginForm";

async function fillAndSubmit(email: string) {
  await userEvent.type(screen.getByLabelText("Correo electrónico"), email);
  await userEvent.type(screen.getByLabelText("Contraseña"), "secreto");
  await userEvent.click(screen.getByRole("button", { name: "Ingresar al portal" }));
}

it("muestra el error del backend y no navega", async () => {
  const onLoggedIn = vi.fn();
  const loginFn = vi.fn().mockRejectedValue(new ApiError(401, "Credenciales inválidas"));
  render(<LoginForm next="/admin" loginFn={loginFn} onLoggedIn={onLoggedIn} />);
  await fillAndSubmit("x@holh.cu");
  expect(await screen.findByRole("alert")).toHaveTextContent("Credenciales inválidas");
  expect(onLoggedIn).not.toHaveBeenCalled();
  expect(screen.getByRole("button", { name: "Ingresar al portal" })).toBeEnabled();
});

it("al entrar vuelve a la ruta pedida", async () => {
  const onLoggedIn = vi.fn();
  const loginFn = vi.fn().mockResolvedValue(undefined);
  render(<LoginForm next="/admin/guias" loginFn={loginFn} onLoggedIn={onLoggedIn} />);
  await fillAndSubmit("medico@holh.cu");
  await waitFor(() => expect(onLoggedIn).toHaveBeenCalledWith("/admin/guias"));
  expect(loginFn).toHaveBeenCalledWith("medico@holh.cu", "secreto");
});
