import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { AboutSection, AboutSectionInput } from "../domain/types";
import type { AboutApi } from "../infrastructure/about.api";
import { AboutManager } from "./AboutManager";

const section = (over: Partial<AboutSection>): AboutSection => ({
  id: "1",
  slug: "el-centro",
  title: "El centro",
  body: "Texto",
  sort_order: 10,
  image_url: null,
  updated_at: "2026-11-09T12:00:00Z",
  ...over,
});

function fakeApi(items: AboutSection[]) {
  const updates: [string, AboutSectionInput][] = [];
  const api: AboutApi = {
    list: async () => items,
    create: async (input) => section({ id: "9", title: input.title }),
    update: async (id, input) => {
      updates.push([id, input]);
      return section({ id, title: input.title });
    },
    remove: async () => undefined,
  };
  return { api, updates };
}

const items = [section({}), section({ id: "2", slug: "pediatria", title: "Pediatría", sort_order: 20 })];

it("reordena intercambiando el orden de dos apartados", async () => {
  const user = userEvent.setup();
  const { api, updates } = fakeApi(items);
  render(<AboutManager initialItems={items} api={api} />);
  await user.click(screen.getByRole("button", { name: "Subir «Pediatría»" }));
  await waitFor(() => expect(updates).toHaveLength(2));
  expect(updates[0]).toEqual(["2", expect.objectContaining({ sort_order: 10, image: { kind: "keep" } })]);
  expect(updates[1]).toEqual(["1", expect.objectContaining({ sort_order: 20 })]);
  expect(screen.getByRole("button", { name: "Subir «El centro»" })).toBeDisabled();
});

it("muestra cómo queda el texto con formato antes de guardar", async () => {
  const user = userEvent.setup();
  const { api, updates } = fakeApi(items);
  render(<AboutManager initialItems={items} api={api} />);
  await user.click(screen.getAllByRole("button", { name: "Editar" })[0]);
  const dialog = screen.getByRole("dialog");
  const body = within(dialog).getByLabelText("Texto");
  await user.clear(body);
  await user.type(body, "### Misión{enter}- **Humanidad**");
  await user.click(within(dialog).getByRole("button", { name: "Ver cómo queda" }));
  expect(within(dialog).getByRole("heading", { name: "Misión" })).toBeInTheDocument();
  expect(within(dialog).getByText("Humanidad").tagName).toBe("STRONG");
  await user.click(within(dialog).getByRole("button", { name: "Guardar" }));
  await waitFor(() => expect(updates).toHaveLength(1));
  expect(updates[0][1]).toMatchObject({ body: "### Misión\n- **Humanidad**", image: { kind: "none" } });
});
