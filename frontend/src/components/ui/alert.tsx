import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";

export function Alert({ className, ...props }: ComponentProps<"div">) {
  return (
    <div
      role="alert"
      data-slot="alert"
      className={cn(
        "mb-4 rounded-holh border border-solid border-[#fecaca] bg-[#fef2f2] px-4 py-3 text-[0.9rem] text-holh-danger",
        className,
      )}
      {...props}
    />
  );
}
