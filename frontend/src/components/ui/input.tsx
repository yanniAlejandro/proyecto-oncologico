import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";

export const fieldControl =
  "w-full rounded-holh border border-solid border-holh-border bg-white px-[0.85rem] py-[0.6rem] text-[0.95rem] leading-[normal] font-normal text-holh-text transition-[border-color,box-shadow] duration-200 focus:border-holh-teal focus:shadow-[0_0_0_3px_rgba(42,143,158,0.12)] focus:outline-none aria-invalid:border-holh-danger";

export function Input({ className, ...props }: ComponentProps<"input">) {
  return <input data-slot="input" className={cn(fieldControl, className)} {...props} />;
}
