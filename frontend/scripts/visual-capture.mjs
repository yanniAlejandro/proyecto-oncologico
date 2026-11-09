// Captura cada pantalla × rol × viewport y la compara con la referencia visual.
//
//   pnpm visual                       → captura en docs/visual-current y compara con docs/visual-baseline
//   pnpm visual -- --base http://localhost:4321 --out ../docs/visual-current --baseline ../docs/visual-baseline
//
// Requisitos: API y frontend levantados, BD con los seeds. Chromium de Playwright
// (`pnpm exec playwright install chromium`, o CHROMIUM_PATH). Informe: <out>/report.md con el % de píxeles distintos por pantalla.
import fs from "node:fs/promises";
import path from "node:path";
import { parseArgs } from "node:util";
import pixelmatch from "pixelmatch";
import { chromium } from "@playwright/test";
import { PNG } from "pngjs";

const { values: args } = parseArgs({
  // pnpm reenvía el «--» de `pnpm visual -- --base …`; tras «--» parseArgs lo trataría todo como posicional.
  args: process.argv.slice(2).filter((a) => a !== "--"),
  options: {
    base: { type: "string", default: "http://localhost:4321" },
    out: { type: "string", default: "../docs/visual-current" },
    baseline: { type: "string", default: "../docs/visual-baseline" },
  },
});

const USERS = {
  visitante: null,
  medico: ["medico@oncologico.com", "Medico123!"], // sin permisos: solo lectura
  editora: ["editora@oncologico.com", "Editora123!"], // médica con permisos (publicaciones, documentos, enlaces)
  admin: ["admin@oncologico.com", "Admin123!"],
};
// Las rutas sin acceso redirigen: el nombre del fichero lo indica (__redirect_...).
const ROUTES = [
  ["01-quienes-somos", "/"],
  ["02-publicaciones", "/publicaciones"],
  ["03-guias", "/guias-diagnostico"],
  ["04-protocolos", "/protocolos-tratamiento"],
  ["05-documentos", "/documentos"],
  ["06-enlaces", "/enlaces"],
  ["07-linea-ayuda", "/linea-de-ayuda"],
  ["08-contacto", "/contacto"],
  ["09-panel-resumen", "/admin"],
  ["10-panel-publicaciones", "/admin/publicaciones"],
  ["11-panel-usuarios", "/admin/usuarios"],
  ["12-login", "/login?next=%2Fadmin"],
];
const MODALS = [
  ["medico", "m02-guia-leer", "/guias-diagnostico", "Leer"],
  ["editora", "m03-publicacion-nueva", "/admin/publicaciones", "+ Nueva publicación"],
  ["editora", "m04-documento-nuevo", "/admin/documentos", "+ Nuevo documento"],
  ["admin", "m05-guia-nueva", "/admin/guias", "+ Nueva guía"],
  ["admin", "m06-protocolo-editar", "/admin/protocolos", "Editar"],
  ["admin", "m07-usuario-editar", "/admin/usuarios", "Editar"],
  ["medico", "m08-documento-visor", "/documentos", /^Ver /],
];
const VIEWPORTS = { desktop: { width: 1440, height: 900 }, mobile: { width: 390, height: 844 } };

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

// El Chromium de @playwright/test (`pnpm exec playwright install chromium`), o CHROMIUM_PATH.
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });
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
      const routePath = new URL(route, args.base).pathname;
      const suffix = finalPath !== routePath ? `__redirect${finalPath.replaceAll("/", "_")}` : "";
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
