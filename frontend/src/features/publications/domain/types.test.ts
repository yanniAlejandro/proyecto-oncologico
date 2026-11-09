import { isHttpUrl, toFormData, validateImageFile } from "./types";

const base = { title: " Nota ", url: " https://who.int/n ", description: " " };

describe("publicaciones: reglas puras", () => {
  it("solo acepta URLs http/https", () => {
    expect(isHttpUrl("https://who.int/x")).toBe(true);
    expect(isHttpUrl("javascript:alert(1)")).toBe(false);
    expect(isHttpUrl("who.int")).toBe(false);
  });

  it("imagen de la página → image_url (la descarga el servidor)", () => {
    const f = toFormData({ ...base, image: { kind: "page", url: "https://who.int/a.png" } }, { editing: false });
    expect(f.get("title")).toBe("Nota");
    expect(f.get("url")).toBe("https://who.int/n");
    expect(f.get("image_url")).toBe("https://who.int/a.png");
    expect(f.get("image")).toBeNull();
  });

  it("subida a mano → image; quitar imagen solo al editar", () => {
    const file = new File(["x"], "f.png", { type: "image/png" });
    expect(toFormData({ ...base, image: { kind: "upload", file } }, { editing: false }).get("image")).toBeInstanceOf(File);
    expect(toFormData({ ...base, image: { kind: "none" } }, { editing: true }).get("remove_image")).toBe("true");
    expect(toFormData({ ...base, image: { kind: "none" } }, { editing: false }).get("remove_image")).toBeNull();
    expect(toFormData({ ...base, image: { kind: "keep" } }, { editing: true }).get("remove_image")).toBeNull();
  });

  it("valida tipo y tamaño de la imagen", () => {
    expect(validateImageFile(new File(["x"], "a.svg", { type: "image/svg+xml" }))).toMatch(/Formato/);
    expect(validateImageFile(new File([new Uint8Array(6 * 1024 * 1024)], "a.png", { type: "image/png" }))).toMatch(/5 MB/);
    expect(validateImageFile(new File(["x"], "a.png", { type: "image/png" }))).toBeNull();
  });
});
