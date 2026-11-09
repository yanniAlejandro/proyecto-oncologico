import { expect, type Page } from "@playwright/test";

export const USERS = {
  admin: ["admin@oncologico.com", "Admin123!"],
  editora: ["editora@oncologico.com", "Editora123!"], // médica con permisos de publicaciones, documentos y enlaces
  medico: ["medico@oncologico.com", "Medico123!"], // médico sin permisos (solo lectura)
} as const;

/** Rellena el formulario de /login (la página ya debe estar abierta). */
export async function submitLogin(page: Page, who: keyof typeof USERS) {
  const [email, password] = USERS[who];
  const form = page.getByRole("form", { name: "Acceso institucional" });
  await form.getByLabel("Correo electrónico").fill(email);
  await form.getByLabel("Contraseña").fill(password);
  await form.getByRole("button", { name: "Ingresar al portal" }).click();
  await expect(page.getByRole("button", { name: "Cerrar sesión" })).toBeVisible();
}

export async function login(page: Page, who: keyof typeof USERS) {
  await page.goto("/login");
  // Con sesión abierta, /login redirige: se cierra la anterior para cambiar de usuario.
  if (!new URL(page.url()).pathname.startsWith("/login")) {
    await logout(page);
    await page.goto("/login");
  }
  await submitLogin(page, who);
}

/** Cierra sesión desde el portal o desde el panel. */
export async function logout(page: Page) {
  await page.goto("/");
  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(page.getByRole("link", { name: "Iniciar sesión" })).toBeVisible();
}

/** Menú lateral del panel. */
export const sidebar = (page: Page) => page.getByRole("complementary", { name: "Menú del panel" });
