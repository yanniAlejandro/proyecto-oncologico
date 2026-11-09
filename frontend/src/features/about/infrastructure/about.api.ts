import type { Transport } from "@/shared/api/transport";
import { type AboutSection, type AboutSectionInput, toFormData } from "../domain/types";

export function createAboutApi(t: Transport) {
  return {
    list: () => t.request<AboutSection[]>("GET", "/about"),
    create: (input: AboutSectionInput) =>
      t.request<AboutSection>("POST", "/about", { body: toFormData(input, { editing: false }) }),
    update: (id: string, input: AboutSectionInput) =>
      t.request<AboutSection>("PUT", `/about/${id}`, { body: toFormData(input, { editing: true }) }),
    remove: (id: string) => t.request<void>("DELETE", `/about/${id}`),
  };
}
export type AboutApi = ReturnType<typeof createAboutApi>;
