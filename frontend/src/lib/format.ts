const dateFormatter = new Intl.DateTimeFormat("es-ES", { timeZone: "America/Havana" });

/** Fecha corta como la mostraba el portal (`toLocaleDateString('es-ES')`). */
export function formatDate(iso: string): string {
  return dateFormatter.format(new Date(iso));
}

/** Recorta el texto y añade «...» solo si de verdad se recortó (BUG-007). */
export function previewText(text: string, max = 180): string {
  return text.length > max ? `${text.slice(0, max).trimEnd()}...` : text;
}

export function formatBytes(bytes: number | null | undefined): string {
  if (bytes == null) return "—";
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB"];
  let value = bytes / 1024;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toLocaleString("es-ES", { maximumFractionDigits: 1 })} ${units[unit]}`;
}
