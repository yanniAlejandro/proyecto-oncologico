import { cva, type VariantProps } from "class-variance-authority";
import { Slot } from "radix-ui";
import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";

/**
 * Nota: el tamaño de letra lleva el interlineado en la misma clase (`text-[x]/[normal]`);
 * con `leading-*` aparte, tailwind-merge lo descartaría al combinar variantes.
 *
 * Botón shadcn con las variantes del portal HOLH (antes .btn/.btn-primary/...). */
export const buttonVariants = cva(
  "inline-flex items-center justify-center gap-1.5 rounded-holh border-0 font-semibold whitespace-nowrap cursor-pointer transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-55 [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        primary: "bg-holh-teal text-white hover:bg-holh-teal-dark hover:text-white hover:shadow-holh-sm",
        secondary: "bg-holh-blue text-white hover:bg-holh-blue-light hover:text-white",
        outline:
          "border border-solid border-holh-border bg-transparent text-holh-text hover:border-holh-teal hover:text-holh-teal",
        danger: "bg-holh-danger text-white hover:bg-holh-danger-dark hover:text-white",
        header:
          "border border-solid border-holh-border bg-transparent text-holh-blue hover:bg-holh-cream hover:text-holh-blue",
        ghost: "bg-transparent text-holh-muted hover:bg-holh-cream hover:text-holh-text",
      },
      size: {
        default: "px-[1.1rem] py-[0.55rem] text-[0.9rem]/[normal]",
        sm: "px-[0.65rem] py-[0.3rem] text-[0.8rem]/[normal]",
        lg: "px-6 py-3 text-[0.95rem]/[normal]",
        header: "px-[0.85rem] py-[0.4rem] text-[0.82rem]/[normal]",
        icon: "size-8 p-0 text-2xl/none",
      },
    },
    defaultVariants: { variant: "primary", size: "default" },
  },
);

export type ButtonProps = ComponentProps<"button"> & VariantProps<typeof buttonVariants> & { asChild?: boolean };

export function Button({ className, variant, size, asChild = false, type, ...props }: ButtonProps) {
  const Comp = asChild ? Slot.Root : "button";
  return (
    <Comp
      data-slot="button"
      type={asChild ? undefined : (type ?? "button")}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  );
}
