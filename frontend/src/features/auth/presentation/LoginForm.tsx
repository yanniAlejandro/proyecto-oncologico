import { type SubmitEvent, useState } from "react";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { getErrorMessage } from "@/shared/api/transport";
import { login } from "../infrastructure/auth.api";

interface LoginFormProps {
  /** Ruta interna a la que volver (ya validada en el servidor con safeNext). */
  next: string;
  /** Inyectables para tests. */
  onLoggedIn?: (next: string) => void;
  loginFn?: typeof login;
}

/** Recarga completa: el SSR vuelve a pintar menú, cabecera y permisos con la sesión. */
const goTo = (next: string) => window.location.assign(next);

export function LoginForm({ next, onLoggedIn = goTo, loginFn = login }: LoginFormProps) {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setError("");
    setLoading(true);
    try {
      await loginFn(String(form.get("email")), String(form.get("password")));
      onLoggedIn(next);
    } catch (err) {
      setError(getErrorMessage(err));
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="grid gap-4" aria-label="Acceso institucional">
      {error && <Alert className="mb-0">{error}</Alert>}
      <Field label="Correo electrónico">
        <Input type="email" name="email" required autoComplete="username" placeholder="usuario@holh.sld.cu" autoFocus />
      </Field>
      <Field label="Contraseña">
        <Input type="password" name="password" required autoComplete="current-password" />
      </Field>
      <Button type="submit" disabled={loading}>
        {loading ? "Verificando credenciales..." : "Ingresar al portal"}
      </Button>
    </form>
  );
}
