import { parseInline, parseRichText } from "./richText";

describe("texto con formato básico", () => {
  it("negritas en línea", () => {
    expect(parseInline("Atención **centrada** en la familia")).toEqual([
      { text: "Atención ", bold: false },
      { text: "centrada", bold: true },
      { text: " en la familia", bold: false },
    ]);
  });

  it("párrafos, subtítulos, listas y notas", () => {
    const blocks = parseRichText(
      "> Borrador\n\nPrimera línea\nsigue el párrafo.\n\n### Misión\n- uno\n- **dos**\nTexto tras lista",
    );
    expect(blocks.map((b) => b.type)).toEqual(["note", "p", "h", "ul", "p"]);
    expect(blocks[1]).toEqual({ type: "p", inlines: [{ text: "Primera línea sigue el párrafo.", bold: false }] });
    expect(blocks[3]).toEqual({
      type: "ul",
      items: [[{ text: "uno", bold: false }], [{ text: "dos", bold: true }]],
    });
  });

  it("el HTML se trata como texto, nunca como marcado", () => {
    expect(parseRichText("<img src=x onerror=alert(1)>")).toEqual([
      { type: "p", inlines: [{ text: "<img src=x onerror=alert(1)>", bold: false }] },
    ]);
  });
});
