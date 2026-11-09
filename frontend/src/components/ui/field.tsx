import type { ComponentProps, ReactNode } from "react";
import { cn } from "@/lib/utils";

/** Etiqueta envolvente: texto + control en rejilla (antes `.form-grid label`). */
export function Field({ label, children, className, ...props }: ComponentProps<"label"> & { label: ReactNode }) {
  return (
    <label className={cn("grid gap-[0.35rem] text-[0.88rem] font-semibold text-holh-text", className)} {...props}>
      {label}
      {children}
    </label>
  );
}

export function CheckboxField({ label, className, ...props }: ComponentProps<"input"> & { label: ReactNode }) {
  return (
    <label className={cn("flex items-center gap-2 text-[0.88rem] font-medium text-holh-text", className)}>
      <input type="checkbox" className="size-[13px] accent-holh-teal" {...props} />
      {label}
    </label>
  );
}
