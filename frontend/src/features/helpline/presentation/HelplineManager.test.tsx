import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ConfigInput, HelplineConfig, ProfessionalInput } from "../domain/types";
import type { HelplineApi } from "../infrastructure/helpline.api";
import { HelplineManager } from "./HelplineManager";

const config: HelplineConfig = {
  phone: "+53 7 000 0000",
  label: "Teléfono de atención",
  off_hours_message: "Fuera de horario",
  emergency_phone: null,
  slots: [{ weekday: 0, start: "08:00", end: "12:00" }],
  daily_hours: [4, 0, 0, 0, 0, 0, 0],
  meets_minimum: false,
};

function fakeApi() {
  const saved: ConfigInput[] = [];
  const created: ProfessionalInput[] = [];
  const api: HelplineApi = {
    get: async () => ({ config, status: { available_now: true, next_opening: null }, professionals: [], weekdays: [] }),
    updateConfig: async (input) => {
      saved.push(input);
      return { ...config, ...input, daily_hours: [6, 6, 6, 6, 6, 0, 0], meets_minimum: false };
    },
    listProfessionals: async () => [],
    createProfessional: async (input) => {
      created.push(input);
      return { id: "1", status: null, ...input };
    },
    updateProfessional: async (id, input) => ({ id, status: null, ...input }),
    removeProfessional: async () => undefined,
  };
  return { api, saved, created };
}

it("avisa cuando el horario no cubre las 6 horas diarias", () => {
  render(<HelplineManager initialConfig={config} initialProfessionals={[]} api={fakeApi().api} />);
  expect(screen.getByText(/no cubre las 6 horas diarias/)).toHaveTextContent("Lunes (4 h)");
});

it("rellena lunes a viernes y guarda teléfono y horario", async () => {
  const user = userEvent.setup();
  const { api, saved } = fakeApi();
  render(<HelplineManager initialConfig={config} initialProfessionals={[]} api={api} />);
  await user.click(screen.getByRole("button", { name: "Lunes a viernes 08:00–14:00" }));
  await user.click(screen.getByRole("button", { name: "Guardar teléfono y horario" }));
  await waitFor(() => expect(saved).toHaveLength(1));
  expect(saved[0].slots).toHaveLength(5);
  expect(saved[0].slots.every((s) => s.start === "08:00" && s.end === "14:00")).toBe(true);
  expect(await screen.findByRole("status")).toHaveTextContent("Cambios guardados");
});

it("no envía un profesional con una franja al revés", async () => {
  const user = userEvent.setup();
  const { api, created } = fakeApi();
  render(<HelplineManager initialConfig={config} initialProfessionals={[]} api={api} />);
  await user.click(screen.getByRole("button", { name: "+ Nuevo profesional" }));
  const dialog = screen.getByRole("dialog");
  await user.type(within(dialog).getByLabelText("Nombre"), "Dra. Ana");
  await user.type(within(dialog).getByLabelText("Especialidad o servicio"), "Pediatría");
  await user.type(within(dialog).getByLabelText("Teléfono"), "+53 5 123 4567");
  await user.click(within(dialog).getByRole("button", { name: "+ Añadir franja" }));
  const end = within(dialog).getByLabelText("Fin de la franja 1");
  await user.clear(end);
  await user.type(end, "07:00");
  await user.click(within(dialog).getByRole("button", { name: "Guardar" }));
  expect(await within(dialog).findByText(/anterior a la de fin/)).toBeInTheDocument();
  expect(created).toHaveLength(0);
});
