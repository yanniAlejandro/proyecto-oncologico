import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ClinicalDoc } from "../domain/types";
import type { ClinicalApi } from "../infrastructure/clinical.api";
import { ClinicalDocsPage } from "./ClinicalDocsPage";

const guide: ClinicalDoc = {
  id: "g1",
  disease_id: "d1",
  disease_name: "Leucemia",
  title: "Guía LMA",
  content: "Criterios diagnósticos completos",
  author_name: "Encargado",
  created_at: "2026-11-04T12:00:00Z",
  updated_at: "2026-11-04T12:00:00Z",
};

function fakeApi() {
  const searches: (string | undefined)[] = [];
  const updates: unknown[] = [];
  const api: ClinicalApi = {
    list: async (search) => {
      searches.push(search);
      return search ? [] : [guide];
    },
    create: async () => guide,
    update: async (id, input) => {
      updates.push({ id, ...input });
      return guide;
    },
    remove: async () => undefined,
  };
  return { api, searches, updates };
}

it("médico: puede leer pero no editar ni eliminar", async () => {
  render(<ClinicalDocsPage kind="guide" initialItems={[guide]} diseases={[]} canManage={false} api={fakeApi().api} />);
  expect(screen.getByRole("heading", { name: "Guías de Diagnóstico" })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Editar" })).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "+ Nueva guía" })).not.toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Leer" }));
  expect(await screen.findByText("Criterios diagnósticos completos")).toBeInTheDocument();
});

it("la búsqueda consulta la API con el término (con debounce)", async () => {
  const { api, searches } = fakeApi();
  render(<ClinicalDocsPage kind="protocol" initialItems={[guide]} diseases={[]} canManage={false} api={api} />);
  await userEvent.type(screen.getByRole("searchbox"), "  zzz ");
  await waitFor(() => expect(searches).toContain("zzz"));
  expect(await screen.findByText("No se encontraron protocolos.")).toBeInTheDocument();
});

it("encargado: edita con el formulario precargado", async () => {
  const { api, updates } = fakeApi();
  const diseases = [{ id: "d1", name: "Leucemia", description: null }];
  render(<ClinicalDocsPage kind="guide" initialItems={[guide]} diseases={diseases} canManage api={api} />);
  await userEvent.click(screen.getByRole("button", { name: "Editar" }));
  const dialog = await screen.findByRole("dialog", { name: "Editar guía" });
  const title = within(dialog).getByLabelText("Título");
  expect(title).toHaveValue("Guía LMA");
  await userEvent.clear(title);
  await userEvent.type(title, "Guía LMA 2026");
  await userEvent.click(within(dialog).getByRole("button", { name: "Guardar" }));
  await waitFor(() => expect(updates).toEqual([{ id: "g1", disease_id: "d1", title: "Guía LMA 2026", content: guide.content }]));
});
