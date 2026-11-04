import type { Transport } from "@/shared/api/transport";
import type { Disease } from "../domain/types";

export function createDiseasesApi(t: Transport) {
  return {
    list: (search?: string) => t.request<Disease[]>("GET", "/diseases", { query: { search } }),
  };
}
export type DiseasesApi = ReturnType<typeof createDiseasesApi>;
