import { ApiError, buildUrl, createFetchTransport, errorFromResponse, getErrorMessage } from "./transport";

describe("buildUrl", () => {
  it("omite parámetros vacíos y codifica el resto", () => {
    expect(buildUrl("/api/v1/", "/news", { search: "mamá", empty: "", none: undefined })).toBe(
      "/api/v1/news?search=mam%C3%A1",
    );
    expect(buildUrl("http://x/api", "/news")).toBe("http://x/api/news");
  });
});

describe("errorFromResponse", () => {
  it("usa el detail de FastAPI (texto o lista de validación)", async () => {
    expect((await errorFromResponse(Response.json({ detail: "Permisos insuficientes" }, { status: 403 }))).message).toBe(
      "Permisos insuficientes",
    );
    const list = Response.json({ detail: [{ msg: "campo requerido" }, { msg: "muy corto" }] }, { status: 422 });
    expect((await errorFromResponse(list)).message).toBe("campo requerido, muy corto");
    const html = new Response("<html>", { status: 502 });
    const err = await errorFromResponse(html);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(502);
    expect(getErrorMessage(err)).toBe("Ha ocurrido un error inesperado");
  });
});

describe("createFetchTransport", () => {
  const calls: { url: string; init: RequestInit }[] = [];
  const fakeFetch = (response: Response) =>
    (async (url: string, init: RequestInit) => {
      calls.push({ url, init });
      return response;
    }) as unknown as typeof fetch;

  beforeEach(() => calls.splice(0));

  it("envía JSON con cabeceras inyectadas y parsea la respuesta", async () => {
    const t = createFetchTransport("/api", () => ({ Authorization: "Bearer x" }), fakeFetch(Response.json({ ok: 1 })));
    await expect(t.request("POST", "/news", { json: { a: 1 } })).resolves.toEqual({ ok: 1 });
    const headers = new Headers(calls[0]!.init.headers);
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(headers.get("Authorization")).toBe("Bearer x");
    expect(calls[0]!.init.body).toBe('{"a":1}');
  });

  it("no fija Content-Type en multipart (lo pone el navegador con el boundary)", async () => {
    const t = createFetchTransport("/api", undefined, fakeFetch(Response.json({})));
    const body = new FormData();
    await t.request("POST", "/documents", { body });
    expect(new Headers(calls[0]!.init.headers).has("Content-Type")).toBe(false);
    expect(calls[0]!.init.body).toBe(body);
  });

  it("204 → undefined; error → ApiError con el mensaje del backend", async () => {
    await expect(
      createFetchTransport("/api", undefined, fakeFetch(new Response(null, { status: 204 }))).request("DELETE", "/x"),
    ).resolves.toBeUndefined();
    const failing = createFetchTransport(
      "/api",
      undefined,
      fakeFetch(Response.json({ detail: "Documento no encontrado" }, { status: 404 })),
    );
    await expect(failing.request("GET", "/x")).rejects.toMatchObject({ status: 404, message: "Documento no encontrado" });
  });
});
