import { formatBytes, formatDate, previewText } from "./format";

it("previewText solo añade «...» si recorta (BUG-007)", () => {
  expect(previewText("corto")).toBe("corto");
  expect(previewText("a".repeat(200), 180)).toBe(`${"a".repeat(180)}...`);
  expect(previewText("palabra ".repeat(40), 20)).toBe("palabra palabra pala...");
});

it("formatBytes", () => {
  expect(formatBytes(null)).toBe("—");
  expect(formatBytes(512)).toBe("512 B");
  expect(formatBytes(1536)).toBe("1,5 KB");
  expect(formatBytes(25 * 1024 * 1024)).toBe("25 MB");
});

it("formatDate usa formato es-ES en hora de La Habana", () => {
  expect(formatDate("2026-11-04T15:00:00Z")).toBe("4/11/2026");
  expect(formatDate("2026-11-05T02:00:00Z")).toBe("4/11/2026"); // aún día 4 en Cuba
});
