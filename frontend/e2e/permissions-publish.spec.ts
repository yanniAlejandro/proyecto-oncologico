import { expect, test } from "@playwright/test";
import { login, logout, sidebar } from "./helpers";

/**
 * Modelo de permisos de punta a punta: un médico sin permisos solo lee; el administrador le concede
 * «Publicaciones» desde el panel; el médico publica (vista previa no disponible → modo manual);
 * la publicación aparece en la página pública; al retirarle el permiso pierde el acceso al instante.
 */

const DOCTOR = "Dr. Juan Pérez";
const TITLE = `Jornada de prueba E2E #${process.pid}`;
// Dominio reservado (.invalid): nunca resuelve → el formulario pasa a modo manual sin depender de Internet.
const URL = `https://jornada-${process.pid}.portal.invalid/`;

test.describe.configure({ mode: "serial" });

async function setDoctorPublications(page: import("@playwright/test").Page, grant: boolean) {
  await page.goto("/admin/usuarios");
  const row = page.getByRole("row").filter({ hasText: DOCTOR });
  await row.getByRole("button", { name: "Editar" }).click();
  const dialog = page.getByRole("dialog", { name: `Editar a ${DOCTOR}` });
  await dialog.getByLabel("Publicaciones").setChecked(grant);
  await dialog.getByRole("button", { name: "Guardar" }).click();
  await expect(dialog).toBeHidden();
  await expect(row).toContainText(grant ? "Publicaciones" : "Solo lectura");
}

test.afterAll(async ({ browser }) => {
  // Deja la BD como estaba aunque el test falle a mitad.
  const page = await browser.newPage();
  await login(page, "admin");
  const row = page.getByRole("row").filter({ hasText: DOCTOR });
  await page.goto("/admin/usuarios");
  if ((await row.textContent())?.includes("Publicaciones")) await setDoctorPublications(page, false);
  await page.goto("/admin/publicaciones");
  const pub = page.getByRole("row").filter({ hasText: TITLE });
  if (await pub.count()) {
    await pub.getByRole("button", { name: "Eliminar" }).click();
    await page.getByRole("alertdialog").getByRole("button", { name: "Eliminar" }).click();
    await expect(pub).toHaveCount(0);
  }
  await page.close();
});

test("el administrador concede «Publicaciones» y el médico publica", async ({ page }) => {
  await test.step("médico sin permisos: solo lectura", async () => {
    await login(page, "medico");
    await expect(page.getByRole("link", { name: "Panel de gestión" })).toHaveCount(0);
    await logout(page);
  });

  await test.step("el admin le concede el permiso desde Usuarios y permisos", async () => {
    await login(page, "admin");
    await setDoctorPublications(page, true);
    await logout(page);
  });

  await test.step("el médico ve el panel solo con Publicaciones", async () => {
    await login(page, "medico");
    await page.getByRole("link", { name: "Panel de gestión" }).click();
    const links = sidebar(page).getByRole("navigation").getByRole("link");
    await expect(links).toHaveText(["Resumen", "Publicaciones"]);
  });

  await test.step("publica un enlace completando los datos a mano", async () => {
    await sidebar(page).getByRole("link", { name: "Publicaciones" }).click();
    await page.getByRole("button", { name: "+ Nueva publicación" }).click();
    const dialog = page.getByRole("dialog", { name: "Nueva publicación" });
    await dialog.getByLabel("Enlace (URL)").fill(URL);
    await dialog.getByLabel("Enlace (URL)").blur();
    await expect(dialog.getByRole("status")).toContainText("Escribe el título a mano");
    await dialog.getByLabel("Título").fill(TITLE);
    await dialog.getByLabel("Descripción").fill("Publicación creada por la prueba E2E de permisos.");
    await dialog.getByRole("button", { name: "Publicar" }).click();
    await expect(dialog).toBeHidden();
    await expect(page.getByRole("row").filter({ hasText: TITLE })).toContainText(DOCTOR);
  });

  await test.step("aparece en la página pública con su autor", async () => {
    await page.goto("/publicaciones");
    const card = page.getByRole("link").filter({ hasText: TITLE });
    await expect(card).toBeVisible();
    await expect(card).toContainText(DOCTOR);
    await expect(card).toHaveAttribute("href", URL);
  });

  await test.step("sin el permiso, pierde el acceso al instante (sin volver a iniciar sesión)", async () => {
    const admin = await page.context().browser()!.newPage(); // otro contexto: otra sesión
    await login(admin, "admin");
    await setDoctorPublications(admin, false);
    await admin.close();
    await page.goto("/admin/publicaciones");
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole("link", { name: "Panel de gestión" })).toHaveCount(0);
  });
});
