import type { ReactNode } from "react";
import { type Inline, parseRichText } from "@/lib/richText";

function inlines(parts: Inline[]): ReactNode[] {
  return parts.map((part, i) => (part.bold ? <strong key={i}>{part.text}</strong> : part.text));
}

/** Pinta el formato básico (ver lib/richText.ts). Sirve en SSR (.astro) y en islas. */
export function RichText({ text, className }: { text: string; className?: string }) {
  return (
    <div className={className ?? "rich-text"}>
      {parseRichText(text).map((block, i) => {
        switch (block.type) {
          case "h":
            return <h3 key={i}>{inlines(block.inlines)}</h3>;
          case "note":
            return (
              <p key={i} className="rich-note">
                {inlines(block.inlines)}
              </p>
            );
          case "ul":
            return (
              <ul key={i}>
                {block.items.map((item, j) => (
                  <li key={j}>{inlines(item)}</li>
                ))}
              </ul>
            );
          default:
            return <p key={i}>{inlines(block.inlines)}</p>;
        }
      })}
    </div>
  );
}
