import { type SubmitEvent, useState } from "react";
import { HospitalLogo } from "@/components/site/HospitalLogo";
import { Alert } from "@/components/ui/alert";
import { Button, type ButtonProps } from "@/components/ui/button";
import { Dialog, DialogCloseButton, DialogContent, DialogDescription, DialogTrigger } from "@/components/ui/dialog";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { getErrorMessage } from "@/shared/api/transport";
import { login } from "../infrastructure/auth.api";
import { Dialog as DialogPrimitive } from "radix-ui";

interface LoginDialogProps {
  triggerLabel: string;
  triggerSize?: ButtonProps["size"];
  /** Inyectable para tests. */
  onLoggedIn?: () => void;
  loginFn?: typeof login;
}

export function LoginDialog({
  triggerLabel,
  triggerSize = "default",
  onLoggedIn = () => window.location.reload(),
  loginFn = login,
}: LoginDialogProps) {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setError("");
    setLoading(true);
    try {
      await loginFn(String(form.get("email")), String(form.get("password")));
      onLoggedIn(); // el SSR vuelve a pintar cabecera, menú y permisos con la sesión
    } catch (err) {
      setError(getErrorMessage(err));
      setLoading(false);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) setError("");
      }}
    >
      <DialogTrigger asChild>
        <Button size={triggerSize}>{triggerLabel}</Button>
      </DialogTrigger>
      <DialogContent size="sm" className="overflow-hidden">
        <div className="flex items-center gap-4 bg-[linear-gradient(135deg,var(--holh-blue)_0%,var(--holh-blue-light)_100%)] p-6 text-white">
          <HospitalLogo size={48} />
          <div>
            <DialogPrimitive.Title className="text-[1.1rem] font-bold">Acceso institucional</DialogPrimitive.Title>
            <DialogDescription className="mt-[0.15rem] text-[0.82rem] opacity-85">
              Hospital Oncológico de La Habana
            </DialogDescription>
          </div>
        </div>
        <form onSubmit={handleSubmit} className="grid gap-4 p-5">
          {error && <Alert className="mb-0">{error}</Alert>}
          <Field label="Correo electrónico">
            <Input type="email" name="email" required autoComplete="username" placeholder="usuario@holh.sld.cu" />
          </Field>
          <Field label="Contraseña">
            <Input type="password" name="password" required autoComplete="current-password" />
          </Field>
          <Button type="submit" disabled={loading}>
            {loading ? "Verificando credenciales..." : "Ingresar al portal"}
          </Button>
        </form>
        <DialogCloseButton className="absolute top-3 right-3 text-white hover:text-holh-text" />
      </DialogContent>
    </Dialog>
  );
}
