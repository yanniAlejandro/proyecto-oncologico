import type { Transport } from "@/shared/api/transport";
import type { ContactInfo } from "../domain/types";

export const createContactApi = (t: Transport) => ({
  get: () => t.request<ContactInfo>("GET", "/contact"),
});
