import { expect, type Page } from "@playwright/test";

export const USERS = {
  admin: ["admin@oncologico.com", "Admin123!"],
  editora: ["editora@oncologico.com", "Editora123!"], // médica con permisos de publicaciones, documentos y enlaces
  medico: ["medico@oncologico.com", "Medico123!"], // médico sin permisos (solo lectura)
} as const;

export async function login(page: Page, who: keyof typeof USERS) {
  const [email, password] = USERS[who];
  await page.goto("/");
  await page.getByRole("button", { name: "Acceso para personal médico" }).click();
  const dialog = page.getByRole("dialog", { name: "Acceso institucional" });
  await dialog.getByLabel("Correo electrónico").fill(email);
  await dialog.getByLabel("Contraseña").fill(password);
  await dialog.getByRole("button", { name: "Ingresar al portal" }).click();
  await expect(page.getByRole("button", { name: "Cerrar sesión" })).toBeVisible();
}

/** Cierra sesión desde el portal o desde el panel. */
export async function logout(page: Page) {
  await page.goto("/");
  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(page.getByText("Acceso público")).toBeVisible();
}

/** Menú lateral del panel. */
export const sidebar = (page: Page) => page.getByRole("complementary", { name: "Menú del panel" });
