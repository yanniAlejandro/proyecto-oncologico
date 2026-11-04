import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";

export function Badge({ className, ...props }: ComponentProps<"span">) {
  return (
    <span
      data-slot="badge"
      className={cn(
        "inline-block rounded bg-[#e3f0f4] px-[0.65rem] py-1 text-[0.8rem] font-semibold text-holh-blue",
        className,
      )}
      {...props}
    />
  );
}
