import type { Transport } from "@/shared/api/transport";
import type { ConfigInput, Helpline, HelplineConfig, Professional, ProfessionalInput } from "../domain/types";

export function createHelplineApi(t: Transport) {
  return {
    get: () => t.request<Helpline>("GET", "/helpline"),
    updateConfig: (input: ConfigInput) => t.request<HelplineConfig>("PUT", "/helpline", { json: input }),
    listProfessionals: () => t.request<Professional[]>("GET", "/helpline/professionals"),
    createProfessional: (input: ProfessionalInput) =>
      t.request<Professional>("POST", "/helpline/professionals", { json: input }),
    updateProfessional: (id: string, input: ProfessionalInput) =>
      t.request<Professional>("PUT", `/helpline/professionals/${id}`, { json: input }),
    removeProfessional: (id: string) => t.request<void>("DELETE", `/helpline/professionals/${id}`),
  };
}
export type HelplineApi = ReturnType<typeof createHelplineApi>;
