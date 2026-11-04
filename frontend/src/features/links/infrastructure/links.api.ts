import type { Transport } from "@/shared/api/transport";
import type { InterestLink } from "../domain/types";

export const createLinksApi = (t: Transport) => ({
  list: () => t.request<InterestLink[]>("GET", "/interest-links"),
});
