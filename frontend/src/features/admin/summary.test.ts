import { latestActivity, pendingDrafts } from "./summary";

const item = (title: string, at: string) => ({ kind: "x", title, who: null, at, href: "/admin" });

it("ordena la actividad de varias fuentes, la más reciente primero", () => {
  const result = latestActivity(
    [[item("a", "2026-11-01T10:00:00Z"), item("c", "2026-11-09T10:00:00Z")], [item("b", "2026-11-05T10:00:00Z"), item("roto", "x")]],
    2,
  );
  expect(result.map((i) => i.title)).toEqual(["c", "b"]);
});

it("cuenta los apartados aún en borrador", () => {
  expect(pendingDrafts(["> Borrador pendiente de validar por…", "Texto validado", "  > borrador pendiente de validar"])).toBe(2);
});
