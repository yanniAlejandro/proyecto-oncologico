import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";
import { fieldControl } from "./input";

/** Select nativo: accesible y usable en móvil sin JS extra. */
export function NativeSelect({ className, ...props }: ComponentProps<"select">) {
  return <select data-slot="native-select" className={cn(fieldControl, className)} {...props} />;
}
