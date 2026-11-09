import { AlertDialog as AlertDialogPrimitive } from "radix-ui";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { buttonVariants } from "./button";
import { overlayClass, panelClass } from "./dialog";

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: ReactNode;
  description: ReactNode;
  confirmLabel?: string;
  pendingLabel?: string;
  pending?: boolean;
  onConfirm: () => void;
}

/** Confirmación destructiva (BUG-004): "Eliminar" ya no borra al primer clic. */
export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = "Eliminar",
  pendingLabel = "Eliminando...",
  pending = false,
  onConfirm,
}: ConfirmDialogProps) {
  return (
    <AlertDialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <AlertDialogPrimitive.Portal>
        <AlertDialogPrimitive.Overlay className={overlayClass}>
          <AlertDialogPrimitive.Content className={cn(panelClass, "max-w-[440px] p-5")}>
            <AlertDialogPrimitive.Title className="mb-2 text-[1.1rem] font-bold text-holh-blue">
              {title}
            </AlertDialogPrimitive.Title>
            <AlertDialogPrimitive.Description className="text-[0.92rem] text-holh-muted">
              {description}
            </AlertDialogPrimitive.Description>
            <div className="mt-5 flex justify-end gap-3">
              <AlertDialogPrimitive.Cancel className={buttonVariants({ variant: "outline" })}>
                Cancelar
              </AlertDialogPrimitive.Cancel>
              <button
                type="button"
                className={buttonVariants({ variant: "danger" })}
                disabled={pending}
                onClick={onConfirm}
              >
                {pending ? pendingLabel : confirmLabel}
              </button>
            </div>
          </AlertDialogPrimitive.Content>
        </AlertDialogPrimitive.Overlay>
      </AlertDialogPrimitive.Portal>
    </AlertDialogPrimitive.Root>
  );
}
