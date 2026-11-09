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

export const SECTION_LABELS: Record<Section, string> = {
  publicaciones: "Publicaciones",
  guias: "Guías de diagnóstico",
  protocolos: "Protocolos de tratamiento",
  enfermedades: "Enfermedades",
  documentos: "Documentos",
  enlaces: "Enlaces de interés",
  quienes_somos: "Quiénes somos",
  linea_ayuda: "Línea de ayuda",
};

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
export const can = (user: MaybeUser, section: Section) => isAdmin(user) || !!user?.permissions?.includes(section);
/** Acceso al panel: admin o médico con al menos un permiso. */
export const canUsePanel = (user: MaybeUser) => isAdmin(user) || (user?.permissions?.length ?? 0) > 0;

/** Qué hace falta para cada pantalla del panel: una sección, o ser administrador. */
export type Requirement = Section | "admin" | "panel";

export interface AdminNavItem {
  href: string;
  label: string;
  requires: Requirement;
  group: "General" | "Contenido clínico" | "Portal" | "Administración";
  icon: string; // nombre del icono de lucide (lo resuelve AdminLayout)
}

export const ADMIN_NAV: AdminNavItem[] = [
  { href: "/admin", label: "Resumen", requires: "panel", group: "General", icon: "LayoutDashboard" },
  { href: "/admin/publicaciones", label: "Publicaciones", requires: "publicaciones", group: "Portal", icon: "Newspaper" },
  { href: "/admin/quienes-somos", label: "Quiénes somos", requires: "quienes_somos", group: "Portal", icon: "Building2" },
  { href: "/admin/linea-ayuda", label: "Línea de ayuda", requires: "linea_ayuda", group: "Portal", icon: "PhoneCall" },
  { href: "/admin/enlaces", label: "Enlaces de interés", requires: "enlaces", group: "Portal", icon: "Link" },
  { href: "/admin/contacto", label: "Contacto", requires: "admin", group: "Portal", icon: "MapPin" },
  { href: "/admin/guias", label: "Guías de diagnóstico", requires: "guias", group: "Contenido clínico", icon: "Stethoscope" },
  { href: "/admin/protocolos", label: "Protocolos", requires: "protocolos", group: "Contenido clínico", icon: "ClipboardList" },
  { href: "/admin/enfermedades", label: "Enfermedades", requires: "enfermedades", group: "Contenido clínico", icon: "Activity" },
  { href: "/admin/documentos", label: "Documentos", requires: "documentos", group: "Contenido clínico", icon: "FileText" },
  { href: "/admin/usuarios", label: "Usuarios y permisos", requires: "admin", group: "Administración", icon: "Users" },
];

export function meets(user: MaybeUser, requires: Requirement): boolean {
  if (requires === "panel") return canUsePanel(user);
  if (requires === "admin") return isAdmin(user);
  return can(user, requires);
}

/** Entradas del panel visibles para el usuario. */
export const adminNavFor = (user: MaybeUser) => ADMIN_NAV.filter((item) => meets(user, item.requires));

const matches = (pathname: string, prefix: string) => pathname === prefix || pathname.startsWith(`${prefix}/`);

/** Rutas protegidas (lo aplica src/middleware.ts en el servidor). La más específica gana. */
export function isRouteAllowed(pathname: string, user: MaybeUser): boolean {
  const rule = [...ADMIN_NAV]
    .sort((a, b) => b.href.length - a.href.length)
    .find((item) => matches(pathname, item.href));
  return rule ? meets(user, rule.requires) : true;
}

/** Rutas antiguas de gestión → panel. */
export const LEGACY_REDIRECTS: Record<string, string> = {
  "/gestion/noticias": "/admin/publicaciones",
  "/gestion/publicaciones": "/admin/publicaciones",
  "/gestion/quienes-somos": "/admin/quienes-somos",
  "/gestion/linea-ayuda": "/admin/linea-ayuda",
  "/gestion/usuarios": "/admin/usuarios",
};
