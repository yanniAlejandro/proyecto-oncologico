import type { Transport } from "@/shared/api/transport";
import type { DocumentItem, UploadPolicy } from "../domain/types";

export interface NewDocumentInput {
  title: string;
  description?: string;
  file?: File | null;
  file_url?: string;
}

export function createDocumentsApi(t: Transport) {
  return {
    list: (search?: string) => t.request<DocumentItem[]>("GET", "/documents", { query: { search } }),
    uploadPolicy: () => t.request<UploadPolicy>("GET", "/documents/upload-policy"),
    create: (input: NewDocumentInput) => {
      const body = new FormData();
      body.set("title", input.title);
      if (input.description) body.set("description", input.description);
      if (input.file) body.set("file", input.file);
      else if (input.file_url) body.set("file_url", input.file_url);
      return t.request<DocumentItem>("POST", "/documents", { body });
    },
    remove: (id: string) => t.request<void>("DELETE", `/documents/${id}`),
  };
}
export type DocumentsApi = ReturnType<typeof createDocumentsApi>;
