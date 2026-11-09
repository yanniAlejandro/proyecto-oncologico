/** Roles y permisos del portal. Espejo de app/shared/domain/actor.py del backend. */

export const ROLES = ["administrador", "medico"] as const;
export type UserRole = (typeof ROLES)[number];

export const SECTIONS = [
  "publicaciones",
  "guias",
  "protocolos",
  "enfermedades",
  "documentos",
  "enlaces",
  "quienes_somos",
  "linea_ayuda",
] as const;
export type Section = (typeof SECTIONS)[number];

export interface SessionUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  /** Secciones que puede gestionar (el backend las devuelve todas para un admin). */
  permissions: Section[];
}

type MaybeUser = Pick<SessionUser, "role" | "permissions"> | null | undefined;

export const isAdmin = (user: MaybeUser) => user?.role === "administrador";
/** Guías y protocolos: cualquier usuario con sesión. */
export const canReadClinical = (user: MaybeUser) => !!user;
/** Gestionar una sección: admin, o médico con ese permiso. */
export const can = (user: MaybeUser, section: Section) =>
  isAdmin(user) || !!user?.permissions?.includes(section);
/** Acceso al panel: admin o médico con al menos un permiso. */
export const canUsePanel = (user: MaybeUser) => isAdmin(user) || (user?.permissions?.length ?? 0) > 0;

/** Rutas protegidas: quién puede entrar. Lo aplica src/middleware.ts en el servidor. */
export const PROTECTED_ROUTES: { prefix: string; allowed: (user: MaybeUser) => boolean }[] = [
  { prefix: "/gestion/publicaciones", allowed: (u) => can(u, "publicaciones") },
  { prefix: "/gestion/quienes-somos", allowed: (u) => can(u, "quienes_somos") },
  { prefix: "/gestion/usuarios", allowed: isAdmin },
];

export function isRouteAllowed(pathname: string, user: MaybeUser): boolean {
  const rule = PROTECTED_ROUTES.find((r) => pathname === r.prefix || pathname.startsWith(`${r.prefix}/`));
  return rule ? rule.allowed(user) : true;
}
