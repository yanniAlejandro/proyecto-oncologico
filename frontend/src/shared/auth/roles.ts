/** Roles y permisos del portal. Espejo de app/shared/domain/actor.py del backend. */

export const ROLES = ["administrador", "encargado", "medico"] as const;
export type UserRole = (typeof ROLES)[number];

export interface SessionUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
}

type MaybeUser = Pick<SessionUser, "role"> | null | undefined;

const has = (user: MaybeUser, ...roles: UserRole[]) => !!user && roles.includes(user.role);

export const canManageContent = (user: MaybeUser) => has(user, "administrador", "encargado");
export const canReadGuides = (user: MaybeUser) => has(user, "administrador", "encargado", "medico");
export const isAdmin = (user: MaybeUser) => has(user, "administrador");

/** Rutas protegidas: quién puede entrar. Lo aplica src/middleware.ts en el servidor. */
export const PROTECTED_ROUTES: { prefix: string; allowed: (user: MaybeUser) => boolean }[] = [
  { prefix: "/gestion/noticias", allowed: canManageContent },
  { prefix: "/gestion/usuarios", allowed: isAdmin },
];

export function isRouteAllowed(pathname: string, user: MaybeUser): boolean {
  const rule = PROTECTED_ROUTES.find((r) => pathname === r.prefix || pathname.startsWith(`${r.prefix}/`));
  return rule ? rule.allowed(user) : true;
}
