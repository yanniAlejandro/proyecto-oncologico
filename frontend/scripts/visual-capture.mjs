// Captura cada pantalla × rol × viewport y la compara con la referencia visual.
//
//   pnpm visual                       → captura en docs/visual-current y compara con docs/visual-baseline
//   pnpm visual -- --base http://localhost:4321 --out ../docs/visual-current --baseline ../docs/visual-baseline
//
// Requisitos: API y frontend levantados, BD con los seeds. Chromium de Playwright en ~/.cache/ms-playwright
// (o CHROMIUM_PATH). Informe: <out>/report.md con el % de píxeles distintos por pantalla.
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { parseArgs } from "node:util";
import pixelmatch from "pixelmatch";
import { chromium } from "playwright-core";
import { PNG } from "pngjs";

const { values: args } = parseArgs({
  options: {
    base: { type: "string", default: "http://localhost:4321" },
    out: { type: "string", default: "../docs/visual-current" },
    baseline: { type: "string", default: "../docs/visual-baseline" },
  },
});

const USERS = {
  visitante: null,
  medico: ["medico@oncologico.com", "Medico123!"],
  encargado: ["encargado@oncologico.com", "Encargado123!"],
  admin: ["admin@oncologico.com", "Admin123!"],
};
const ROUTES = [
  ["01-noticias", "/"],
  ["02-guias", "/guias-diagnostico"],
  ["03-protocolos", "/protocolos-tratamiento"],
  ["04-documentos", "/documentos"],
  ["05-enlaces", "/enlaces"],
  ["06-contacto", "/contacto"],
  ["07-gestion-noticias", "/gestion/noticias"],
  ["08-gestion-usuarios", "/gestion/usuarios"],
];
const MODALS = [
  ["visitante", "m01-login", "/", "Acceso para personal médico"],
  ["medico", "m02-guia-leer", "/guias-diagnostico", "Leer"],
  ["encargado", "m03-guia-nueva", "/guias-diagnostico", "+ Nueva guía"],
  ["encargado", "m04-protocolo-editar", "/protocolos-tratamiento", "Editar"],
  ["encargado", "m05-documento-nuevo", "/documentos", "+ Nuevo documento"],
  ["encargado", "m06-noticia-nueva", "/gestion/noticias", "+ Nueva noticia"],
  ["admin", "m07-usuario-nuevo", "/gestion/usuarios", "+ Nuevo médico"],
  ["visitante", "m08-documento-visor", "/documentos", /^Ver /],
];
const VIEWPORTS = { desktop: { width: 1440, height: 900 }, mobile: { width: 390, height: 844 } };

async function chromiumPath() {
  if (process.env.CHROMIUM_PATH) return process.env.CHROMIUM_PATH;
  const root = path.join(os.homedir(), ".cache/ms-playwright");
  const dirs = (await fs.readdir(root)).filter((d) => d.startsWith("chromium-")).sort();
  return path.join(root, dirs.at(-1), "chrome-linux/chrome");
}

async function settle(page) {
  await page.waitForLoadState("networkidle");
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(250);
}

async function diffPercent(aPath, bPath, diffPath) {
  const [a, b] = await Promise.all([fs.readFile(aPath), fs.readFile(bPath)]);
  {
    const A = PNG.sync.read(a);
    const B = PNG.sync.read(b);
    const width = Math.max(A.width, B.width);
    const height = Math.max(A.height, B.height);
    const pad = (img) => {
      const out = new PNG({ width, height, fill: true });
      out.data.fill(255);
      PNG.bitblt(img, out, 0, 0, img.width, img.height, 0, 0);
      return out;
    };
    const diff = new PNG({ width, height });
    const changed = pixelmatch(pad(A).data, pad(B).data, diff.data, width, height, { threshold: 0.1 });
    if (changed > 0) await fs.writeFile(diffPath, PNG.sync.write(diff));
    return { pct: (100 * changed) / (width * height), sizeA: `${A.width}×${A.height}`, sizeB: `${B.width}×${B.height}` };
  }
}

const browser = await chromium.launch({ executablePath: await chromiumPath() });
const captured = [];
for (const [role, creds] of Object.entries(USERS)) {
  for (const [vpName, viewport] of Object.entries(VIEWPORTS)) {
    const ctx = await browser.newContext({ viewport, locale: "es-ES", deviceScaleFactor: 1 });
    // La toolbar de desarrollo de Astro no forma parte del portal: fuera de las capturas.
    await ctx.addInitScript(() => {
      const hide = () => {
        const style = document.createElement("style");
        style.textContent = "astro-dev-toolbar { display: none !important; }";
        document.head.append(style);
      };
      if (document.head) hide();
      else document.addEventListener("DOMContentLoaded", hide);
    });
    const page = await ctx.newPage();
    if (creds) {
      const res = await ctx.request.post(`${args.base}/api/auth/login`, {
        data: { email: creds[0], password: creds[1] },
        headers: { Origin: args.base },
      });
      if (!res.ok()) throw new Error(`Login ${role} falló: ${res.status()}`);
    }
    const dir = path.join(args.out, vpName, role);
    await fs.mkdir(dir, { recursive: true });
    for (const [name, route] of ROUTES) {
      await page.goto(args.base + route);
      await settle(page);
      const finalPath = new URL(page.url()).pathname;
      const suffix = finalPath !== route ? `__redirect${finalPath.replaceAll("/", "_")}` : "";
      const file = `${name}${suffix}.png`;
      await page.screenshot({ path: path.join(dir, file), fullPage: true });
      captured.push(path.join(vpName, role, file));
    }
    for (const [mRole, name, route, label] of MODALS) {
      if (mRole !== role) continue;
      await page.goto(args.base + route);
      await settle(page);
      await page.getByRole("button", { name: label, exact: typeof label === "string" }).first().click();
      await page.waitForTimeout(400);
      await page.screenshot({ path: path.join(dir, `${name}.png`) });
      captured.push(path.join(vpName, role, `${name}.png`));
    }
    await ctx.close();
  }
}
await browser.close();

const rows = [];
for (const rel of captured) {
  const base = path.join(args.baseline, rel);
  try {
    await fs.access(base);
  } catch {
    rows.push(`| ${rel} | nueva (sin referencia) | | |`);
    continue;
  }
  const r = await diffPercent(base, path.join(args.out, rel), path.join(args.out, rel.replace(/\.png$/, ".diff.png")));
  rows.push(`| ${rel} | ${r.pct.toFixed(2)} % | ${r.sizeA} | ${r.sizeB} |`);
}
const report = `# Comparación visual\n\nReferencia: \`${args.baseline}\` · Actual: \`${args.out}\`\n\n| Pantalla | Píxeles distintos | Tamaño ref. | Tamaño actual |\n|---|---|---|---|\n${rows.join("\n")}\n`;
await fs.writeFile(path.join(args.out, "report.md"), report);
console.log(report);
