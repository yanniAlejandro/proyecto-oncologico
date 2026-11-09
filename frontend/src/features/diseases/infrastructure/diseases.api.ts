import type { Transport } from "@/shared/api/transport";
import type { Disease, DiseaseInput } from "../domain/types";

export function createDiseasesApi(t: Transport) {
  return {
    list: (search?: string) => t.request<Disease[]>("GET", "/diseases", { query: { search } }),
    create: (input: DiseaseInput) => t.request<Disease>("POST", "/diseases", { json: input }),
    update: (id: string, input: DiseaseInput) => t.request<Disease>("PUT", `/diseases/${id}`, { json: input }),
    remove: (id: string) => t.request<void>("DELETE", `/diseases/${id}`),
  };
}
export type DiseasesApi = ReturnType<typeof createDiseasesApi>;
