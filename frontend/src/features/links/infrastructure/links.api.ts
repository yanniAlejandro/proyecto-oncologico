import type { Transport } from "@/shared/api/transport";
import type { InterestLink, LinkInput } from "../domain/types";

export const createLinksApi = (t: Transport) => ({
  list: () => t.request<InterestLink[]>("GET", "/interest-links"),
  listAll: () => t.request<InterestLink[]>("GET", "/interest-links/manage"),
  create: (input: LinkInput) => t.request<InterestLink>("POST", "/interest-links", { json: input }),
  update: (id: string, input: LinkInput) => t.request<InterestLink>("PUT", `/interest-links/${id}`, { json: input }),
  remove: (id: string) => t.request<void>("DELETE", `/interest-links/${id}`),
});
export type LinksApi = ReturnType<typeof createLinksApi>;
