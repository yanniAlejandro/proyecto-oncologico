import { createHash } from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { expect, test } from "@playwright/test";
import { login, logout, sidebar } from "./helpers";

/**
 * Flujo completo del repositorio de documentos respetando permisos:
 * una médica con permiso «documentos» sube un PDF desde el panel → queda en STORAGE_DIR →
 * cualquiera lo ve y lo descarga idéntico en /documentos (solo lectura) →
 * un médico sin permisos no puede gestionar → al eliminarlo desaparece del disco.
 */

const FIXTURE = path.join(import.meta.dirname, "fixtures/protocolo-prueba-e2e.pdf");
const STORAGE_DIR = path.resolve(process.env.E2E_STORAGE_DIR ?? path.join(import.meta.dirname, "../../backend/storage"));
const KEEP = process.env.E2E_KEEP === "1";
// Único por ejecución (con E2E_KEEP pueden convivir varias subidas).
const TITLE = `Protocolo de prueba E2E ${new Date().toISOString().slice(0, 19).replace("T", " ")} #${process.pid}`;

const sha256 = (data: Buffer) => createHash("sha256").update(data).digest("hex");

/** Archivos guardados en STORAGE_DIR (la clave es opaca: <2 primeros>/<uuid>.<ext>). */
async function storedFiles(): Promise<Set<string>> {
  const entries = await fs.readdir(STORAGE_DIR, { recursive: true, withFileTypes: true }).catch(() => []);
  return new Set(
    entries.filter((e) => e.isFile() && !e.name.startsWith(".upload-")).map((e) => path.join(e.parentPath, e.name)),
  );
}

test.describe.configure({ mode: "serial" });

test("subir, almacenar, ver, descargar y eliminar un PDF", async ({ page }, testInfo) => {
  const original = await fs.readFile(FIXTURE);
  const originalHash = sha256(original);
  const row = page.getByRole("row").filter({ hasText: TITLE });
  let storedPath: string | null = null;

  await test.step("visitante: ve el repositorio pero no puede subir", async () => {
    await page.goto("/documentos");
    await expect(page.getByRole("heading", { name: "Repositorio de Documentos" })).toBeVisible();
    await expect(page.getByRole("button", { name: "+ Nuevo documento" })).toHaveCount(0);
  });

  await test.step("médico sin permisos: no tiene panel ni puede entrar", async () => {
    await login(page, "medico");
    await expect(page.getByRole("link", { name: "Panel de gestión" })).toHaveCount(0);
    await page.goto("/admin/documentos");
    await expect(page).toHaveURL(/\/$/);
    await logout(page);
  });

  await test.step("la editora entra al panel y abre Documentos", async () => {
    await login(page, "editora");
    await page.getByRole("link", { name: "Panel de gestión" }).click();
    await sidebar(page).getByRole("link", { name: "Documentos" }).click();
    await expect(page.getByRole("heading", { name: "Repositorio de Documentos" })).toBeVisible();
    await expect(sidebar(page).getByRole("link", { name: "Usuarios y permisos" })).toHaveCount(0);
  });

  const before = await storedFiles();

  await test.step("sube el PDF desde el diálogo", async () => {
    await page.getByRole("button", { name: "+ Nuevo documento" }).click();
    const dialog = page.getByRole("dialog", { name: "Nuevo documento" });
    await dialog.getByLabel("Título").fill(TITLE);
    await dialog.getByLabel("Descripción").fill("Documento ficticio subido por la prueba E2E.");
    await dialog.locator('input[type="file"]').setInputFiles(FIXTURE);
    await expect(dialog.getByText("protocolo-prueba-e2e.pdf")).toBeVisible(); // la zona de soltar muestra el archivo
    await dialog.getByRole("button", { name: "Subir documento" }).click();
    await expect(dialog).toBeHidden();
    await expect(row).toBeVisible();
    await expect(row).toContainText("PDF · 1,5 KB");
  });

  await test.step("el archivo queda en el almacenamiento del backend", async () => {
    // El archivo de ESTA subida es el que aparece nuevo respecto a la foto previa.
    const created = [...(await storedFiles())].filter((f) => !before.has(f));
    expect(created, `archivos nuevos en ${STORAGE_DIR}`).toHaveLength(1);
    storedPath = created[0]!;
    expect(sha256(await fs.readFile(storedPath))).toBe(originalHash);
    const stat = await fs.stat(storedPath!);
    expect(stat.size).toBe(original.length);
    const info = `Archivo almacenado: ${storedPath}\nTamaño: ${stat.size} bytes · SHA-256: ${originalHash}`;
    console.log(`\n${info}\n`);
    await testInfo.attach("archivo-almacenado.txt", { body: info, contentType: "text/plain" });
  });

  await test.step("se ve en el navegador (visor)", async () => {
    await row.getByRole("button", { name: `Ver ${TITLE}` }).click();
    const viewer = page.getByRole("dialog", { name: TITLE });
    const frame = viewer.locator("iframe");
    await expect(frame).toBeVisible();
    const src = await frame.getAttribute("src");
    expect(src).toMatch(/\/api\/v1\/documents\/.+\/file\?disposition=inline$/);
    const res = await page.request.get(src!);
    expect(res.headers()["content-type"]).toBe("application/pdf");
    expect(res.headers()["content-disposition"]).toMatch(/^inline;/);
    expect(sha256(await res.body())).toBe(originalHash);
    await page.waitForTimeout(Number(process.env.E2E_SLOWMO ?? 0) * 4); // tiempo para verlo en --headed
    await page.keyboard.press("Escape");
    await expect(viewer).toBeHidden();
  });

  await test.step("se descarga idéntico", async () => {
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      row.getByRole("link", { name: "Descargar protocolo-prueba-e2e.pdf" }).click(),
    ]);
    expect(download.suggestedFilename()).toBe("protocolo-prueba-e2e.pdf");
    expect(sha256(await fs.readFile((await download.path())!))).toBe(originalHash);
  });

  await test.step("visitante: lo ve y descarga en la página pública, pero no puede eliminar", async () => {
    await logout(page);
    await page.goto("/documentos");
    await expect(row).toBeVisible();
    await expect(row.getByRole("button", { name: `Ver ${TITLE}` })).toBeVisible();
    await expect(row.getByRole("button", { name: "Eliminar" })).toHaveCount(0);
  });

  if (KEEP) {
    console.log(`\nE2E_KEEP=1 → se conserva el documento «${TITLE}» y su archivo ${storedPath}\n`);
    return;
  }

  await test.step("la editora lo elimina desde el panel (con confirmación) y el archivo desaparece del disco", async () => {
    await login(page, "editora");
    await page.goto("/admin/documentos");
    await row.getByRole("button", { name: "Eliminar" }).click();
    await page.getByRole("alertdialog").getByRole("button", { name: "Eliminar" }).click();
    await expect(row).toHaveCount(0);
    await expect.poll(() => fs.access(storedPath!).then(() => true, () => false)).toBe(false);
  });
});
