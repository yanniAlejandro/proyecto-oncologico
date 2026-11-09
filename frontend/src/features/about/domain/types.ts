export interface AboutSection {
  id: string;
  slug: string;
  title: string;
  body: string;
  sort_order: number;
  image_url: string | null;
  updated_at: string;
}

export interface AboutSectionInput {
  title: string;
  body: string;
  sort_order: number;
  image: { kind: "keep" } | { kind: "none" } | { kind: "upload"; file: File };
}

export function toFormData(input: AboutSectionInput, { editing }: { editing: boolean }): FormData {
  const form = new FormData();
  form.set("title", input.title.trim());
  form.set("body", input.body);
  form.set("sort_order", String(input.sort_order));
  if (input.image.kind === "upload") form.set("image", input.image.file);
  else if (input.image.kind === "none" && editing) form.set("remove_image", "true");
  return form;
}
