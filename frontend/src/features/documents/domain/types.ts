export interface DocumentItem {
  id: string;
  title: string;
  description: string | null;
  file_name: string;
  file_type: string | null;
  file_url: string | null;
  size_bytes: number | null;
  has_file: boolean;
  is_previewable: boolean;
  uploader_name: string | null;
  created_at: string;
}

export interface UploadPolicy {
  allowed_extensions: string[];
  max_bytes: number;
}

export type Disposition = "inline" | "attachment";

/** URL (vía proxy de Astro) para ver o descargar el archivo almacenado. */
export function documentFileUrl(doc: Pick<DocumentItem, "id">, disposition: Disposition, base = "/api/v1"): string {
  return `${base}/documents/${doc.id}/file?disposition=${disposition}`;
}

export type PreviewKind = "pdf" | "image" | "text" | null;

export function previewKind(doc: Pick<DocumentItem, "is_previewable" | "file_name">): PreviewKind {
  if (!doc.is_previewable) return null;
  const ext = doc.file_name.toLowerCase().split(".").pop();
  if (ext === "pdf") return "pdf";
  if (ext === "png" || ext === "jpg" || ext === "jpeg") return "image";
  if (ext === "txt") return "text";
  return null;
}

/** Validación previa en cliente (el backend vuelve a validar tipo, firma y tamaño). */
export function validateFile(file: File, policy: UploadPolicy | undefined): string | null {
  if (file.size === 0) return "El archivo está vacío";
  if (!policy) return null;
  const ext = `.${file.name.toLowerCase().split(".").pop()}`;
  if (!policy.allowed_extensions.includes(ext)) {
    const allowed = policy.allowed_extensions.map((e) => e.slice(1).toUpperCase()).join(", ");
    return `Tipo de archivo no permitido. Formatos aceptados: ${allowed}`;
  }
  if (file.size > policy.max_bytes) {
    return `El archivo supera el máximo de ${Math.floor(policy.max_bytes / (1024 * 1024))} MB`;
  }
  return null;
}
