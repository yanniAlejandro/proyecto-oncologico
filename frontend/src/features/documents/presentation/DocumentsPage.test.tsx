import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { DocumentItem } from "../domain/types";
import type { DocumentsApi } from "../infrastructure/documents.api";
import { DocumentsPage } from "./DocumentsPage";

const doc = (over: Partial<DocumentItem>): DocumentItem => ({
  id: "1",
  title: "Manual HOLH",
  description: "Procedimientos",
  file_name: "manual.pdf",
  file_type: "PDF",
  file_url: null,
  size_bytes: 2048,
  has_file: true,
  is_previewable: true,
  uploader_name: "Encargado",
  created_at: "2026-11-04T12:00:00Z",
  ...over,
});

const items = [
  doc({}),
  doc({ id: "2", title: "Checklist", file_name: "check.docx", file_type: "DOCX", is_previewable: false }),
  doc({ id: "3", title: "OMS", file_name: "oms.pdf", has_file: false, is_previewable: false, file_url: "https://who.int/oms.pdf" }),
];

function fakeApi(): DocumentsApi & { removed: string[]; created: unknown[] } {
  const removed: string[] = [];
  const created: unknown[] = [];
  return {
    removed,
    created,
    list: async () => items.filter((i) => !removed.includes(i.id)),
    uploadPolicy: async () => ({ allowed_extensions: [".pdf"], max_bytes: 1024 }),
    create: async (input) => {
      created.push(input);
      return doc({ id: "9", title: input.title });
    },
    remove: async (id) => {
      removed.push(id);
    },
  };
}

beforeEach(() => {
  globalThis.fetch = (async () => new Response(null, { status: 200 })) as typeof fetch; // HEAD del visor
});

it("visitante: ve, descarga y abre enlaces externos, pero no sube ni elimina", () => {
  render(<DocumentsPage initialItems={items} canManage={false} api={fakeApi()} />);
  expect(screen.queryByRole("button", { name: "+ Nuevo documento" })).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Eliminar" })).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Ver Manual HOLH" })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Ver Checklist" })).not.toBeInTheDocument(); // DOCX: sin vista previa
  expect(screen.getByRole("link", { name: "Descargar check.docx" })).toHaveAttribute(
    "href",
    "/api/v1/documents/2/file?disposition=attachment",
  );
  expect(screen.getByRole("link", { name: "Abrir OMS (enlace externo)" })).toHaveAttribute("href", "https://who.int/oms.pdf");
});

it("abre el visor con el PDF incrustado", async () => {
  render(<DocumentsPage initialItems={items} canManage={false} api={fakeApi()} />);
  await userEvent.click(screen.getByRole("button", { name: "Ver Manual HOLH" }));
  const dialog = await screen.findByRole("dialog");
  const frame = await within(dialog).findByTitle("Vista previa de manual.pdf");
  expect(frame).toHaveAttribute("src", "/api/v1/documents/1/file?disposition=inline");
});

it("encargado: eliminar pide confirmación antes de borrar (BUG-004)", async () => {
  const api = fakeApi();
  render(<DocumentsPage initialItems={items} canManage api={api} />);
  await userEvent.click(screen.getAllByRole("button", { name: "Eliminar" })[0]!);
  expect(api.removed).toEqual([]);
  const confirm = await screen.findByRole("alertdialog");
  await userEvent.click(within(confirm).getByRole("button", { name: "Eliminar" }));
  await waitFor(() => expect(api.removed).toEqual(["1"]));
});

it("encargado: valida el archivo en cliente antes de subirlo", async () => {
  const api = fakeApi();
  const policy = { allowed_extensions: [".pdf"], max_bytes: 1024 };
  render(<DocumentsPage initialItems={items} canManage policy={policy} api={api} />);
  await userEvent.click(screen.getByRole("button", { name: "+ Nuevo documento" }));
  const dialog = await screen.findByRole("dialog");
  await userEvent.type(within(dialog).getByLabelText("Título"), "Informe anual");
  const input = dialog.querySelector<HTMLInputElement>('input[type="file"]')!;
  await userEvent.upload(input, new File(["x".repeat(10)], "virus.exe"), { applyAccept: false });
  expect(await within(dialog).findByRole("alert")).toHaveTextContent("Tipo de archivo no permitido");
  await userEvent.upload(input, new File(["%PDF-1.4"], "informe.pdf", { type: "application/pdf" }));
  await userEvent.click(within(dialog).getByRole("button", { name: "Subir documento" }));
  await waitFor(() => expect(api.created).toHaveLength(1));
  expect(api.created[0]).toMatchObject({ title: "Informe anual", file: expect.any(File) });
});
