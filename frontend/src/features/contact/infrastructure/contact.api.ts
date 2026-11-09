import type { Transport } from "@/shared/api/transport";
import type { ContactInfo, ContactInput } from "../domain/types";

export const createContactApi = (t: Transport) => ({
  get: () => t.request<ContactInfo>("GET", "/contact"),
  update: (input: ContactInput) => t.request<ContactInfo>("PUT", "/contact", { json: input }),
});
export type ContactApi = ReturnType<typeof createContactApi>;
