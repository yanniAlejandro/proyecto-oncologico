import type { Transport } from "@/shared/api/transport";
import { CLINICAL_COPY, type ClinicalDoc, type ClinicalInput, type ClinicalKind } from "../domain/types";

export function createClinicalApi(t: Transport, kind: ClinicalKind) {
  const base = CLINICAL_COPY[kind].endpoint;
  return {
    list: (search?: string) => t.request<ClinicalDoc[]>("GET", base, { query: { search } }),
    create: (input: ClinicalInput) => t.request<ClinicalDoc>("POST", base, { json: input }),
    update: (id: string, input: Partial<ClinicalInput>) =>
      t.request<ClinicalDoc>("PUT", `${base}/${id}`, { json: input }),
    remove: (id: string) => t.request<void>("DELETE", `${base}/${id}`),
  };
}
export type ClinicalApi = ReturnType<typeof createClinicalApi>;
