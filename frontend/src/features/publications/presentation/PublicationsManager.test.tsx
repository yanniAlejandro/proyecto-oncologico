import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { LinkPreview, Publication, PublicationInput } from "../domain/types";
import type { PublicationsApi } from "../infrastructure/publications.api";
import { PublicationsManager } from "./PublicationsManager";

const URL_OMS = "https://www.who.int/es/cancer";

const pub = (over: Partial<Publication> = {}): Publication => ({
  id: "1",
  title: "Jornada científica",
  url: "https://holh.sld.cu/jornada",
  domain: "holh.sld.cu",
  description: null,
  image_url: "/api/v1/publications/1/image?v=1",
  author_name: "Dra. María González",
  created_at: "2026-11-09T12:00:00Z",
  updated_at: "2026-11-09T12:00:00Z",
  ...over,
});

function fakeApi(previews: Record<string, LinkPreview> = {}) {
  const created: PublicationInput[] = [];
  const updated: [string, PublicationInput][] = [];
  const api: PublicationsApi = {
    list: async () => [pub()],
    preview: async (url) =>
      previews[url] ?? { found: false, title: null, description: null, image_url: null, site_name: null },
    create: async (input) => {
      created.push(input);
      return pub({ id: "2", title: input.title });
    },
    update: async (id, input) => {
      updated.push([id, input]);
      return pub({ id, title: input.title });
    },
    remove: async () => undefined,
  };
  return { api, created, updated };
}

const OMS_PREVIEW: LinkPreview = {
  found: true,
  title: "Cáncer — OMS",
  description: "Datos y cifras",
  image_url: "https://cdn.who.int/cancer.jpg",
  site_name: "OMS",
};

it("al pegar un enlace autocompleta título, descripción e imagen (como WhatsApp)", async () => {
  const user = userEvent.setup();
  const { api, created } = fakeApi({ [URL_OMS]: OMS_PREVIEW });
  render(<PublicationsManager initialItems={[pub()]} api={api} />);

  await user.click(screen.getByRole("button", { name: "+ Nueva publicación" }));
  const dialog = screen.getByRole("dialog");
  await user.click(within(dialog).getByLabelText("Enlace (URL)"));
  await user.paste(URL_OMS);

  await waitFor(() => expect(within(dialog).getByLabelText("Título")).toHaveValue("Cáncer — OMS"));
  expect(within(dialog).getByLabelText("Descripción")).toHaveValue("Datos y cifras");
  expect(within(dialog).getByLabelText("Usar la imagen de la página")).toBeChecked();

  await user.click(within(dialog).getByRole("button", { name: "Publicar" }));
  await waitFor(() => expect(created).toHaveLength(1));
  expect(created[0]).toMatchObject({
    url: URL_OMS,
    title: "Cáncer — OMS",
    image: { kind: "page", url: "https://cdn.who.int/cancer.jpg" },
  });
});

it("sin vista previa: avisa y deja completar a mano sin imagen", async () => {
  const user = userEvent.setup();
  const { api, created } = fakeApi();
  render(<PublicationsManager initialItems={[]} api={api} />);

  await user.click(screen.getByRole("button", { name: "+ Nueva publicación" }));
  const dialog = screen.getByRole("dialog");
  await user.click(within(dialog).getByLabelText("Enlace (URL)"));
  await user.paste("https://intranet.cu/nota");
  expect(await within(dialog).findByRole("status")).toHaveTextContent(/Escribe el título a mano/);

  await user.type(within(dialog).getByLabelText("Título"), "Nota interna");
  await user.click(within(dialog).getByRole("button", { name: "Publicar" }));
  await waitFor(() => expect(created).toHaveLength(1));
  expect(created[0].image).toEqual({ kind: "none" });
});

it("no pisa el título que el usuario ya escribió", async () => {
  const user = userEvent.setup();
  const { api } = fakeApi({ [URL_OMS]: OMS_PREVIEW });
  render(<PublicationsManager initialItems={[]} api={api} />);
  await user.click(screen.getByRole("button", { name: "+ Nueva publicación" }));
  const dialog = screen.getByRole("dialog");
  await user.type(within(dialog).getByLabelText("Título"), "Mi título");
  await user.click(within(dialog).getByLabelText("Enlace (URL)"));
  await user.paste(URL_OMS);
  await waitFor(() => expect(within(dialog).getByLabelText("Descripción")).toHaveValue("Datos y cifras"));
  expect(within(dialog).getByLabelText("Título")).toHaveValue("Mi título");
});

it("subida manual: rechaza formatos no admitidos antes de enviar", async () => {
  const user = userEvent.setup({ applyAccept: false });
  const { api, created } = fakeApi();
  render(<PublicationsManager initialItems={[]} api={api} />);
  await user.click(screen.getByRole("button", { name: "+ Nueva publicación" }));
  const dialog = screen.getByRole("dialog");
  await user.type(within(dialog).getByLabelText("Enlace (URL)"), "https://holh.sld.cu/x");
  await user.type(within(dialog).getByLabelText("Título"), "Con foto");
  await user.click(within(dialog).getByLabelText("Subir una imagen"));
  await user.upload(within(dialog).getByLabelText("Archivo de imagen"), new File(["<svg/>"], "a.svg", { type: "image/svg+xml" }));
  await user.click(within(dialog).getByRole("button", { name: "Publicar" }));
  expect(await within(dialog).findByText(/Formato no admitido/)).toBeInTheDocument();
  expect(created).toHaveLength(0);
});

it("editar conserva la imagen actual por defecto", async () => {
  const user = userEvent.setup();
  const { api, updated } = fakeApi();
  render(<PublicationsManager initialItems={[pub()]} api={api} />);
  await user.click(screen.getByRole("button", { name: "Editar" }));
  const dialog = screen.getByRole("dialog");
  expect(within(dialog).getByLabelText("Mantener la imagen actual")).toBeChecked();
  const title = within(dialog).getByLabelText("Título");
  await user.clear(title);
  await user.type(title, "Jornada 2026");
  await user.click(within(dialog).getByRole("button", { name: "Publicar" }));
  await waitFor(() => expect(updated).toHaveLength(1));
  expect(updated[0]).toEqual(["1", expect.objectContaining({ title: "Jornada 2026", image: { kind: "keep" } })]);
});
