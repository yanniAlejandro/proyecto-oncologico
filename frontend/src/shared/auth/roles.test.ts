import { adminNavFor, can, canReadClinical, canUsePanel, isAdmin, isRouteAllowed } from "./roles";

const admin = { role: "administrador" as const, permissions: [] };
const editor = { role: "medico" as const, permissions: ["publicaciones" as const, "documentos" as const] };
const doctor = { role: "medico" as const, permissions: [] };

describe("permisos (espejo del backend)", () => {
  it("el admin gestiona todo aunque no tenga permisos guardados", () => {
    expect(can(admin, "guias")).toBe(true);
    expect(isAdmin(admin)).toBe(true);
    expect(canUsePanel(admin)).toBe(true);
  });

  it("un médico solo gestiona las secciones concedidas", () => {
    expect(can(editor, "publicaciones")).toBe(true);
    expect(can(editor, "guias")).toBe(false);
    expect(canUsePanel(editor)).toBe(true);
    expect(can(doctor, "publicaciones")).toBe(false);
    expect(canUsePanel(doctor)).toBe(false);
  });

  it("guías y protocolos: cualquier usuario con sesión", () => {
    expect(canReadClinical(doctor)).toBe(true);
    expect(canReadClinical(null)).toBe(false);
  });

  it("el menú del panel solo muestra lo concedido", () => {
    expect(adminNavFor(editor).map((i) => i.href)).toEqual(["/admin", "/admin/publicaciones", "/admin/documentos"]);
    expect(adminNavFor(admin)).toHaveLength(11);
    expect(adminNavFor(doctor)).toEqual([]);
  });

  it("protege el panel en el servidor (la regla más específica gana)", () => {
    expect(isRouteAllowed("/admin", editor)).toBe(true);
    expect(isRouteAllowed("/admin/publicaciones", editor)).toBe(true);
    expect(isRouteAllowed("/admin/guias", editor)).toBe(false);
    expect(isRouteAllowed("/admin/usuarios", editor)).toBe(false);
    expect(isRouteAllowed("/admin/usuarios", admin)).toBe(true);
    expect(isRouteAllowed("/admin", doctor)).toBe(false);
    expect(isRouteAllowed("/admin/", null)).toBe(false);
    expect(isRouteAllowed("/administracion", null)).toBe(true); // no es prefijo de ruta
    expect(isRouteAllowed("/documentos", null)).toBe(true);
  });
});
