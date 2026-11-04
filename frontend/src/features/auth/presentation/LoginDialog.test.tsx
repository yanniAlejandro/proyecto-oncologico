import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ApiError } from "@/shared/api/transport";
import { LoginDialog } from "./LoginDialog";

async function fillAndSubmit(email: string) {
  await userEvent.click(screen.getByRole("button", { name: "Acceso para personal médico" }));
  const dialog = await screen.findByRole("dialog", { name: "Acceso institucional" });
  await userEvent.type(within(dialog).getByLabelText("Correo electrónico"), email);
  await userEvent.type(within(dialog).getByLabelText("Contraseña"), "secreto");
  await userEvent.click(within(dialog).getByRole("button", { name: "Ingresar al portal" }));
  return dialog;
}

it("muestra el error del backend y no recarga", async () => {
  const onLoggedIn = vi.fn();
  const loginFn = vi.fn().mockRejectedValue(new ApiError(401, "Credenciales inválidas"));
  render(<LoginDialog triggerLabel="Acceso para personal médico" loginFn={loginFn} onLoggedIn={onLoggedIn} />);
  const dialog = await fillAndSubmit("x@holh.cu");
  expect(await within(dialog).findByRole("alert")).toHaveTextContent("Credenciales inválidas");
  expect(onLoggedIn).not.toHaveBeenCalled();
});

it("al entrar delega en onLoggedIn (recarga SSR con la sesión)", async () => {
  const onLoggedIn = vi.fn();
  const loginFn = vi.fn().mockResolvedValue(undefined);
  render(<LoginDialog triggerLabel="Acceso para personal médico" loginFn={loginFn} onLoggedIn={onLoggedIn} />);
  await fillAndSubmit("medico@holh.cu");
  await waitFor(() => expect(onLoggedIn).toHaveBeenCalledOnce());
  expect(loginFn).toHaveBeenCalledWith("medico@holh.cu", "secreto");
});
