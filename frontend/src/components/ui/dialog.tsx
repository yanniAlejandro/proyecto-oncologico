import { Dialog as DialogPrimitive, Slot } from "radix-ui";
import type { ComponentProps, ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * Diálogo shadcn (Radix) con el aspecto de los modales del portal.
 * El contenido va dentro del overlay (patrón "scrollable overlay" de Radix) para
 * centrarlo con grid igual que el `.modal-overlay` original.
 */
export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogClose = DialogPrimitive.Close;

export const overlayClass =
  "fixed inset-0 z-[1000] grid place-items-center overflow-y-auto bg-[rgba(6,42,64,0.55)] p-4 backdrop-blur-[4px]";
export const panelClass =
  "relative w-full rounded-holh-lg border border-solid border-holh-border bg-white shadow-holh-lg focus:outline-none";

export function DialogContent({
  className,
  children,
  size = "lg",
  ...props
}: ComponentProps<typeof DialogPrimitive.Content> & { size?: "sm" | "lg" | "xl" }) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className={overlayClass}>
        <DialogPrimitive.Content
          data-slot="dialog-content"
          className={cn(
            panelClass,
            size === "sm" && "max-w-[440px]",
            size === "lg" && "max-w-[640px]",
            size === "xl" && "max-w-[min(1100px,100%)]",
            className,
          )}
          {...props}
        >
          {children}
        </DialogPrimitive.Content>
      </DialogPrimitive.Overlay>
    </DialogPrimitive.Portal>
  );
}

export function DialogCloseButton({ className, label = "Cerrar" }: { className?: string; label?: string }) {
  return (
    <DialogPrimitive.Close
      aria-label={label}
      className={cn(
        "grid size-8 cursor-pointer place-items-center rounded-holh border-0 bg-transparent text-2xl leading-none text-holh-muted hover:bg-holh-cream hover:text-holh-text",
        className,
      )}
    >
      ×
    </DialogPrimitive.Close>
  );
}

export function DialogHeader({ title, actions }: { title: ReactNode; actions?: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-solid border-holh-border bg-holh-cream px-5 py-4">
      <DialogPrimitive.Title className="text-[1.1rem] font-bold text-holh-blue">{title}</DialogPrimitive.Title>
      <div className="flex items-center gap-2">
        {actions}
        <DialogCloseButton />
      </div>
    </div>
  );
}

export function DialogBody({ className, asChild, ...props }: ComponentProps<"div"> & { asChild?: boolean }) {
  const Comp = asChild ? Slot.Root : "div";
  return <Comp className={cn("p-5", className)} {...props} />;
}

export const DialogDescription = DialogPrimitive.Description;

export function DialogFooter({ className, ...props }: ComponentProps<"div">) {
  return <div className={cn("mt-2 flex justify-end gap-3", className)} {...props} />;
}
