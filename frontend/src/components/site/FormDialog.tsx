import type { SubmitEvent, ReactNode } from "react";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Dialog, DialogBody, DialogContent, DialogFooter, DialogHeader } from "@/components/ui/dialog";

interface FormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  onSubmit: (e: SubmitEvent<HTMLFormElement>) => void;
  children: ReactNode;
  submitLabel?: string;
  loading?: boolean;
  loadingLabel?: string;
  error?: string;
}

export function FormDialog({
  open,
  onOpenChange,
  title,
  onSubmit,
  children,
  submitLabel = "Guardar",
  loading = false,
  loadingLabel = "Guardando...",
  error,
}: FormDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent aria-describedby={undefined}>
        <DialogHeader title={title} />
        <DialogBody asChild>
          <form onSubmit={onSubmit} className="grid gap-4" noValidate={false}>
            {error && <Alert className="mb-0">{error}</Alert>}
            {children}
            <DialogFooter>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? loadingLabel : submitLabel}
              </Button>
            </DialogFooter>
          </form>
        </DialogBody>
      </DialogContent>
    </Dialog>
  );
}
