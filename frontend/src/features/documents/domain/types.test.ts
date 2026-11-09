import { documentFileUrl, previewKind, validateFile } from "./types";

const policy = { allowed_extensions: [".pdf", ".docx", ".png"], max_bytes: 1024 };
const file = (name: string, size: number) => new File([new Uint8Array(size)], name);

it("documentFileUrl apunta al proxy con la disposición pedida", () => {
  expect(documentFileUrl({ id: "abc" }, "inline")).toBe("/api/v1/documents/abc/file?disposition=inline");
});

it("previewKind solo para tipos visualizables", () => {
  expect(previewKind({ is_previewable: true, file_name: "a.PDF" })).toBe("pdf");
  expect(previewKind({ is_previewable: true, file_name: "a.jpeg" })).toBe("image");
  expect(previewKind({ is_previewable: true, file_name: "a.txt" })).toBe("text");
  expect(previewKind({ is_previewable: false, file_name: "a.pdf" })).toBeNull();
});

it("validateFile replica la política del backend", () => {
  expect(validateFile(file("ok.pdf", 10), policy)).toBeNull();
  expect(validateFile(file("vacio.pdf", 0), policy)).toBe("El archivo está vacío");
  expect(validateFile(file("x.exe", 10), policy)).toMatch(/no permitido.*PDF, DOCX, PNG/);
  expect(validateFile(file("grande.pdf", 2048), policy)).toMatch(/supera el máximo/);
  expect(validateFile(file("sin-politica.exe", 10), undefined)).toBeNull();
});
