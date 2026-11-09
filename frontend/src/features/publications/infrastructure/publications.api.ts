import type { Transport } from "@/shared/api/transport";
import { type LinkPreview, type Publication, type PublicationInput, toFormData } from "../domain/types";

export function createPublicationsApi(t: Transport) {
  return {
    list: (search?: string) => t.request<Publication[]>("GET", "/publications", { query: { search } }),
    preview: (url: string) => t.request<LinkPreview>("POST", "/publications/preview", { json: { url } }),
    create: (input: PublicationInput) =>
      t.request<Publication>("POST", "/publications", { body: toFormData(input, { editing: false }) }),
    update: (id: string, input: PublicationInput) =>
      t.request<Publication>("PUT", `/publications/${id}`, { body: toFormData(input, { editing: true }) }),
    remove: (id: string) => t.request<void>("DELETE", `/publications/${id}`),
  };
}
export type PublicationsApi = ReturnType<typeof createPublicationsApi>;
