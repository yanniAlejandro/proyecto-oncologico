import type { Transport } from "@/shared/api/transport";
import type { News, NewsInput } from "../domain/types";

export function createNewsApi(t: Transport) {
  return {
    listPublished: (search?: string) => t.request<News[]>("GET", "/news", { query: { search } }),
    listAll: (search?: string) => t.request<News[]>("GET", "/news/manage", { query: { search } }),
    create: (input: NewsInput) => t.request<News>("POST", "/news", { json: input }),
    update: (id: string, input: Partial<NewsInput>) => t.request<News>("PUT", `/news/${id}`, { json: input }),
    remove: (id: string) => t.request<void>("DELETE", `/news/${id}`),
  };
}
export type NewsApi = ReturnType<typeof createNewsApi>;
