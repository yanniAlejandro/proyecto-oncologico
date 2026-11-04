import { canManageContent, canReadGuides, isAdmin, isRouteAllowed } from "./roles";

const admin = { role: "administrador" as const };
const manager = { role: "encargado" as const };
const doctor = { role: "medico" as const };

describe("permisos por rol (espejo del backend)", () => {
  it.each([
    [admin, true, true, true],
    [manager, true, true, false],
    [doctor, false, true, false],
    [null, false, false, false],
  ])("%o → gestiona=%s, guías=%s, admin=%s", (user, manage, guides, adm) => {
    expect(canManageContent(user)).toBe(manage);
    expect(canReadGuides(user)).toBe(guides);
    expect(isAdmin(user)).toBe(adm);
  });

  it("protege las rutas de gestión en el servidor", () => {
    expect(isRouteAllowed("/gestion/noticias", manager)).toBe(true);
    expect(isRouteAllowed("/gestion/noticias", doctor)).toBe(false);
    expect(isRouteAllowed("/gestion/noticias/", null)).toBe(false);
    expect(isRouteAllowed("/gestion/usuarios", manager)).toBe(false);
    expect(isRouteAllowed("/gestion/usuarios", admin)).toBe(true);
    expect(isRouteAllowed("/gestion/noticiasX", null)).toBe(true); // no es prefijo de ruta
    expect(isRouteAllowed("/documentos", null)).toBe(true);
  });
});
