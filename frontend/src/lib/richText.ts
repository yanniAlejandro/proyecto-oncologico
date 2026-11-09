/**
 * Formato básico para textos editables («Quiénes somos»). Sin HTML: se parsea a bloques y React
 * los pinta como elementos, así que no hay riesgo de inyección.
 *   párrafos separados por línea en blanco · «- » listas · «### » subtítulos · «> » nota · «**negrita**»
 */

export type Inline = { text: string; bold: boolean };
export type Block =
  | { type: "p"; inlines: Inline[] }
  | { type: "h"; inlines: Inline[] }
  | { type: "note"; inlines: Inline[] }
  | { type: "ul"; items: Inline[][] };

export function parseInline(text: string): Inline[] {
  const out: Inline[] = [];
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  for (const part of parts) {
    if (!part) continue;
    const bold = part.startsWith("**") && part.endsWith("**") && part.length > 4;
    out.push({ text: bold ? part.slice(2, -2) : part, bold });
  }
  return out;
}

export function parseRichText(source: string): Block[] {
  const blocks: Block[] = [];
  let paragraph: string[] = [];
  let list: Inline[][] | null = null;

  const flushParagraph = () => {
    if (paragraph.length) blocks.push({ type: "p", inlines: parseInline(paragraph.join(" ")) });
    paragraph = [];
  };
  const flushList = () => {
    if (list?.length) blocks.push({ type: "ul", items: list });
    list = null;
  };

  for (const raw of source.replace(/\r\n?/g, "\n").split("\n")) {
    const line = raw.trim();
    if (!line) {
      flushParagraph();
      flushList();
    } else if (/^[-*•]\s+/.test(line)) {
      flushParagraph();
      list ??= [];
      list.push(parseInline(line.replace(/^[-*•]\s+/, "")));
    } else if (line.startsWith("### ") || line.startsWith("## ")) {
      flushParagraph();
      flushList();
      blocks.push({ type: "h", inlines: parseInline(line.replace(/^#+\s+/, "")) });
    } else if (line.startsWith("> ")) {
      flushParagraph();
      flushList();
      blocks.push({ type: "note", inlines: parseInline(line.slice(2)) });
    } else {
      flushList();
      paragraph.push(line);
    }
  }
  flushParagraph();
  flushList();
  return blocks;
}
