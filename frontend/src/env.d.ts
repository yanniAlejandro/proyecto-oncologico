/// <reference types="astro/client" />

declare namespace App {
  interface Locals {
    /** Usuario autenticado (resuelto en el middleware) o null para visitante. */
    user: import("@/shared/auth/roles").SessionUser | null;
    /** JWT de la cookie httpOnly; solo existe en el servidor. */
    token: string | null;
  }
}
