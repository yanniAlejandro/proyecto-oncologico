export interface Publication {
  id: string;
  title: string;
  url: string;
  domain: string;
  description: string | null;
  /** Servida por nuestra API (copia local), nunca la imagen original. */
  image_url: string | null;
  author_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface LinkPreview {
  found: boolean;
  title: string | null;
  description: string | null;
  image_url: string | null;
  site_name: string | null;
}

/** De dónde sale la imagen al guardar. */
export type ImageChoice =
  | { kind: "keep" }
  | { kind: "none" }
  | { kind: "page"; url: string }
  | { kind: "upload"; file: File };

export interface PublicationInput {
  title: string;
  url: string;
  description: string;
  image: ImageChoice;
}

export const MAX_IMAGE_BYTES = 5 * 1024 * 1024;
export const IMAGE_TYPES = ["image/png", "image/jpeg", "image/gif", "image/webp"];

export function isHttpUrl(value: string): boolean {
  try {
    const u = new URL(value.trim());
    return (u.protocol === "http:" || u.protocol === "https:") && !!u.hostname;
  } catch {
    return false;
  }
}

/** Validación en cliente (el backend vuelve a comprobar el contenido real del fichero). */
export function validateImageFile(file: File): string | null {
  if (!IMAGE_TYPES.includes(file.type)) return "Formato no admitido: usa PNG, JPEG, GIF o WebP.";
  if (file.size > MAX_IMAGE_BYTES) return "La imagen supera el máximo de 5 MB.";
  return null;
}

/** Multipart para crear/editar: `image` (subida) o `image_url` (og:image que el servidor descarga). */
export function toFormData(input: PublicationInput, { editing }: { editing: boolean }): FormData {
  const form = new FormData();
  form.set("title", input.title.trim());
  form.set("url", input.url.trim());
  form.set("description", input.description.trim());
  const { image } = input;
  if (image.kind === "upload") form.set("image", image.file);
  else if (image.kind === "page") form.set("image_url", image.url);
  else if (image.kind === "none" && editing) form.set("remove_image", "true");
  return form;
}
